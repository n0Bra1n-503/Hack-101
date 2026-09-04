from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from src.data.schema import SensorSchema


def analyze_correlations(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """Analyze linear (Pearson) and monotonic (Spearman) relationships among sensors.

    Parameters
    ----------
    df : pd.DataFrame
        Sensor DataFrame.
    schema : Optional[SensorSchema]
        Sensor schema.
    output_path : Optional[Path]
        Path to save correlation_matrix.csv.

    Returns
    -------
    pd.DataFrame
        Correlation matrix across available sensor variables.
    """
    if schema is None:
        schema = SensorSchema()

    available_sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if len(available_sensors) < 2:
        return pd.DataFrame()

    sensor_df = df[available_sensors].apply(pd.to_numeric, errors="coerce")

    corr_pearson = sensor_df.corr(method="pearson").round(4)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        corr_pearson.to_csv(out_p)

    return corr_pearson
