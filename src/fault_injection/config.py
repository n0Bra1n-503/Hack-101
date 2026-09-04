from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List

class FaultType(Enum):
    NORMAL = "NORMAL"
    SPIKE = "SPIKE"
    DRIFT = "DRIFT"
    FROZEN = "FROZEN"
    DROPOUT = "DROPOUT"
    ABRUPT_JUMP = "ABRUPT_JUMP"
    MULTIVARIATE_INCONSISTENCY = "MULTIVARIATE_INCONSISTENCY"
    UNKNOWN = "UNKNOWN"

@dataclass
class FaultConfig:
    """Configuration for fault injection engine."""
    random_seed: int = 42
    
    # Fault probabilities/frequencies
    fault_rate: float = 0.05 # 5% of observations affected by faults
    
    # General constraints
    allow_overlapping_faults: bool = False
    
    # Parameters for specific faults
    spike_params: Dict[str, Any] = field(default_factory=lambda: {
        "magnitude_std_min": 3.0,
        "magnitude_std_max": 8.0,
        "duration_min": 1,
        "duration_max": 3
    })
    
    drift_params: Dict[str, Any] = field(default_factory=lambda: {
        "magnitude_std_min": 2.0,
        "magnitude_std_max": 5.0,
        "duration_min": 12, # e.g. 1 hour (if 5 min freq)
        "duration_max": 48  # e.g. 4 hours
    })
    
    frozen_params: Dict[str, Any] = field(default_factory=lambda: {
        "duration_min": 6,
        "duration_max": 24
    })
    
    dropout_params: Dict[str, Any] = field(default_factory=lambda: {
        "duration_min": 2,
        "duration_max": 12
    })
    
    abrupt_jump_params: Dict[str, Any] = field(default_factory=lambda: {
        "magnitude_std_min": 3.0,
        "magnitude_std_max": 6.0,
        "duration_min": 12,
        "duration_max": 36
    })
    
    multivariate_params: Dict[str, Any] = field(default_factory=lambda: {
        "magnitude_std_min": 4.0,
        "magnitude_std_max": 7.0,
        "duration_min": 6,
        "duration_max": 24
    })
