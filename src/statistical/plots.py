from pathlib import Path
from typing import Optional, Union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema


def generate_baseline_plots(
    df_results: pd.DataFrame,
    output_dir: Union[str, Path],
    schema: Optional[SensorSchema] = None,
) -> None:
    """Generate lightweight validation plots for the statistical baseline detector.

    Parameters
    ----------
    df_results : pd.DataFrame
        Enriched DataFrame with statistical results.
    output_dir : Union[str, Path]
        Target directory to save generated plots.
    schema : Optional[SensorSchema]
        Schema definition for sensor columns.
    """
    if schema is None:
        schema = SensorSchema()

    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    total_obs = len(df_results)
    if total_obs == 0:
        return

    # Set aesthetic theme
    sns.set_theme(style="darkgrid", palette="muted")
    plt.rcParams.update({"font.sans-serif": "DejaVu Sans", "figure.autolayout": True})

    sensor_cols = [c for c in schema.required_sensor_columns if c in df_results.columns]
    is_suspicious = df_results.get("is_statistically_suspicious", pd.Series(False, index=df_results.index))

    # ----------------------------------------------------
    # 1. Sensor Time Series with Suspicious Observations Highlighted
    # ----------------------------------------------------
    # Plot first station or representative sample
    has_station = schema.station_id in df_results.columns
    sample_df = df_results
    if has_station:
        stations = df_results[schema.station_id].unique()
        sample_stn = stations[0]
        sample_df = df_results[df_results[schema.station_id] == sample_stn]
        title_prefix = f"Station {sample_stn} - "
    else:
        title_prefix = ""

    # Subsample if very large for clean plotting
    if len(sample_df) > 1000:
        sample_df = sample_df.iloc[:1000]

    n_sensors = len(sensor_cols)
    if n_sensors > 0:
        fig, axes = plt.subplots(n_sensors, 1, figsize=(14, 3.5 * n_sensors), sharex=True)
        if n_sensors == 1:
            axes = [axes]

        x_axis = sample_df.index
        if schema.timestamp in sample_df.columns:
            try:
                x_axis = pd.to_datetime(sample_df[schema.timestamp])
            except Exception:
                x_axis = sample_df.index

        for ax, sensor in zip(axes, sensor_cols):
            y_vals = sample_df[sensor]
            susp_mask = sample_df.get("is_statistically_suspicious", pd.Series(False, index=sample_df.index))

            ax.plot(x_axis, y_vals, label=f"{sensor.capitalize()} Normal", color="#3b82f6", lw=1.2, alpha=0.85)
            if susp_mask.any():
                ax.scatter(
                    x_axis[susp_mask],
                    y_vals[susp_mask],
                    color="#ef4444",
                    s=32,
                    label="Statistically Suspicious",
                    zorder=5,
                    edgecolor="black",
                    linewidth=0.5,
                )

            ax.set_title(f"{title_prefix}{sensor.capitalize()} Sensor Readings with Statistical Flags", fontsize=12, fontweight="bold")
            ax.set_ylabel(sensor.capitalize(), fontsize=11)
            ax.legend(loc="upper right")

        plt.xlabel("Timestamp / Index", fontsize=11)
        fig.tight_layout()
        fig.savefig(out_p / "time_series_anomalies.png", dpi=200)
        plt.close(fig)

    # ----------------------------------------------------
    # 2. Distribution of Standard Z-Scores with Threshold Markers
    # ----------------------------------------------------
    z_cols = [f"{s}_zscore" for s in sensor_cols if f"{s}_zscore" in df_results.columns]
    if z_cols:
        fig, axes = plt.subplots(1, len(z_cols), figsize=(5 * len(z_cols), 4.5))
        if len(z_cols) == 1:
            axes = [axes]

        for ax, z_col in zip(axes, z_cols):
            clean_z = df_results[z_col].dropna()
            clean_z_capped = clean_z.clip(-6.0, 6.0)
            sns.histplot(clean_z_capped, kde=True, ax=ax, color="#6366f1", bins=30, alpha=0.6)
            ax.axvline(3.0, color="#ef4444", linestyle="--", lw=1.5, label="+3σ Threshold")
            ax.axvline(-3.0, color="#ef4444", linestyle="--", lw=1.5, label="-3σ Threshold")
            ax.set_title(f"Distribution: {z_col}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Z-Score", fontsize=10)
            ax.legend(loc="upper right")

        fig.tight_layout()
        fig.savefig(out_p / "zscore_distributions.png", dpi=200)
        plt.close(fig)

    # ----------------------------------------------------
    # 3. Composite Anomaly Score Distribution & Severity Breakdown
    # ----------------------------------------------------
    if "statistical_anomaly_score" in df_results.columns:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        scores = df_results["statistical_anomaly_score"].dropna()
        sns.histplot(scores, kde=True, ax=ax1, color="#10b981", bins=25, alpha=0.7)
        ax1.axvline(0.40, color="#f59e0b", linestyle="--", lw=1.5, label="Suspicious (0.40)")
        ax1.axvline(0.70, color="#ef4444", linestyle="--", lw=1.5, label="Strongly Unusual (0.70)")
        ax1.set_title("Statistical Anomaly Score Distribution", fontsize=12, fontweight="bold")
        ax1.set_xlabel("Score [0.0 - 1.0]", fontsize=11)
        ax1.legend(loc="upper right")

        # Severity breakdown bar plot
        if "anomaly_severity" in df_results.columns:
            sev_counts = df_results["anomaly_severity"].value_counts().reindex(["NORMAL", "SLIGHTLY_UNUSUAL", "STRONGLY_UNUSUAL"]).fillna(0)
            colors = ["#10b981", "#f59e0b", "#ef4444"]
            bars = ax2.bar(sev_counts.index, sev_counts.values, color=colors, edgecolor="black", alpha=0.85)
            for bar in bars:
                h = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width() / 2.0, h + total_obs * 0.01, f"{int(h):,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
            ax2.set_title("Observations by Severity Level", fontsize=12, fontweight="bold")
            ax2.set_ylabel("Count", fontsize=11)

        fig.tight_layout()
        fig.savefig(out_p / "anomaly_score_distribution.png", dpi=200)
        plt.close(fig)
