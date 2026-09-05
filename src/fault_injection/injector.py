import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
import uuid

from src.data.schema import SensorSchema
from .config import FaultConfig, FaultType
from .labels import FaultEvent, initialize_ground_truth
from . import faults

class FaultInjector:
    """Engine for injecting controlled sensor faults into dataset."""
    
    def __init__(self, config: Optional[FaultConfig] = None, schema: Optional[SensorSchema] = None):
        self.config = config or FaultConfig()
        self.schema = schema or SensorSchema()
        self.rng = np.random.RandomState(self.config.random_seed)
        self.events: List[FaultEvent] = []
        
    def _generate_event_id(self) -> str:
        return f"FAULT_{uuid.uuid4().hex[:8].upper()}"
        
    def _get_sensor_std(self, df: pd.DataFrame, sensor: str) -> float:
        """Estimate normal standard deviation for realistic magnitude scaling."""
        std = pd.to_numeric(df[sensor], errors="coerce").std()
        if pd.isna(std) or std == 0:
            std = 1.0 # Safe fallback
        return std

    def inject(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Inject faults into a copy of the dataframe.
        
        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (injected_dataset, ground_truth_labels)
        """
        df_injected = df.copy()
        df_gt = initialize_ground_truth(df, self.schema)
        self.events = []
        
        total_obs = len(df)
        if total_obs == 0:
            return df_injected, df_gt
            
        sensors = [s for s in self.schema.required_sensor_columns if s in df.columns]
        if not sensors:
            return df_injected, df_gt
            
        # Target number of fault events based on fault rate
        # Assume average fault duration is ~10 points, adjust event count accordingly
        avg_duration = 10
        target_fault_points = int(total_obs * self.config.fault_rate)
        target_events = max(1, target_fault_points // avg_duration)
        
        # Pre-calculate sensor std for realistic magnitudes
        sensor_stds = {s: self._get_sensor_std(df, s) for s in sensors}
        
        # Keep track of injected indices to prevent overlap if configured
        injected_mask = np.zeros(total_obs, dtype=bool)
        
        fault_types = [
            FaultType.SPIKE,
            FaultType.DRIFT,
            FaultType.FROZEN,
            FaultType.DROPOUT,
            FaultType.ABRUPT_JUMP,
            FaultType.MULTIVARIATE_INCONSISTENCY
        ]
        
        attempts = 0
        max_attempts = target_events * 5
        
        while len(self.events) < target_events and attempts < max_attempts:
            attempts += 1
            
            # Select random fault parameters
            fault_type = self.rng.choice(fault_types)
            sensor = str(self.rng.choice(sensors))
            
            # Select duration based on fault type config
            params = getattr(self.config, f"{fault_type.value.lower()}_params", {})
            duration_min = params.get("duration_min", 1)
            duration_max = params.get("duration_max", 5)
            duration = self.rng.randint(duration_min, duration_max + 1)
            
            # Select start index
            start_idx = self.rng.randint(0, max(1, total_obs - duration))
            end_idx = min(start_idx + duration, total_obs)
            
            # Check overlap
            if not self.config.allow_overlapping_faults:
                if np.any(injected_mask[start_idx:end_idx]):
                    continue
                    
            # Calculate magnitude
            std_val = sensor_stds[sensor]
            mag_min = params.get("magnitude_std_min", 2.0)
            mag_max = params.get("magnitude_std_max", 5.0)
            magnitude = self.rng.uniform(mag_min, mag_max) * std_val
            direction = self.rng.choice([-1, 1])
            
            # Extract relevant series
            series = df_injected[sensor]
            
            # Inject fault
            if fault_type == FaultType.SPIKE:
                series = faults.inject_spike(series, start_idx, duration, magnitude, direction)
            elif fault_type == FaultType.DRIFT:
                series = faults.inject_drift(series, start_idx, duration, magnitude, direction)
            elif fault_type == FaultType.FROZEN:
                series = faults.inject_frozen(series, start_idx, duration)
                magnitude = 0.0 # Not applicable
            elif fault_type == FaultType.DROPOUT:
                series = faults.inject_dropout(series, start_idx, duration)
                magnitude = 0.0
            elif fault_type == FaultType.ABRUPT_JUMP:
                series = faults.inject_abrupt_jump(series, start_idx, duration, magnitude, direction)
            elif fault_type == FaultType.MULTIVARIATE_INCONSISTENCY:
                series = faults.inject_multivariate_inconsistency(series, start_idx, duration, magnitude, direction)
                
            # Apply back to dataframe
            df_injected[sensor] = series
            
            # Record ground truth
            injected_mask[start_idx:end_idx] = True
            
            station = df.iloc[start_idx][self.schema.station_id] if self.schema.station_id in df.columns else "UNKNOWN"
            start_ts = df.iloc[start_idx][self.schema.timestamp] if self.schema.timestamp in df.columns else start_idx
            end_ts = df.iloc[end_idx-1][self.schema.timestamp] if self.schema.timestamp in df.columns else end_idx-1
            
            event = FaultEvent(
                event_id=self._generate_event_id(),
                station_id=str(station),
                sensor=sensor,
                fault_type=fault_type,
                start_timestamp=start_ts,
                end_timestamp=end_ts,
                start_idx=start_idx,
                end_idx=end_idx,
                magnitude=magnitude * direction,
                seed=self.config.random_seed
            )
            self.events.append(event)
            
            # Update ground truth dataframe
            df_gt.iloc[start_idx:end_idx, df_gt.columns.get_loc("fault_present")] = True
            df_gt.iloc[start_idx:end_idx, df_gt.columns.get_loc("fault_type")] = fault_type.value
            df_gt.iloc[start_idx:end_idx, df_gt.columns.get_loc("affected_sensor")] = sensor
            df_gt.iloc[start_idx:end_idx, df_gt.columns.get_loc("event_id")] = event.event_id
            
        return df_injected, df_gt
        
    def get_metadata(self) -> pd.DataFrame:
        """Get summary metadata of all injected events."""
        if not self.events:
            return pd.DataFrame()
        return pd.DataFrame([e.to_dict() for e in self.events])
