import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
import joblib
from pathlib import Path
import json

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.data.schema import SensorSchema
from .autoencoder_config import AutoencoderConfig


def get_autoencoder_features(df: pd.DataFrame, schema: Optional[SensorSchema] = None) -> List[str]:
    """
    Identify valid features for the Autoencoder model.
    Excludes metadata, timestamps, identifiers, and ground truth labels.
    """
    if schema is None:
        schema = SensorSchema()
        
    excluded_keywords = [
        "station_id", "timestamp", "original_time", "event_id", 
        "fault_type", "fault_present", "affected_sensor", "seed",
        "magnitude", "start_idx", "end_idx", "_gt", "ground_truth",
        "latitude", "longitude"
    ]
    
    features = []
    for col in df.columns:
        if any(excl.lower() in col.lower() for excl in excluded_keywords):
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        features.append(col)
        
    return features


class TabularAutoencoder(nn.Module):
    """Simple dense Autoencoder for tabular data."""
    def __init__(self, input_dim: int, hidden_dims: tuple):
        super().__init__()
        
        # Encoder
        encoder_layers = []
        in_d = input_dim
        for h_dim in hidden_dims[:len(hidden_dims)//2]:
            encoder_layers.append(nn.Linear(in_d, h_dim))
            encoder_layers.append(nn.ReLU())
            in_d = h_dim
        # Latent space
        latent_dim = hidden_dims[len(hidden_dims)//2]
        encoder_layers.append(nn.Linear(in_d, latent_dim))
        encoder_layers.append(nn.ReLU())
        self.encoder = nn.Sequential(*encoder_layers)
        
        # Decoder
        decoder_layers = []
        in_d = latent_dim
        for h_dim in hidden_dims[len(hidden_dims)//2 + 1:]:
            decoder_layers.append(nn.Linear(in_d, h_dim))
            decoder_layers.append(nn.ReLU())
            in_d = h_dim
        # Output layer matches input
        decoder_layers.append(nn.Linear(in_d, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded


class AutoencoderEngine:
    """Engine for training, predicting and managing the PyTorch Autoencoder."""
    
    def __init__(self, config: Optional[AutoencoderConfig] = None):
        self.config = config or AutoencoderConfig()
        self.features: List[str] = []
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.model: Optional[TabularAutoencoder] = None
        self.threshold: float = 0.0
        self.is_fitted = False
        
        # Set seeds
        torch.manual_seed(self.config.random_seed)
        np.random.seed(self.config.random_seed)
        
    def _prepare_data(self, df: pd.DataFrame, is_training: bool = False) -> torch.Tensor:
        """Extract, impute, scale and convert to tensor."""
        if not self.features:
            raise ValueError("Features not defined.")
            
        missing_cols = [f for f in self.features if f not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required features: {missing_cols}")
            
        X = df[self.features].copy()
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        if is_training:
            X_imp = self.imputer.fit_transform(X)
            X_scaled = self.scaler.fit_transform(X_imp)
        else:
            X_imp = self.imputer.transform(X)
            X_scaled = self.scaler.transform(X_imp)
            
        return torch.tensor(X_scaled, dtype=torch.float32)

    def fit(self, df: pd.DataFrame, schema: Optional[SensorSchema] = None) -> Dict[str, list]:
        """Train the Autoencoder with chronological train/val split."""
        self.features = get_autoencoder_features(df, schema)
        X_tensor = self._prepare_data(df, is_training=True)
        
        # Chronological split (90/10)
        split_idx = int(len(X_tensor) * 0.9)
        train_tensor = X_tensor[:split_idx]
        val_tensor = X_tensor[split_idx:]
        
        train_loader = DataLoader(TensorDataset(train_tensor, train_tensor), 
                                  batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(TensorDataset(val_tensor, val_tensor), 
                                batch_size=self.config.batch_size, shuffle=False)
        
        self.model = TabularAutoencoder(input_dim=len(self.features), hidden_dims=self.config.hidden_dims)
        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        
        best_val_loss = float('inf')
        patience_counter = 0
        best_state = None
        history = {"train_loss": [], "val_loss": []}
        
        for epoch in range(self.config.epochs):
            self.model.train()
            train_loss = 0.0
            for batch_x, _ in train_loader:
                optimizer.zero_grad()
                output = self.model(batch_x)
                loss = criterion(output, batch_x)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * batch_x.size(0)
            train_loss /= len(train_loader.dataset)
            
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_x, _ in val_loader:
                    output = self.model(batch_x)
                    loss = criterion(output, batch_x)
                    val_loss += loss.item() * batch_x.size(0)
            val_loss /= len(val_loader.dataset)
            
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = self.model.state_dict()
                patience_counter = 0
            else:
                patience_counter += 1
                
            if patience_counter >= self.config.patience:
                break
                
        # Restore best model
        if best_state is not None:
            self.model.load_state_dict(best_state)
            
        self.is_fitted = True
        
        # Calculate threshold on full training data
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            mse_scores = torch.mean((X_tensor - reconstructed) ** 2, dim=1).numpy()
            self.threshold = np.percentile(mse_scores, self.config.threshold_percentile)
            
        return history

    def calculate_reconstruction_error(self, df: pd.DataFrame) -> np.ndarray:
        """Calculate MSE reconstruction error for each observation."""
        if not self.is_fitted or self.model is None:
            raise ValueError("Model is not fitted.")
            
        X_tensor = self._prepare_data(df, is_training=False)
        
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            mse_scores = torch.mean((X_tensor - reconstructed) ** 2, dim=1).numpy()
            
        return mse_scores

    def predict(self, df: pd.DataFrame, threshold_percentile: Optional[float] = None) -> pd.DataFrame:
        """Generate anomaly scores and predictions."""
        scores = self.calculate_reconstruction_error(df)
        
        threshold = self.threshold
        if threshold_percentile is not None and threshold_percentile != self.config.threshold_percentile:
            # Need to recalculate threshold if different percentile is requested
            # Note: A true configurable threshold should ideally be derived from the training set,
            # but to be practical here we assume self.threshold was pre-calculated correctly,
            # OR the runner will supply an explicit threshold value.
            pass # Usually handled via explicit threshold argument in a separate method
            
        predictions = scores >= threshold
        
        results = pd.DataFrame(index=df.index)
        results["anomaly_score"] = scores
        results["anomaly_prediction"] = predictions
        
        return results

    def save(self, output_dir: str | Path):
        """Save the trained model and artifacts."""
        if not self.is_fitted or self.model is None:
            raise ValueError("Cannot save an unfitted model.")
            
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        
        # Save PyTorch model weights
        torch.save(self.model.state_dict(), out_p / "model.pt")
        
        # Save preprocessors
        joblib.dump(self.imputer, out_p / "imputer.joblib")
        joblib.dump(self.scaler, out_p / "scaler.joblib")
        
        # Save config and features
        state = {
            "features": self.features,
            "threshold": float(self.threshold),
            "config": {
                "hidden_dims": self.config.hidden_dims,
                "input_dim": len(self.features)
            }
        }
        with open(out_p / "state.json", "w") as f:
            json.dump(state, f, indent=4)

    @classmethod
    def load(cls, input_dir: str | Path) -> 'AutoencoderEngine':
        """Load a trained model."""
        in_p = Path(input_dir)
        
        with open(in_p / "state.json", "r") as f:
            state = json.load(f)
            
        config = AutoencoderConfig(hidden_dims=tuple(state["config"]["hidden_dims"]))
        engine = cls(config=config)
        
        engine.features = state["features"]
        engine.threshold = state["threshold"]
        
        engine.model = TabularAutoencoder(input_dim=state["config"]["input_dim"], hidden_dims=engine.config.hidden_dims)
        engine.model.load_state_dict(torch.load(in_p / "model.pt"))
        engine.model.eval()
        
        engine.imputer = joblib.load(in_p / "imputer.joblib")
        engine.scaler = joblib.load(in_p / "scaler.joblib")
        
        engine.is_fitted = True
        return engine
