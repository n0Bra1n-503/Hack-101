from dataclasses import dataclass
from typing import Union

@dataclass
class IsolationForestConfig:
    """Configuration for Isolation Forest Model."""
    n_estimators: int = 100
    max_samples: Union[str, int, float] = "auto"
    contamination: Union[float, str] = "auto"
    max_features: float = 1.0
    random_state: int = 42
    n_jobs: int = -1
    
    # Thresholding configuration
    # If contamination is "auto", we need a threshold strategy.
    # e.g., 99th percentile of anomaly scores on the training data
    threshold_percentile: float = 95.0
