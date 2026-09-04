from dataclasses import dataclass

@dataclass
class DecisionConfig:
    """Configuration for Weather-vs-Sensor Decision Engine and Trust Score."""
    
    # Classification Thresholds
    sensor_fault_threshold: float = 0.50
    weather_threshold: float = 0.50
    conflict_threshold: float = 0.40
    
    # Autoencoder explicit override weight
    # If AE is above this, we heavily boost the sensor_fault_score
    ae_override_threshold: float = 0.70
    
    # Trust Score parameters
    base_trust: float = 100.0
    max_fault_penalty: float = 70.0
    max_conflict_penalty: float = 20.0
    max_weather_bonus: float = 20.0
