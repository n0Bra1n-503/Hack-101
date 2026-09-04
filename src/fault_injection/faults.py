import numpy as np
import pandas as pd
from typing import Tuple

def inject_spike(
    series: pd.Series,
    start_idx: int,
    duration: int,
    magnitude: float,
    direction: int = 1
) -> pd.Series:
    """Inject an isolated spike."""
    s_injected = series.copy()
    
    end_idx = min(start_idx + duration, len(s_injected))
    for i in range(start_idx, end_idx):
        if not pd.isna(s_injected.iloc[i]):
            s_injected.iloc[i] += magnitude * direction
            
    return s_injected

def inject_drift(
    series: pd.Series,
    start_idx: int,
    duration: int,
    magnitude: float,
    direction: int = 1
) -> pd.Series:
    """Inject a gradual linear drift."""
    s_injected = series.copy()
    end_idx = min(start_idx + duration, len(s_injected))
    
    actual_duration = end_idx - start_idx
    if actual_duration <= 0:
        return s_injected
        
    # Linear drift from 0 to magnitude
    drift_values = np.linspace(0, magnitude, actual_duration) * direction
    
    for i in range(actual_duration):
        idx = start_idx + i
        if not pd.isna(s_injected.iloc[idx]):
            s_injected.iloc[idx] += drift_values[i]
            
    return s_injected

def inject_frozen(
    series: pd.Series,
    start_idx: int,
    duration: int
) -> pd.Series:
    """Freeze a sensor at its current value."""
    s_injected = series.copy()
    end_idx = min(start_idx + duration, len(s_injected))
    
    frozen_val = s_injected.iloc[start_idx]
    if pd.isna(frozen_val):
        # Find nearest previous valid value if possible
        valid_history = s_injected.iloc[:start_idx].dropna()
        if len(valid_history) > 0:
            frozen_val = valid_history.iloc[-1]
        else:
            frozen_val = 0.0 # Fallback
            
    for i in range(start_idx, end_idx):
        s_injected.iloc[i] = frozen_val
        
    return s_injected

def inject_dropout(
    series: pd.Series,
    start_idx: int,
    duration: int
) -> pd.Series:
    """Inject sensor dropout (NaNs)."""
    s_injected = series.copy()
    end_idx = min(start_idx + duration, len(s_injected))
    
    for i in range(start_idx, end_idx):
        s_injected.iloc[i] = np.nan
        
    return s_injected

def inject_abrupt_jump(
    series: pd.Series,
    start_idx: int,
    duration: int,
    magnitude: float,
    direction: int = 1
) -> pd.Series:
    """Inject an abrupt jump to a new persistent level."""
    s_injected = series.copy()
    end_idx = min(start_idx + duration, len(s_injected))
    
    # Abrupt jump persists fully for the entire duration (unlike spike which is short, this forms a new level)
    for i in range(start_idx, end_idx):
        if not pd.isna(s_injected.iloc[i]):
            s_injected.iloc[i] += magnitude * direction
            
    return s_injected

def inject_multivariate_inconsistency(
    series: pd.Series,
    start_idx: int,
    duration: int,
    magnitude: float,
    direction: int = 1
) -> pd.Series:
    """Inject a fault onto one sensor that breaks its normal physical relationship."""
    # Under the hood, this is an abrupt jump or drift applied solely to one sensor
    # while explicitly leaving the others alone. 
    # For the individual sensor transformation, it behaves like an abrupt jump.
    return inject_abrupt_jump(series, start_idx, duration, magnitude, direction)
