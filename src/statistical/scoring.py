from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from src.data.schema import SensorSchema
from .baselines import BaselineReference, SensorStatRecord
from .config import StatisticalConfig


def compute_standardized_scores(
    series: pd.Series,
    stat: SensorStatRecord,
    eps: float = 1e-5,
) -> Tuple[pd.Series, pd.Series]:
    """Compute standard Z-score and robust modified Z-score against a reference stat record."""
    vals = pd.to_numeric(series, errors="coerce")
    is_pos_inf = vals == np.inf
    is_neg_inf = vals == -np.inf
    clean_vals = vals.replace([np.inf, -np.inf], np.nan)
    
    # 1. Standard Z-score
    if stat.std > eps:
        zscore = (clean_vals - stat.mean) / stat.std
    else:
        # If std is 0, any deviation from mean is extreme
        zscore = pd.Series(0.0, index=vals.index)
        dev = clean_vals - stat.mean
        zscore[dev > eps] = 99.0
        zscore[dev < -eps] = -99.0

    # 2. Robust Score (using IQR/1.349 or MAD*1.4826)
    scale = (stat.iqr / 1.349) if stat.iqr > eps else (stat.mad * 1.4826)
    if scale > eps:
        robust_score = (clean_vals - stat.median) / scale
    else:
        robust_score = pd.Series(0.0, index=vals.index)
        dev = clean_vals - stat.median
        robust_score[dev > eps] = 99.0
        robust_score[dev < -eps] = -99.0

    # Map +/- inf to explicit safe extreme scores (+/- 99.0)
    zscore[is_pos_inf] = 99.0
    zscore[is_neg_inf] = -99.0
    robust_score[is_pos_inf] = 99.0
    robust_score[is_neg_inf] = -99.0

    # Retain NaNs where original value is NaN (excluding infs which were handled)
    nan_mask = vals.isna() & (~is_pos_inf) & (~is_neg_inf)
    zscore[nan_mask] = np.nan
    robust_score[nan_mask] = np.nan

    return zscore, robust_score


def calculate_statistical_scores(
    df: pd.DataFrame,
    baselines: BaselineReference,
    config: StatisticalConfig,
    schema: Optional[SensorSchema] = None,
) -> pd.DataFrame:
    """Vectorized calculation of all statistical deviation metrics and baseline scores.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe (features or raw).
    baselines : BaselineReference
        Fitted baseline parameters.
    config : StatisticalConfig
        Configuration thresholds and weights.
    schema : SensorSchema, optional
        Column schema.

    Returns
    -------
    pd.DataFrame
        DataFrame containing computed statistical scores.
    """
    if schema is None:
        schema = SensorSchema()

    df_scores = pd.DataFrame(index=df.index)
    has_station = schema.station_id in df.columns
    sensor_cols = [c for c in schema.required_sensor_columns if c in df.columns]

    # Hour series for diurnal scoring
    hour_series = None
    if schema.hour in df.columns:
        hour_series = pd.to_numeric(df[schema.hour], errors="coerce")
    elif schema.timestamp in df.columns:
        hour_series = pd.to_datetime(df[schema.timestamp], errors="coerce").dt.hour

    for sensor in sensor_cols:
        s_vals = pd.to_numeric(df[sensor], errors="coerce")

        # ----------------------------------------------------
        # 1. Global Baseline Scores
        # ----------------------------------------------------
        g_stat = baselines.global_stats.get(sensor, SensorStatRecord())
        g_z, g_rob = compute_standardized_scores(s_vals, g_stat)
        df_scores[f"{sensor}_global_zscore"] = g_z
        df_scores[f"{sensor}_global_robust_score"] = g_rob

        # ----------------------------------------------------
        # 2. Station-Specific Baseline Scores
        # ----------------------------------------------------
        if has_station and sensor in baselines.station_stats:
            stn_z = pd.Series(np.nan, index=df.index, dtype=float)
            stn_rob = pd.Series(np.nan, index=df.index, dtype=float)

            for stn_val, idxs in df.groupby(schema.station_id).groups.items():
                stn_key = str(stn_val)
                stat_rec = baselines.station_stats[sensor].get(stn_key, g_stat)
                z_sub, rob_sub = compute_standardized_scores(s_vals.loc[idxs], stat_rec)
                stn_z.loc[idxs] = z_sub
                stn_rob.loc[idxs] = rob_sub

            df_scores[f"{sensor}_station_zscore"] = stn_z
            df_scores[f"{sensor}_station_robust_score"] = stn_rob
            # Preferred baseline for single-station evaluation is station-specific
            df_scores[f"{sensor}_zscore"] = stn_z
            df_scores[f"{sensor}_robust_score"] = stn_rob
        else:
            df_scores[f"{sensor}_zscore"] = g_z
            df_scores[f"{sensor}_robust_score"] = g_rob

        # ----------------------------------------------------
        # 3. Diurnal (Time-of-day) Baseline Scores
        # ----------------------------------------------------
        if hour_series is not None and sensor in baselines.diurnal_stats:
            diurnal_z = pd.Series(np.nan, index=df.index, dtype=float)
            df_temp = pd.DataFrame({"stn": df[schema.station_id] if has_station else "all", "hour": hour_series}, index=df.index)

            if has_station and sensor in baselines.station_diurnal_stats:
                for (stn_val, h_val), idxs in df_temp.groupby(["stn", "hour"]).groups.items():
                    if pd.isna(h_val):
                        continue
                    stn_key = str(stn_val)
                    h_int = int(h_val)
                    stat_rec = baselines.station_diurnal_stats[sensor].get(
                        (stn_key, h_int),
                        baselines.station_stats.get(sensor, {}).get(stn_key, g_stat)
                    )
                    z_sub, _ = compute_standardized_scores(s_vals.loc[idxs], stat_rec)
                    diurnal_z.loc[idxs] = z_sub
            else:
                for h_val, idxs in df_temp.groupby("hour").groups.items():
                    if pd.isna(h_val):
                        continue
                    h_int = int(h_val)
                    stat_rec = baselines.diurnal_stats[sensor].get(h_int, g_stat)
                    z_sub, _ = compute_standardized_scores(s_vals.loc[idxs], stat_rec)
                    diurnal_z.loc[idxs] = z_sub

            df_scores[f"{sensor}_diurnal_zscore"] = diurnal_z

        # ----------------------------------------------------
        # 4. Rolling Baseline Deviation (Short & Medium Windows)
        # ----------------------------------------------------
        # Reuse Step 3 features if present, otherwise compute
        roll_z_col_6 = f"{sensor}_zscore_roll_6"
        roll_dev_col_6 = f"{sensor}_dev_roll_mean_6"

        if roll_z_col_6 in df.columns:
            df_scores[f"{sensor}_rolling_zscore"] = df[roll_z_col_6]
        elif roll_dev_col_6 in df.columns and f"{sensor}_roll_std_6" in df.columns:
            safe_std = df[f"{sensor}_roll_std_6"].replace(0, 1e-5)
            df_scores[f"{sensor}_rolling_zscore"] = df[roll_dev_col_6] / safe_std
        else:
            # On-the-fly rolling deviation with shifted window (no leakage)
            if has_station:
                shifted = df.groupby(schema.station_id)[sensor].shift(1)
                temp = pd.DataFrame({"stn": df[schema.station_id], "val": shifted})
                roll_mean = temp.groupby("stn")["val"].rolling(6, min_periods=2).mean().reset_index(level=0, drop=True)
                roll_std = temp.groupby("stn")["val"].rolling(6, min_periods=2).std().reset_index(level=0, drop=True)
            else:
                shifted = s_vals.shift(1)
                roll_mean = shifted.rolling(6, min_periods=2).mean()
                roll_std = shifted.rolling(6, min_periods=2).std()

            safe_roll_std = roll_std.replace(0, 1e-5)
            clean_s = s_vals.replace([np.inf, -np.inf], np.nan)
            df_scores[f"{sensor}_rolling_zscore"] = (clean_s - roll_mean) / safe_roll_std
            df_scores.loc[s_vals == np.inf, f"{sensor}_rolling_zscore"] = 99.0
            df_scores.loc[s_vals == -np.inf, f"{sensor}_rolling_zscore"] = -99.0

        # Clean rolling zscore if from existing columns
        df_scores[f"{sensor}_rolling_zscore"] = (
            df_scores[f"{sensor}_rolling_zscore"].replace([np.inf], 99.0).replace([-np.inf], -99.0)
        )

        if roll_dev_col_6 in df.columns:
            df_scores[f"{sensor}_rolling_deviation"] = df[roll_dev_col_6].replace([np.inf], 9999.0).replace([-np.inf], -9999.0)
        else:
            clean_s = s_vals.replace([np.inf, -np.inf], np.nan)
            df_scores[f"{sensor}_rolling_deviation"] = clean_s - roll_mean
            df_scores.loc[s_vals == np.inf, f"{sensor}_rolling_deviation"] = 9999.0
            df_scores.loc[s_vals == -np.inf, f"{sensor}_rolling_deviation"] = -9999.0

        # ----------------------------------------------------
        # 5. Cross-Station Deviation (Peer Median Exclusion)
        # ----------------------------------------------------
        peer_dev_col = f"{sensor}_dev_peer_median"
        if peer_dev_col in df.columns:
            df_scores[f"{sensor}_cross_station_deviation"] = (
                df[peer_dev_col].replace([np.inf], 9999.0).replace([-np.inf], -9999.0)
            )
        elif has_station and schema.timestamp in df.columns:
            # Compute peer median excluding self on the fly
            clean_sensor_df = df.copy()
            clean_sensor_df[sensor] = pd.to_numeric(clean_sensor_df[sensor], errors="coerce").replace([np.inf, -np.inf], np.nan)
            pivot = clean_sensor_df.pivot_table(index=schema.timestamp, columns=schema.station_id, values=sensor, aggfunc="mean")
            if pivot.shape[1] >= 2:
                recs = []
                for stn in pivot.columns:
                    peers = [c for c in pivot.columns if c != stn]
                    peer_med = pivot[peers].median(axis=1)
                    recs.append(pd.DataFrame({schema.timestamp: peer_med.index, schema.station_id: stn, "_pmed": peer_med.values}))
                peer_df = pd.concat(recs, ignore_index=True)
                tmp = df[[schema.station_id, schema.timestamp]].copy()
                tmp["__idx"] = tmp.index
                m = pd.merge(tmp, peer_df, on=[schema.station_id, schema.timestamp], how="left").sort_values("__idx").set_index("__idx")
                clean_s = s_vals.replace([np.inf, -np.inf], np.nan)
                df_scores[f"{sensor}_cross_station_deviation"] = clean_s - m["_pmed"]
                df_scores.loc[s_vals == np.inf, f"{sensor}_cross_station_deviation"] = 9999.0
                df_scores.loc[s_vals == -np.inf, f"{sensor}_cross_station_deviation"] = -9999.0
            else:
                df_scores[f"{sensor}_cross_station_deviation"] = np.nan
        else:
            df_scores[f"{sensor}_cross_station_deviation"] = np.nan

    return df_scores
