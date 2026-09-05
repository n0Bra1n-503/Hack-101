from pathlib import Path
from typing import Optional
import warnings
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from src.data.schema import SensorSchema

warnings.filterwarnings("ignore", category=FutureWarning)


def setup_plot_style():
    """Configure modern, readable aesthetic styles for EDA plots."""
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.titlesize"] = 13
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 11
    plt.rcParams["xtick.labelsize"] = 10
    plt.rcParams["ytick.labelsize"] = 10
    plt.rcParams["figure.titlesize"] = 15


def plot_sensor_distributions(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot histograms and KDE distributions for core sensors."""
    sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if not sensors:
        return

    units = {"temperature": "°C", "pressure": "hPa", "humidity": "%"}
    colors = {"temperature": "#d95f02", "pressure": "#7570b3", "humidity": "#1b9e77"}

    fig, axes = plt.subplots(1, len(sensors), figsize=(5.5 * len(sensors), 4.5))
    if len(sensors) == 1:
        axes = [axes]

    for ax, s in zip(axes, sensors):
        vals = pd.to_numeric(df[s], errors="coerce").dropna()
        unit = units.get(s, "")
        color = colors.get(s, "#3366cc")

        sns.histplot(vals, kde=True, ax=ax, color=color, edgecolor="white", alpha=0.6, bins=30)
        ax.set_title(f"{s.capitalize()} Distribution")
        ax.set_xlabel(f"{s.capitalize()} ({unit})" if unit else s.capitalize())
        ax.set_ylabel("Frequency")

    plt.tight_layout()
    fig.savefig(output_dir / "sensor_distributions.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sensor_boxplots(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot box plots for core sensors."""
    sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if not sensors:
        return

    units = {"temperature": "°C", "pressure": "hPa", "humidity": "%"}
    colors = {"temperature": "#d95f02", "pressure": "#7570b3", "humidity": "#1b9e77"}

    fig, axes = plt.subplots(1, len(sensors), figsize=(4.5 * len(sensors), 4.5))
    if len(sensors) == 1:
        axes = [axes]

    for ax, s in zip(axes, sensors):
        vals = pd.to_numeric(df[s], errors="coerce").dropna()
        unit = units.get(s, "")
        color = colors.get(s, "#3366cc")

        sns.boxplot(y=vals, ax=ax, color=color, width=0.4)
        ax.set_title(f"{s.capitalize()} Spread & Quartiles")
        ax.set_ylabel(f"{s.capitalize()} ({unit})" if unit else s.capitalize())

    plt.tight_layout()
    fig.savefig(output_dir / "sensor_boxplots.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_timeseries_overview(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot time-series traces for each sensor across all stations."""
    if schema.timestamp not in df.columns:
        return

    df_work = df.copy()
    df_work["_dt"] = pd.to_datetime(df_work[schema.timestamp], errors="coerce")
    df_work = df_work.dropna(subset=["_dt"]).sort_values("_dt")

    sensors = [s for s in schema.required_sensor_columns if s in df_work.columns]
    if not sensors:
        return

    units = {"temperature": "°C", "pressure": "hPa", "humidity": "%"}

    fig, axes = plt.subplots(len(sensors), 1, figsize=(13, 3.8 * len(sensors)), sharex=True)
    if len(sensors) == 1:
        axes = [axes]

    has_stations = schema.station_id in df_work.columns

    for ax, s in zip(axes, sensors):
        unit = units.get(s, "")
        if has_stations:
            for stn, stn_df in df_work.groupby(schema.station_id):
                ax.plot(stn_df["_dt"], pd.to_numeric(stn_df[s], errors="coerce"), label=stn, alpha=0.8, linewidth=1.2)
        else:
            ax.plot(df_work["_dt"], pd.to_numeric(df_work[s], errors="coerce"), color="#1f77b4", linewidth=1.2)

        ax.set_title(f"Time-Series: {s.capitalize()}")
        ax.set_ylabel(f"{s.capitalize()} ({unit})" if unit else s.capitalize())
        if has_stations:
            ax.legend(loc="upper right", frameon=True, fontsize=9)

    axes[-1].set_xlabel("Observation Timestamp")
    plt.tight_layout()
    fig.savefig(output_dir / "timeseries_overview.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sampling_intervals(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot distribution of sampling intervals in minutes."""
    if schema.timestamp not in df.columns:
        return

    df_work = df.copy()
    df_work["_dt"] = pd.to_datetime(df_work[schema.timestamp], errors="coerce")
    df_work = df_work.dropna(subset=["_dt"])

    intervals = []
    if schema.station_id in df_work.columns:
        for _, stn_df in df_work.groupby(schema.station_id):
            s_ts = stn_df["_dt"].sort_values().drop_duplicates()
            deltas = s_ts.diff().dt.total_seconds().dropna() / 60.0
            intervals.extend(deltas.tolist())
    else:
        s_ts = df_work["_dt"].sort_values().drop_duplicates()
        deltas = s_ts.diff().dt.total_seconds().dropna() / 60.0
        intervals.extend(deltas.tolist())

    if not intervals:
        return

    series_int = pd.Series(intervals)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.histplot(series_int, bins=30, ax=ax, color="#2b5c8f", edgecolor="white")
    ax.set_title("Sampling Interval Distribution (Consecutive Readings)")
    ax.set_xlabel("Sampling Interval (Minutes)")
    ax.set_ylabel("Frequency (Pairs of Consecutive Observations)")

    plt.tight_layout()
    fig.savefig(output_dir / "sampling_intervals.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_station_comparisons(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot comparative boxplots per station for each sensor."""
    if schema.station_id not in df.columns:
        return

    sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if not sensors:
        return

    units = {"temperature": "°C", "pressure": "hPa", "humidity": "%"}
    fig, axes = plt.subplots(len(sensors), 1, figsize=(10, 3.8 * len(sensors)))
    if len(sensors) == 1:
        axes = [axes]

    for ax, s in zip(axes, sensors):
        unit = units.get(s, "")
        sns.boxplot(data=df, x=schema.station_id, y=s, hue=schema.station_id, ax=ax, palette="Set2", legend=False)
        ax.set_title(f"Station Comparison: {s.capitalize()}")
        ax.set_xlabel("Weather Station")
        ax.set_ylabel(f"{s.capitalize()} ({unit})" if unit else s.capitalize())

    plt.tight_layout()
    fig.savefig(output_dir / "station_sensor_comparisons.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_correlation_heatmap(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot correlation heatmap across core sensor variables."""
    sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if len(sensors) < 2:
        return

    sensor_df = df[sensors].apply(pd.to_numeric, errors="coerce")
    corr = sensor_df.corr(method="pearson")

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        corr,
        annot=True,
        fmt=".3f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=1,
        cbar_kws={"label": "Pearson Correlation Coefficient"},
        ax=ax,
    )
    ax.set_title("Sensor Correlation Matrix")

    plt.tight_layout()
    fig.savefig(output_dir / "correlation_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_sensor_pairplots(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot scatter relationships between sensor pairs."""
    sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if len(sensors) < 2:
        return

    pairs = [
        (schema.temperature, schema.humidity),
        (schema.temperature, schema.pressure),
        (schema.pressure, schema.humidity),
    ]
    pairs = [(s1, s2) for s1, s2 in pairs if s1 in df.columns and s2 in df.columns]
    if not pairs:
        return

    fig, axes = plt.subplots(1, len(pairs), figsize=(5.2 * len(pairs), 4.5))
    if len(pairs) == 1:
        axes = [axes]

    for ax, (s1, s2) in zip(axes, pairs):
        sns.scatterplot(
            data=df,
            x=s1,
            y=s2,
            hue=schema.station_id if schema.station_id in df.columns else None,
            alpha=0.4,
            s=18,
            ax=ax,
        )
        ax.set_title(f"{s1.capitalize()} vs {s2.capitalize()}")
        ax.set_xlabel(s1.capitalize())
        ax.set_ylabel(s2.capitalize())
        if schema.station_id in df.columns:
            ax.legend(fontsize=8, loc="best")

    plt.tight_layout()
    fig.savefig(output_dir / "sensor_pairplots.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_diurnal_patterns(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot 24-hour diurnal pattern profiles."""
    df_work = df.copy()
    if "hour" in df_work.columns:
        hours = pd.to_numeric(df_work["hour"], errors="coerce")
    elif schema.timestamp in df_work.columns:
        dt = pd.to_datetime(df_work[schema.timestamp], errors="coerce")
        hours = dt.dt.hour
    else:
        return

    df_work["_hour"] = hours
    df_work = df_work.dropna(subset=["_hour"])
    df_work["_hour"] = df_work["_hour"].astype(int)

    sensors = [s for s in schema.required_sensor_columns if s in df_work.columns]
    if not sensors:
        return

    units = {"temperature": "°C", "pressure": "hPa", "humidity": "%"}
    fig, axes = plt.subplots(len(sensors), 1, figsize=(10, 3.5 * len(sensors)), sharex=True)
    if len(sensors) == 1:
        axes = [axes]

    for ax, s in zip(axes, sensors):
        unit = units.get(s, "")
        hourly_stats = df_work.groupby("_hour")[s].agg(["mean", "std"]).reset_index()
        ax.plot(hourly_stats["_hour"], hourly_stats["mean"], color="#006699", linewidth=2, label="Hourly Mean")
        ax.fill_between(
            hourly_stats["_hour"],
            hourly_stats["mean"] - hourly_stats["std"],
            hourly_stats["mean"] + hourly_stats["std"],
            color="#006699",
            alpha=0.2,
            label="±1 Std Dev",
        )
        ax.set_title(f"Diurnal (24-Hour) Profile: {s.capitalize()}")
        ax.set_ylabel(f"{s.capitalize()} ({unit})" if unit else s.capitalize())
        ax.set_xticks(range(0, 24, 2))
        ax.legend(loc="best", fontsize=9)

    axes[-1].set_xlabel("Hour of Day (00:00 - 23:00)")
    plt.tight_layout()
    fig.savefig(output_dir / "diurnal_patterns.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_cross_station_deviations(df: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Plot distribution of station deviations from cross-station median."""
    if schema.station_id not in df.columns or schema.timestamp not in df.columns:
        return

    sensors = [s for s in schema.required_sensor_columns if s in df.columns]
    if not sensors:
        return

    dev_records = []
    for s in sensors:
        pivot = df.pivot_table(index=schema.timestamp, columns=schema.station_id, values=s, aggfunc="mean")
        if pivot.shape[1] < 2:
            continue
        group_med = pivot.median(axis=1)
        for stn in pivot.columns:
            dev = pivot[stn] - group_med
            for v in dev.dropna():
                dev_records.append({"station_id": stn, "sensor": s, "deviation": v})

    if not dev_records:
        return

    df_dev = pd.DataFrame(dev_records)
    units = {"temperature": "°C", "pressure": "hPa", "humidity": "%"}

    fig, axes = plt.subplots(len(sensors), 1, figsize=(10, 3.5 * len(sensors)))
    if len(sensors) == 1:
        axes = [axes]

    for ax, s in zip(axes, sensors):
        s_data = df_dev[df_dev["sensor"] == s]
        unit = units.get(s, "")
        sns.boxplot(data=s_data, x="station_id", y="deviation", hue="station_id", ax=ax, palette="pastel", legend=False)
        ax.axhline(0, color="gray", linestyle="--", linewidth=1)
        ax.set_title(f"Cross-Station Deviation from Group Median: {s.capitalize()}")
        ax.set_xlabel("Weather Station")
        ax.set_ylabel(f"Deviation ({unit})" if unit else "Deviation")

    plt.tight_layout()
    fig.savefig(output_dir / "cross_station_deviations.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_all_eda_plots(
    df: pd.DataFrame,
    schema: Optional[SensorSchema] = None,
    output_dir: Optional[Path] = None,
):
    """Generate and save all exploratory data visualization plots."""
    if schema is None:
        schema = SensorSchema()

    if output_dir is None:
        output_dir = Path("reports/eda/plots")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    setup_plot_style()

    plot_sensor_distributions(df, schema, output_dir)
    plot_sensor_boxplots(df, schema, output_dir)
    plot_timeseries_overview(df, schema, output_dir)
    plot_sampling_intervals(df, schema, output_dir)
    plot_station_comparisons(df, schema, output_dir)
    plot_correlation_heatmap(df, schema, output_dir)
    plot_sensor_pairplots(df, schema, output_dir)
    plot_diurnal_patterns(df, schema, output_dir)
    plot_cross_station_deviations(df, schema, output_dir)

    print(f"Generated and saved all EDA plots to: {output_dir}")
