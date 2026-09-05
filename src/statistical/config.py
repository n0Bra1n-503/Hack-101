from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Union
import yaml


@dataclass
class StatisticalConfig:
    """Configuration parameters for statistical anomaly detection."""
    zscore_threshold: float = 3.0
    robust_threshold: float = 3.5
    rolling_z_threshold: float = 3.0
    diurnal_z_threshold: float = 3.0
    cross_station_dev_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "temperature": 4.0,
            "pressure": 3.5,
            "humidity": 15.0,
        }
    )
    min_evidence_for_suspicious: int = 1
    suspicious_score_threshold: float = 0.40
    strongly_unusual_score_threshold: float = 0.70
    weights: Dict[str, float] = field(
        default_factory=lambda: {
            "zscore": 0.20,
            "robust": 0.20,
            "rolling": 0.25,
            "diurnal": 0.15,
            "cross_station": 0.20,
        }
    )

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> "StatisticalConfig":
        """Load configuration from a YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            return cls()

        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        scoring_data = data.get("scoring", {})

        return cls(
            zscore_threshold=float(data.get("zscore_threshold", 3.0)),
            robust_threshold=float(data.get("robust_threshold", 3.5)),
            rolling_z_threshold=float(data.get("rolling_z_threshold", 3.0)),
            diurnal_z_threshold=float(data.get("diurnal_z_threshold", 3.0)),
            cross_station_dev_thresholds=data.get(
                "cross_station_dev_thresholds",
                {"temperature": 4.0, "pressure": 3.5, "humidity": 15.0},
            ),
            min_evidence_for_suspicious=int(
                scoring_data.get("min_evidence_for_suspicious", 1)
            ),
            suspicious_score_threshold=float(
                scoring_data.get("suspicious_score_threshold", 0.40)
            ),
            strongly_unusual_score_threshold=float(
                scoring_data.get("strongly_unusual_score_threshold", 0.70)
            ),
            weights=scoring_data.get(
                "weights",
                {
                    "zscore": 0.20,
                    "robust": 0.20,
                    "rolling": 0.25,
                    "diurnal": 0.15,
                    "cross_station": 0.20,
                },
            ),
        )
