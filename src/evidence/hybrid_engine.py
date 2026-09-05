import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import json

from .hybrid_config import HybridEngineConfig
from src.data.schema import SensorSchema

class HybridEvidenceEngine:
    def __init__(self, config: Optional[HybridEngineConfig] = None):
        self.config = config or HybridEngineConfig()
        self.norm_params = {}
        
    def _normalize_array(self, arr: np.ndarray, key: str, is_training: bool) -> np.ndarray:
        """MinMax scale strictly to [0,1] using p99 to bound outliers."""
        if is_training:
            min_v = np.nanmin(arr)
            p99 = np.nanpercentile(arr, self.config.norm_percentile)
            # Avoid division by zero
            if p99 == min_v:
                p99 = min_v + 1e-6
            self.norm_params[key] = {"min": min_v, "p99": p99}
        else:
            min_v = self.norm_params[key]["min"]
            p99 = self.norm_params[key]["p99"]
            
        scaled = (arr - min_v) / (p99 - min_v)
        return np.clip(scaled, 0.0, 1.0)
        
    def fit_normalizers(self, df_if_train: pd.DataFrame, df_ae_train: pd.DataFrame):
        """Fit normalization limits on clean training data scores."""
        if "anomaly_score" in df_if_train:
            self._normalize_array(df_if_train["anomaly_score"].values, "isolation_forest", True)
        if "anomaly_score" in df_ae_train:
            self._normalize_array(df_ae_train["anomaly_score"].values, "autoencoder", True)
            
    def generate_hybrid_evidence(
        self,
        df_raw: pd.DataFrame,
        df_stat: pd.DataFrame,
        df_if: pd.DataFrame,
        df_ae: pd.DataFrame,
        schema: Optional[SensorSchema] = None
    ) -> pd.DataFrame:
        """
        Combine statistical, isolation forest, and autoencoder evidence into a unified record.
        Must be called after `fit_normalizers` when evaluating.
        """
        if schema is None:
            schema = SensorSchema()
            
        df_out = pd.DataFrame(index=df_raw.index)
        
        # 1. Statistical Evidence
        if "statistical_anomaly_score" in df_stat:
            stat_score = df_stat["statistical_anomaly_score"].fillna(0.0)
        else:
            stat_score = pd.Series(0.0, index=df_raw.index)
            
        # 2. Isolation Forest Evidence
        if "anomaly_score" in df_if and "isolation_forest" in self.norm_params:
            if_raw = df_if["anomaly_score"].fillna(df_if["anomaly_score"].median())
            if_score = self._normalize_array(if_raw.values, "isolation_forest", False)
        else:
            if_score = np.zeros(len(df_raw))
            
        # 3. Autoencoder Evidence
        if "anomaly_score" in df_ae and "autoencoder" in self.norm_params:
            ae_raw = df_ae["anomaly_score"].fillna(df_ae["anomaly_score"].median())
            ae_score = self._normalize_array(ae_raw.values, "autoencoder", False)
        else:
            ae_score = np.zeros(len(df_raw))
            
        # 4. Temporal & Cross-sensor extracted directly from Statistical Engine's flags
        # The statistical engine already computes rolling deviations and cross-station devs
        # Let's map those flags to a 0-1 score
        if "rolling_deviation_high" in df_stat:
            temporal_score = df_stat["rolling_deviation_high"].astype(float)
        else:
            temporal_score = pd.Series(0.0, index=df_raw.index)
            
        if "is_concurrent_multisensor_anomaly" in df_stat:
            cross_sensor_score = df_stat["is_concurrent_multisensor_anomaly"].astype(float)
        else:
            cross_sensor_score = pd.Series(0.0, index=df_raw.index)
            
        # Calculate Hybrid Score
        w_tot = (self.config.w_statistical + self.config.w_isolation_forest + 
                 self.config.w_autoencoder + self.config.w_temporal_persistence + 
                 self.config.w_cross_sensor)
                 
        hybrid = (
            (stat_score * self.config.w_statistical) +
            (if_score * self.config.w_isolation_forest) +
            (ae_score * self.config.w_autoencoder) +
            (temporal_score * self.config.w_temporal_persistence) +
            (cross_sensor_score * self.config.w_cross_sensor)
        ) / w_tot
        
        df_out["statistical_anomaly_score"] = stat_score
        df_out["isolation_forest_raw"] = df_if["anomaly_score"] if "anomaly_score" in df_if else 0.0
        df_out["isolation_forest_norm"] = if_score
        df_out["autoencoder_raw"] = df_ae["anomaly_score"] if "anomaly_score" in df_ae else 0.0
        df_out["autoencoder_norm"] = ae_score
        df_out["temporal_score"] = temporal_score
        df_out["cross_sensor_score"] = cross_sensor_score
        
        df_out["hybrid_score"] = hybrid
        
        # Evidence Strength
        strength = pd.Series("LOW", index=df_out.index)
        strength[hybrid >= self.config.threshold_medium] = "MEDIUM"
        strength[hybrid >= self.config.threshold_high] = "HIGH"
        df_out["evidence_strength"] = strength
        
        # Evidence Reasons
        reasons_list = []
        for i in range(len(df_out)):
            r = []
            if stat_score.iloc[i] >= 0.5:
                r.append("Strong statistical anomaly detected.")
            if if_score[i] >= 0.6:
                r.append("Isolation Forest identifies significant spatial anomaly.")
            if ae_score[i] >= 0.6:
                r.append("Autoencoder reconstruction error is unusually high.")
            if temporal_score.iloc[i] > 0:
                r.append("Abrupt temporal deviation from rolling baseline.")
            if cross_sensor_score.iloc[i] > 0:
                r.append("Concurrent multi-sensor abnormality detected.")
            
            reasons_list.append(json.dumps(r))
            
        df_out["evidence_reasons"] = reasons_list
        
        return df_out
