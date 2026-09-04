from pathlib import Path
from typing import Optional, Dict, Any, Union
import pandas as pd
from src.data.schema import SensorSchema


def generate_statistical_summary(
    df_results: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> pd.DataFrame:
    """Generate comprehensive summary statistics for the statistical baseline run.

    Parameters
    ----------
    df_results : pd.DataFrame
        Enriched DataFrame output from detect_statistical_anomalies.
    schema : SensorSchema, optional
        Schema configuration.
    output_path : Optional[Union[str, Path]]
        File path to save the summary CSV.

    Returns
    -------
    pd.DataFrame
        Summary DataFrame with metrics.
    """
    if schema is None:
        schema = SensorSchema()

    total_obs = len(df_results)
    if total_obs == 0:
        return pd.DataFrame()

    suspicious_mask = df_results.get("is_statistically_suspicious", pd.Series(False, index=df_results.index))
    num_suspicious = int(suspicious_mask.sum())
    pct_suspicious = round((num_suspicious / total_obs) * 100.0, 2)

    temp_unusual = int(df_results.get("temperature_unusual", pd.Series(False, index=df_results.index)).sum())
    press_unusual = int(df_results.get("pressure_unusual", pd.Series(False, index=df_results.index)).sum())
    humid_unusual = int(df_results.get("humidity_unusual", pd.Series(False, index=df_results.index)).sum())

    rolling_unusual = int(df_results.get("rolling_deviation_high", pd.Series(False, index=df_results.index)).sum())
    cs_unusual = int(df_results.get("cross_station_deviation_high", pd.Series(False, index=df_results.index)).sum())

    isolated_unusual = int(df_results.get("is_isolated_sensor_anomaly", pd.Series(False, index=df_results.index)).sum())
    concurrent_unusual = int(df_results.get("is_concurrent_multisensor_anomaly", pd.Series(False, index=df_results.index)).sum())

    severity_counts = df_results.get("anomaly_severity", pd.Series("NORMAL", index=df_results.index)).value_counts().to_dict()

    summary_rows = [
        {"metric": "total_observations_analyzed", "value": total_obs, "category": "overall"},
        {"metric": "statistically_suspicious_count", "value": num_suspicious, "category": "overall"},
        {"metric": "statistically_suspicious_pct", "value": f"{pct_suspicious}%", "category": "overall"},
        {"metric": "severity_normal_count", "value": severity_counts.get("NORMAL", 0), "category": "severity"},
        {"metric": "severity_slightly_unusual_count", "value": severity_counts.get("SLIGHTLY_UNUSUAL", 0), "category": "severity"},
        {"metric": "severity_strongly_unusual_count", "value": severity_counts.get("STRONGLY_UNUSUAL", 0), "category": "severity"},
        {"metric": "flagged_by_temperature", "value": temp_unusual, "category": "sensor_breakdown"},
        {"metric": "flagged_by_pressure", "value": press_unusual, "category": "sensor_breakdown"},
        {"metric": "flagged_by_humidity", "value": humid_unusual, "category": "sensor_breakdown"},
        {"metric": "flagged_by_rolling_deviation", "value": rolling_unusual, "category": "method_breakdown"},
        {"metric": "flagged_by_cross_station_deviation", "value": cs_unusual, "category": "method_breakdown"},
        {"metric": "isolated_sensor_deviations", "value": isolated_unusual, "category": "multivariate_evidence"},
        {"metric": "concurrent_multisensor_deviations", "value": concurrent_unusual, "category": "multivariate_evidence"},
    ]

    # Station level summaries
    if schema.station_id in df_results.columns:
        for stn, stn_df in df_results.groupby(schema.station_id):
            stn_total = len(stn_df)
            stn_susp = int(stn_df.get("is_statistically_suspicious", pd.Series(False, index=stn_df.index)).sum())
            stn_pct = round((stn_susp / stn_total) * 100.0, 2)
            summary_rows.append({
                "metric": f"station_{stn}_suspicious",
                "value": f"{stn_susp}/{stn_total} ({stn_pct}%)",
                "category": "station_breakdown",
            })

    df_summary = pd.DataFrame(summary_rows)

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(out_p, index=False)

    return df_summary
