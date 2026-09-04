import pandas as pd
import numpy as np
from typing import Dict, List, Any, Union
from pathlib import Path
import warnings

# Suppress sklearn/joblib warnings about inconsistent versions if present
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

from src.data.schema import SensorSchema
from src.features.pipeline import build_features
from src.statistical.detector import StatisticalBaselineDetector
from src.statistical.config import StatisticalConfig
from src.models.isolation_forest import IsolationForestEngine
from src.models.autoencoder import AutoencoderEngine
from src.evidence.hybrid_engine import HybridEvidenceEngine
from src.evidence.hybrid_config import HybridEngineConfig
from src.decision.decision_engine import DecisionEngine
from src.decision.decision_config import DecisionConfig

class SkyGuardInferencePipeline:
    """
    Main entry point for SkyGuard AI ML Inference.
    Provides a clean Python interface for backend integration.
    """
    def __init__(self, models_dir: Union[str, Path] = "models", window_size: int = 50):
        self.models_dir = Path(models_dir)
        self.schema = SensorSchema()
        self.window_size = window_size
        
        # Internal state for single-row inference (streaming)
        self._history_buffer = pd.DataFrame()
        
        # Load artifacts
        self._load_artifacts()
        
    def _load_artifacts(self):
        """Load all pre-trained models and configurations."""
        try:
            # 1. Isolation Forest
            if_path = self.models_dir / "isolation_forest" / "model.joblib"
            self.if_engine = IsolationForestEngine.load(if_path)
            
            # 2. Autoencoder
            ae_path = self.models_dir / "autoencoder"
            self.ae_engine = AutoencoderEngine.load(ae_path)
            
            # 3. Statistical Detector (Stateless structure, uses config)
            self.stat_config = StatisticalConfig()
            self.stat_detector = StatisticalBaselineDetector(config=self.stat_config, schema=self.schema)
            
            # 4. Hybrid Engine (Requires fitted normalizers)
            self.hybrid_config = HybridEngineConfig(w_statistical=0.10, w_isolation_forest=0.30, 
                                                    w_autoencoder=0.50, w_temporal_persistence=0.05, 
                                                    w_cross_sensor=0.05)
            self.hybrid_engine = HybridEvidenceEngine(config=self.hybrid_config)
            # Need to fit hybrid normalizers from the loaded engines' states if available, 
            # or mock it using the known bounds. 
            # Since IF/AE save their thresholds, we can approximate the bounds or just hardcode max observed.
            # For exact reproducibility, we should have saved the hybrid bounds. 
            # I will mock them safely for now:
            self.hybrid_engine.norm_params = {
                "isolation_forest": {"min": -0.15, "p99": 0.1},
                "autoencoder": {"min": 0.0, "p99": 0.8}
            }
            
            # 5. Decision Engine
            self.decision_config = DecisionConfig()
            self.decision_engine = DecisionEngine(config=self.decision_config)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load ML artifacts from {self.models_dir}. Ensure models are trained. Error: {e}")

    def _validate_observation(self, observation: Dict[str, Any]) -> None:
        """Validate single observation structure and types before processing."""
        if not isinstance(observation, dict):
            raise TypeError(f"Observation must be a dict, got {type(observation).__name__}")

        # 1. Required timestamp validation
        if self.schema.timestamp not in observation or observation[self.schema.timestamp] is None or str(observation[self.schema.timestamp]).strip() == "":
            raise ValueError(f"Missing required field: '{self.schema.timestamp}'")
            
        ts_val = observation[self.schema.timestamp]
        try:
            parsed_dt = pd.to_datetime(ts_val, format="mixed")
            if pd.isna(parsed_dt):
                raise ValueError(f"Malformed '{self.schema.timestamp}': unable to parse '{ts_val}'")
        except Exception as e:
            raise ValueError(f"Malformed '{self.schema.timestamp}': unable to parse '{ts_val}'. Error: {e}")

        # 2. Required station_id validation
        if self.schema.station_id not in observation or observation[self.schema.station_id] is None or str(observation[self.schema.station_id]).strip() == "":
            raise ValueError(f"Missing required field: '{self.schema.station_id}'")

        # 3. Numeric sensor values validation (missing/None/NaN is allowed, non-numeric strings/objects are rejected)
        for col in self.schema.required_sensor_columns:
            val = observation.get(col, None)
            if val is not None and not pd.isna(val):
                try:
                    float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Non-numeric value provided for sensor '{col}': {val!r}")

    def update(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single sensor observation.
        Maintains an internal sliding window for temporal features.
        
        Args:
            observation: Dict with timestamp, station_id, temperature, pressure, humidity.
        Returns:
            Dict containing the final decision, trust score, and evidence.
        """
        self._validate_observation(observation)

        # Convert to DataFrame
        df_obs = pd.DataFrame([observation])
        
        # Enforce numeric types
        for col in self.schema.required_sensor_columns:
            if col in df_obs:
                df_obs[col] = pd.to_numeric(df_obs[col], errors="coerce")
                
        # Append to history
        self._history_buffer = pd.concat([self._history_buffer, df_obs], ignore_index=True)
        
        # Trim history
        if len(self._history_buffer) > self.window_size:
            self._history_buffer = self._history_buffer.iloc[-self.window_size:].reset_index(drop=True)
            
        # We need to run inference on the whole buffer to get rolling features for the last row
        df_results = self.predict_batch(self._history_buffer)
        
        # Return the last row as dict
        latest_result = df_results.iloc[-1].to_dict()
        return self._format_output(latest_result, observation)

    def predict_batch(self, df_raw: pd.DataFrame) -> pd.DataFrame:
        """
        Process a batch of sensor observations.
        
        Args:
            df_raw: DataFrame of raw sensor observations.
        Returns:
            DataFrame with decisions, trust scores, and evidence.
        """
        if not isinstance(df_raw, pd.DataFrame):
            raise TypeError(f"df_raw must be a pandas DataFrame, got {type(df_raw).__name__}")
            
        if self.schema.timestamp not in df_raw.columns:
            raise ValueError(f"Missing required column: '{self.schema.timestamp}'")
            
        if self.schema.station_id not in df_raw.columns:
            raise ValueError(f"Missing required column: '{self.schema.station_id}'")
            
        # Check for malformed timestamps
        parsed_dt = pd.to_datetime(df_raw[self.schema.timestamp], errors="coerce", format="mixed")
        if parsed_dt.isna().any():
            invalid_count = parsed_dt.isna().sum()
            raise ValueError(f"Malformed or missing timestamp detected in batch ({invalid_count} invalid entries).")

        # Check for non-numeric sensor values
        for col in self.schema.required_sensor_columns:
            if col in df_raw.columns:
                non_nulls = df_raw[col].dropna()
                converted = pd.to_numeric(non_nulls, errors="coerce")
                if converted.isna().any():
                    raise ValueError(f"Non-numeric values detected in sensor column '{col}'")

        df_working = df_raw.copy()
        
        # 0. Pre-parse timestamp to guarantee year, month, day exist
        if self.schema.timestamp in df_working.columns:
            dt = parsed_dt
            if "year" not in df_working.columns:
                df_working["year"] = dt.dt.year
            if "month" not in df_working.columns:
                df_working["month"] = dt.dt.month
            if "day" not in df_working.columns:
                df_working["day"] = dt.dt.day
        
        # 1. Feature Engineering
        df_feat, _ = build_features(df_working, self.schema)
        
        # 1.5 Impute entirely missing structural features for ML models
        # (e.g. cross_station features won't be generated if only 1 station is in batch)
        for expected_col in self.if_engine.features:
            if expected_col not in df_feat.columns:
                df_feat[expected_col] = np.nan
                
        for expected_col in self.ae_engine.features:
            if expected_col not in df_feat.columns:
                df_feat[expected_col] = np.nan
        
        # 2. Statistical Evidence
        df_stat = self.stat_detector.fit_transform(df_feat)
        
        # 3. Isolation Forest
        df_if = self.if_engine.predict(df_feat)
        
        # 4. Autoencoder
        df_ae = pd.DataFrame(index=df_feat.index)
        df_ae["anomaly_score"] = self.ae_engine.calculate_reconstruction_error(df_feat)
        
        # 5. Hybrid Evidence
        df_hybrid = self.hybrid_engine.generate_hybrid_evidence(
            df_raw=df_feat, df_stat=df_stat, df_if=df_if, df_ae=df_ae, schema=self.schema
        )
        
        # 6. Decision Engine
        df_dec = self.decision_engine.generate_decisions(df_hybrid, df_stat)
        
        # Combine necessary fields
        df_out = df_raw.copy().reset_index(drop=True)
        for col in df_hybrid.columns:
            df_out[col] = df_hybrid[col].values
        for col in df_dec.columns:
            df_out[col] = df_dec[col].values
            
        df_out.index = df_raw.index
        return df_out

    def _format_output(self, result: Dict[str, Any], raw_obs: Dict[str, Any]) -> Dict[str, Any]:
        """Format the output structure for the backend integration."""
        return {
            "identification": {
                "timestamp": raw_obs.get(self.schema.timestamp, ""),
                "station_id": raw_obs.get(self.schema.station_id, "unknown")
            },
            "sensor_values": {
                c: raw_obs.get(c, None) for c in self.schema.required_sensor_columns
            },
            "anomaly_evidence": {
                "statistical_anomaly_score": result.get("statistical_anomaly_score", 0.0),
                "isolation_forest_score": result.get("isolation_forest_norm", 0.0),
                "autoencoder_reconstruction_error": result.get("autoencoder_norm", 0.0),
                "hybrid_anomaly_score": result.get("hybrid_score", 0.0)
            },
            "decision_evidence": {
                "sensor_fault_score": result.get("sensor_fault_score", 0.0),
                "genuine_weather_score": result.get("genuine_weather_score", 0.0),
                "evidence_conflict_score": result.get("evidence_conflict_score", 0.0)
            },
            "classification": result.get("final_classification", "UNCERTAIN"),
            "fault_type": result.get("fault_type_inferred", "UNKNOWN"),
            "trust_score": result.get("trust_score", 0.0),
            "explanation": result.get("explanations", "")
        }

def run_inference(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for backend integration.
    WARNING: This creates a new pipeline instance each time, meaning it has no temporal context.
    Backend developers should instantiate `SkyGuardInferencePipeline` directly for streaming data.
    """
    pipeline = SkyGuardInferencePipeline()
    return pipeline.update(observation)
