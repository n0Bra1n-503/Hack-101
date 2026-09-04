import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any, Optional, Union
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
import joblib
from pathlib import Path

from src.data.schema import SensorSchema
from .config import IsolationForestConfig

def get_isolation_forest_features(df: pd.DataFrame, schema: Optional[SensorSchema] = None) -> List[str]:
    """
    Identify valid features for the model.
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
        # Check against exclusions
        if any(excl.lower() in col.lower() for excl in excluded_keywords):
            continue
            
        # Only include numeric columns
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
            
        features.append(col)
        
    return features

class IsolationForestEngine:
    def __init__(self, config: Optional[IsolationForestConfig] = None):
        self.config = config or IsolationForestConfig()
        self.model = IsolationForest(
            n_estimators=self.config.n_estimators,
            max_samples=self.config.max_samples,
            contamination=self.config.contamination,
            max_features=self.config.max_features,
            random_state=self.config.random_state,
            n_jobs=self.config.n_jobs
        )
        self.imputer = SimpleImputer(strategy="median")
        self.features: List[str] = []
        self.threshold: float = 0.0
        self.is_fitted = False
        
    def prepare_data(self, df: pd.DataFrame, is_training: bool = False) -> np.ndarray:
        """Extract and impute features."""
        if not self.features:
            raise ValueError("Features not defined. Call fit() or load a trained model first.")
            
        # Ensure all required features are present
        missing_cols = [f for f in self.features if f not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required features: {missing_cols}")
            
        X = df[self.features].copy()
        
        # Handle infinities
        X.replace([np.inf, -np.inf], np.nan, inplace=True)
        
        if is_training:
            X_imputed = self.imputer.fit_transform(X)
        else:
            X_imputed = self.imputer.transform(X)
            
        return X_imputed

    def fit(self, df: pd.DataFrame, schema: Optional[SensorSchema] = None):
        """Train the Isolation Forest model on the reference dataset."""
        self.features = get_isolation_forest_features(df, schema)
        X = self.prepare_data(df, is_training=True)
        
        self.model.fit(X)
        
        # Calculate threshold on training data based on percentile
        # decision_function returns positive for inliers, negative for outliers
        # We invert it so higher = more anomalous
        scores = -self.model.decision_function(X)
        self.threshold = np.percentile(scores, self.config.threshold_percentile)
        self.is_fitted = True
        
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate anomaly scores and predictions for a dataset."""
        if not self.is_fitted:
            raise ValueError("Model is not fitted.")
            
        X = self.prepare_data(df, is_training=False)
        
        # Raw scores: lower is more anomalous in sklearn
        # We invert so higher is more anomalous
        scores = -self.model.decision_function(X)
        
        # Prediction based on threshold
        predictions = scores >= self.threshold
        
        results = pd.DataFrame(index=df.index)
        results["anomaly_score"] = scores
        results["anomaly_prediction"] = predictions
        
        return results

    def save(self, path: Union[str, Path]):
        """Save the trained model and its metadata."""
        if not self.is_fitted:
            raise ValueError("Cannot save an unfitted model.")
            
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        state = {
            "model": self.model,
            "imputer": self.imputer,
            "features": self.features,
            "threshold": self.threshold,
            "config": self.config
        }
        joblib.dump(state, path)

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'IsolationForestEngine':
        """Load a trained model."""
        state = joblib.load(path)
        
        engine = cls(config=state["config"])
        engine.model = state["model"]
        engine.imputer = state["imputer"]
        engine.features = state["features"]
        engine.threshold = state["threshold"]
        engine.is_fitted = True
        
        return engine
