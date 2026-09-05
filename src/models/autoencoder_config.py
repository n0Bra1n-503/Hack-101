from dataclasses import dataclass

@dataclass
class AutoencoderConfig:
    """Configuration for PyTorch Autoencoder Model."""
    hidden_dims: tuple = (32, 16, 32)
    learning_rate: float = 1e-3
    batch_size: int = 64
    epochs: int = 50
    patience: int = 5
    random_seed: int = 42
    
    # Thresholding configuration
    # By default, use 95th percentile, but this can be overridden during evaluation
    threshold_percentile: float = 95.0
