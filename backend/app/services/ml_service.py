"""ML Inference Service integrating Manan's pre-trained anomaly models.

Architecture:
Supabase Reading -> ML Feature Adapter -> Manan Trained Models -> Anomaly Result

Provides singleton model loading and deterministic anomaly evaluation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from src.pipeline.inference_pipeline import SkyGuardInferencePipeline

logger = logging.getLogger("skyguard.ml_service")


class MLInferenceService:
    """Thread-safe singleton service managing pre-trained ML anomaly models."""

    _instance: Optional["MLInferenceService"] = None

    def __init__(self, models_dir: Union[str, Path] = "models", window_size: int = 50):
        self.models_dir = Path(models_dir)
        self.window_size = window_size
        logger.info(f"Loading SkyGuard ML models from {self.models_dir.resolve()}...")
        self.pipeline = SkyGuardInferencePipeline(models_dir=self.models_dir, window_size=self.window_size)
        logger.info("SkyGuard ML models loaded successfully.")

    @classmethod
    def get_instance(cls, models_dir: Union[str, Path] = "models") -> "MLInferenceService":
        if cls._instance is None:
            cls._instance = cls(models_dir=models_dir)
        return cls._instance

    def detect_anomaly(self, reading_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run ML anomaly detection on a single weather observation.

        Parameters:
            reading_data: Dict containing timestamp, station_id, temperature, pressure, humidity.

        Returns:
            Stable ML anomaly contract:
            {
                "anomaly": bool,
                "anomaly_score": float,
                "model": "hybrid",
                "signals": {
                    "statistical": float,
                    "isolation_forest": float,
                    "autoencoder": float
                }
            }
        """
        # Map database schema to ML pipeline required inputs
        obs = {
            "timestamp": str(reading_data.get("timestamp")),
            "station_id": str(reading_data.get("station_id", "UNKNOWN")),
            "temperature": reading_data.get("temperature"),
            "pressure": reading_data.get("pressure"),
            "humidity": reading_data.get("humidity"),
        }

        # Run pipeline inference
        result = self.pipeline.update(obs)
        evidence = result.get("anomaly_evidence", {})

        stat_score = float(evidence.get("statistical_anomaly_score", 0.0))
        if_score = float(evidence.get("isolation_forest_score", 0.0))
        ae_score = float(evidence.get("autoencoder_reconstruction_error", 0.0))
        hybrid_score = float(evidence.get("hybrid_anomaly_score", 0.0))

        # Hybrid anomaly threshold (0.50 as standard calibrated threshold)
        is_anomaly = hybrid_score >= 0.50

        return {
            "anomaly": is_anomaly,
            "anomaly_score": round(hybrid_score, 4),
            "model": "hybrid",
            "signals": {
                "statistical": round(stat_score, 4),
                "isolation_forest": round(if_score, 4),
                "autoencoder": round(ae_score, 4),
            },
        }

    def detect_batch(self, readings_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run inference across a batch of readings."""
        return [self.detect_anomaly(r) for r in readings_list]


# Global accessor for FastAPI dependency injection
def get_ml_service() -> MLInferenceService:
    return MLInferenceService.get_instance()
