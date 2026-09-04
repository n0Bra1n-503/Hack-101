from typing import Dict, List, Optional
import json
import numpy as np
import pandas as pd
from src.data.schema import SensorSchema
from .config import StatisticalConfig


def _clip_score(val: pd.Series, low_thr: float, high_thr: float) -> pd.Series:
    """Linearly map absolute value in [low_thr, high_thr] to [0.0, 1.0], clipping outside."""
    abs_v = val.abs()
    scaled = (abs_v - low_thr) / max(1e-5, (high_thr - low_thr))
    return scaled.clip(lower=0.0, upper=1.0).fillna(0.0)


def extract_statistical_evidence(
    df_raw: pd.DataFrame,
    df_scores: pd.DataFrame,
    config: StatisticalConfig,
    schema: Optional[SensorSchema] = None,
) -> pd.DataFrame:
    """Generate discrete evidence flags, multi-sensor indicators, composite scores, and explainable reasons.

    Parameters
    ----------
    df_raw : pd.DataFrame
        Original dataframe with raw values and station identifiers.
    df_scores : pd.DataFrame
        Computed statistical scores dataframe from calculate_statistical_scores.
    config : StatisticalConfig
        Threshold and scoring configuration.
    schema : SensorSchema, optional
        Column schema.

    Returns
    -------
    pd.DataFrame
        Enriched DataFrame containing flags, composite score, severity, and reasons.
    """
    if schema is None:
        schema = SensorSchema()

    df_ev = pd.DataFrame(index=df_scores.index)
    sensor_cols = [c for c in schema.required_sensor_columns if c in df_raw.columns]

    w_z = config.weights.get("zscore", 0.20)
    w_rob = config.weights.get("robust", 0.20)
    w_roll = config.weights.get("rolling", 0.25)
    w_diu = config.weights.get("diurnal", 0.15)
    w_cs = config.weights.get("cross_station", 0.20)

    sensor_unusual_flags = {}
    sensor_scores = {}
    evidence_flags_list = []

    for sensor in sensor_cols:
        # Z-score flag
        z_col = f"{sensor}_zscore"
        z_unusual = (df_scores[z_col].abs() >= config.zscore_threshold).fillna(False)
        df_ev[f"{sensor}_z_unusual"] = z_unusual
        evidence_flags_list.append(z_unusual)

        # Robust score flag
        rob_col = f"{sensor}_robust_score"
        rob_unusual = (df_scores[rob_col].abs() >= config.robust_threshold).fillna(False)
        df_ev[f"{sensor}_robust_unusual"] = rob_unusual
        evidence_flags_list.append(rob_unusual)

        # Rolling score flag
        roll_col = f"{sensor}_rolling_zscore"
        roll_unusual = (df_scores[roll_col].abs() >= config.rolling_z_threshold).fillna(False)
        df_ev[f"{sensor}_rolling_unusual"] = roll_unusual
        evidence_flags_list.append(roll_unusual)

        # Diurnal score flag (if present)
        diu_col = f"{sensor}_diurnal_zscore"
        if diu_col in df_scores.columns:
            diu_unusual = (df_scores[diu_col].abs() >= config.diurnal_z_threshold).fillna(False)
            df_ev[f"{sensor}_diurnal_unusual"] = diu_unusual
            evidence_flags_list.append(diu_unusual)
        else:
            diu_unusual = pd.Series(False, index=df_scores.index)

        # Cross-station deviation flag
        cs_col = f"{sensor}_cross_station_deviation"
        cs_thr = config.cross_station_dev_thresholds.get(sensor, 4.0)
        cs_unusual = (df_scores[cs_col].abs() >= cs_thr).fillna(False)
        df_ev[f"{sensor}_cross_station_unusual"] = cs_unusual
        evidence_flags_list.append(cs_unusual)

        # Sensor-level aggregate unusual flag
        s_unusual = z_unusual | rob_unusual | roll_unusual | diu_unusual | cs_unusual
        df_ev[f"{sensor}_unusual"] = s_unusual
        sensor_unusual_flags[sensor] = s_unusual

        # Continuous single-sensor anomaly score
        s_z_norm = _clip_score(df_scores[z_col], config.zscore_threshold * 0.5, config.zscore_threshold * 1.5)
        s_rob_norm = _clip_score(df_scores[rob_col], config.robust_threshold * 0.5, config.robust_threshold * 1.5)
        s_roll_norm = _clip_score(df_scores[roll_col], config.rolling_z_threshold * 0.5, config.rolling_z_threshold * 1.5)
        s_diu_norm = (
            _clip_score(df_scores[diu_col], config.diurnal_z_threshold * 0.5, config.diurnal_z_threshold * 1.5)
            if diu_col in df_scores.columns
            else pd.Series(0.0, index=df_scores.index)
        )
        s_cs_norm = _clip_score(df_scores[cs_col], cs_thr * 0.5, cs_thr * 1.5)

        comp_sensor_score = (
            w_z * s_z_norm
            + w_rob * s_rob_norm
            + w_roll * s_roll_norm
            + w_diu * s_diu_norm
            + w_cs * s_cs_norm
        )
        sensor_scores[sensor] = comp_sensor_score
        df_ev[f"{sensor}_anomaly_score"] = comp_sensor_score.round(4)

    # --------------------------------------------------------
    # Multi-sensor & System-level Evidence Aggregations
    # --------------------------------------------------------
    for sensor in schema.required_sensor_columns:
        if f"{sensor}_unusual" not in df_ev.columns:
            df_ev[f"{sensor}_unusual"] = False

    # Count how many of (temperature, pressure, humidity) are unusual
    sensor_flag_df = pd.DataFrame({s: sensor_unusual_flags[s] for s in sensor_cols})
    df_ev["unusual_sensor_count"] = sensor_flag_df.sum(axis=1)
    df_ev["is_isolated_sensor_anomaly"] = df_ev["unusual_sensor_count"] == 1
    df_ev["is_concurrent_multisensor_anomaly"] = df_ev["unusual_sensor_count"] >= 2

    # Global evidence flags
    rolling_cols = [f"{s}_rolling_unusual" for s in sensor_cols]
    df_ev["rolling_deviation_high"] = df_ev[rolling_cols].any(axis=1)

    cs_cols = [f"{s}_cross_station_unusual" for s in sensor_cols]
    df_ev["cross_station_deviation_high"] = df_ev[cs_cols].any(axis=1)

    # Total specific evidence counts
    all_evidence_df = pd.DataFrame(evidence_flags_list).T
    df_ev["evidence_count"] = all_evidence_df.sum(axis=1)

    # Composite Statistical Anomaly Score (Max across sensors, with small boost if concurrent)
    if sensor_scores:
        scores_matrix = pd.DataFrame(sensor_scores)
        max_sensor_score = scores_matrix.max(axis=1)
        # 10% boost for concurrent multi-sensor statistical anomalies
        concurrent_mult = np.where(df_ev["is_concurrent_multisensor_anomaly"], 1.10, 1.0)
        composite_score = (max_sensor_score * concurrent_mult).clip(lower=0.0, upper=1.0)
    else:
        composite_score = pd.Series(0.0, index=df_scores.index)

    df_ev["statistical_anomaly_score"] = composite_score.round(4)

    # Severity classification
    severity = pd.Series("NORMAL", index=df_scores.index)
    severity[composite_score >= config.suspicious_score_threshold] = "SLIGHTLY_UNUSUAL"
    severity[composite_score >= config.strongly_unusual_score_threshold] = "STRONGLY_UNUSUAL"
    df_ev["anomaly_severity"] = severity

    # Is statistically suspicious flag
    df_ev["is_statistically_suspicious"] = (
        (composite_score >= config.suspicious_score_threshold)
        | (df_ev["evidence_count"] >= config.min_evidence_for_suspicious)
    )

    # --------------------------------------------------------
    # Generate Explainable Reasons (Vectorized / Iterative where suspicious)
    # --------------------------------------------------------
    reasons_list: List[str] = []
    
    # Generate reasons efficiently for flagged rows
    for idx, row in df_ev.iterrows():
        if not row["is_statistically_suspicious"]:
            reasons_list.append("[]")
            continue

        r_items: List[str] = []
        for s in sensor_cols:
            s_label = s.capitalize()
            val = df_raw.loc[idx, s] if s in df_raw.columns else None
            z_val = df_scores.loc[idx, f"{s}_zscore"]
            rob_val = df_scores.loc[idx, f"{s}_robust_score"]
            roll_val = df_scores.loc[idx, f"{s}_rolling_zscore"]
            cs_val = df_scores.loc[idx, f"{s}_cross_station_deviation"]

            if row.get(f"{s}_z_unusual", False) or row.get(f"{s}_robust_unusual", False):
                r_items.append(
                    f"{s_label} ({val:.2f}) deviates significantly from baseline (z={z_val:+.2f}, robust_z={rob_val:+.2f})"
                )

            if row.get(f"{s}_rolling_unusual", False):
                dev_val = df_scores.loc[idx, f"{s}_rolling_deviation"]
                r_items.append(
                    f"{s_label} changed abruptly from recent rolling mean (z_roll={roll_val:+.2f}, dev={dev_val:+.2f})"
                )

            if row.get(f"{s}_cross_station_unusual", False):
                r_items.append(
                    f"{s_label} deviates substantially from peer station median (peer_dev={cs_val:+.2f})"
                )

        if row["is_isolated_sensor_anomaly"]:
            unusual_names = [s.capitalize() for s in sensor_cols if row.get(f"{s}_unusual", False)]
            if unusual_names:
                r_items.append(
                    f"Isolated anomaly: only {', '.join(unusual_names)} is statistically unusual while other sensors remain normal"
                )

        if row["is_concurrent_multisensor_anomaly"]:
            unusual_names = [s.capitalize() for s in sensor_cols if row.get(f"{s}_unusual", False)]
            r_items.append(
                f"Concurrent multi-sensor anomaly: {', '.join(unusual_names)} show concurrent statistical deviations"
            )

        reasons_list.append(json.dumps(r_items))

    df_ev["reasons"] = reasons_list

    return df_ev
