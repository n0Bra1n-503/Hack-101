"""SkyGuard AI - Statistical Anomaly Detection Package."""

from .config import StatisticalConfig
from .detector import StatisticalBaselineDetector, detect_statistical_anomalies
from .baselines import fit_statistical_baselines, BaselineReference
from .summary import generate_statistical_summary

__all__ = [
    "StatisticalConfig",
    "StatisticalBaselineDetector",
    "detect_statistical_anomalies",
    "fit_statistical_baselines",
    "BaselineReference",
    "generate_statistical_summary",
]
