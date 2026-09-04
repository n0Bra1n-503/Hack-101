import pandas as pd
from typing import Dict, Any, Tuple
from src.data.schema import SensorSchema

def build_cross_sensor_features(df: pd.DataFrame, schema: SensorSchema) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Generate features modeling relationships between sensors (e.g. Temperature vs Humidity)."""
    df_feat = pd.DataFrame(index=df.index)
    metadata = {}
    
    has_temp = schema.temperature in df.columns
    has_humid = schema.humidity in df.columns
    has_press = schema.pressure in df.columns
    
    if has_temp and has_humid:
        # Temperature and Humidity are strongly inversely correlated
        # Creating a simple linear residual feature based on naive domain assumption 
        # (higher temp -> lower humidity usually). A basic indicator is the product or sum of normalized values.
        # But even simpler: just track if they are moving in the SAME direction (which is suspicious).
        
        # We need their deltas for this. But since delta calculation is separate, 
        # we will do a simple concurrent step feature: Temp * Humidity
        temp_val = pd.to_numeric(df[schema.temperature], errors="coerce")
        humid_val = pd.to_numeric(df[schema.humidity], errors="coerce")
        
        # Cross product (sometimes used to approximate heat index or vapor pressure aspects implicitly)
        df_feat["temp_humid_product"] = temp_val * humid_val
        metadata["temp_humid_product"] = {"category": "cross_sensor", "description": "Product of temperature and humidity", "uses_history": False}

        # Temperature/Humidity Ratio
        safe_humid = humid_val.replace(0, 1e-5)
        df_feat["temp_humid_ratio"] = temp_val / safe_humid
        metadata["temp_humid_ratio"] = {"category": "cross_sensor", "description": "Ratio of temperature to humidity", "uses_history": False}

    if has_temp and has_press:
        temp_val = pd.to_numeric(df[schema.temperature], errors="coerce")
        press_val = pd.to_numeric(df[schema.pressure], errors="coerce")
        
        # Simple ratio (rough analogue to air density variations)
        safe_temp = temp_val.replace(0, 1e-5)
        df_feat["press_temp_ratio"] = press_val / safe_temp
        metadata["press_temp_ratio"] = {"category": "cross_sensor", "description": "Ratio of pressure to temperature", "uses_history": False}

    return df_feat, metadata
