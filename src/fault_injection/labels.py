import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from .config import FaultType

@dataclass
class FaultEvent:
    event_id: str
    station_id: str
    sensor: str
    fault_type: FaultType
    start_timestamp: Any
    end_timestamp: Any
    start_idx: int
    end_idx: int
    magnitude: float
    seed: int
    
    def to_dict(self):
        d = asdict(self)
        d["fault_type"] = self.fault_type.value
        return d

def initialize_ground_truth(df: pd.DataFrame, schema) -> pd.DataFrame:
    """Initialize a ground-truth labels DataFrame aligned with the input dataset."""
    df_gt = pd.DataFrame(index=df.index)
    
    if schema.station_id in df.columns:
        df_gt["station_id"] = df[schema.station_id]
        
    if schema.timestamp in df.columns:
        df_gt["timestamp"] = df[schema.timestamp]
        
    df_gt["fault_present"] = False
    df_gt["fault_type"] = FaultType.NORMAL.value
    df_gt["affected_sensor"] = "NONE"
    df_gt["event_id"] = "NONE"
    
    return df_gt
