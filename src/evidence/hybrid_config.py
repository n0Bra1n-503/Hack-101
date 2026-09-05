from dataclasses import dataclass

@dataclass
class HybridEngineConfig:
    """Configuration for Hybrid Evidence Engine."""
    
    # Weights for the evidence score
    w_statistical: float = 0.25
    w_isolation_forest: float = 0.20
    w_autoencoder: float = 0.35
    w_temporal_persistence: float = 0.10
    w_cross_sensor: float = 0.10
    
    # Overall score normalization
    # If weights sum to 1.0, the max score is 1.0
    
    # Categorical Strength Thresholds
    threshold_high: float = 0.65
    threshold_medium: float = 0.40
    
    # Normalization percentiles for IF and AE to bound them to [0,1]
    # We map [min_val, p99] -> [0, 1] to limit outlier effects
    norm_percentile: float = 99.5
