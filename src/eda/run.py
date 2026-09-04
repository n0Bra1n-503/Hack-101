import argparse
from pathlib import Path
import sys
import pandas as pd

from src.data import load_sensor_data, load_merged_sensor_data, SensorSchema, validate_sensor_columns
from src.eda.quality import analyze_data_quality
from src.eda.statistics import calculate_sensor_statistics, calculate_station_statistics
from src.eda.temporal import analyze_sampling_intervals, analyze_temporal_patterns
from src.eda.station import analyze_stations, analyze_cross_station
from src.eda.correlations import analyze_correlations
from src.eda.suspicious import identify_potentially_suspicious
from src.eda.plots import generate_all_eda_plots


def run_eda(
    data_path: Path = Path("data/raw"),
    reports_dir: Path = Path("reports/eda"),
    plots_dir: Path = Path("reports/eda/plots"),
    schema: SensorSchema = None,
):
    """Execute the full Step 2 Exploratory Data Analysis and Quality suite."""
    if schema is None:
        schema = SensorSchema()

    reports_dir = Path(reports_dir)
    plots_dir = Path(plots_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SKYGUARD AI - STEP 2: EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 60)

    # 1. Load Data
    print(f"\n[1/8] Loading dataset from: {data_path}")
    data_path = Path(data_path)
    if not data_path.exists():
        print(f"Error: Dataset path does not exist: {data_path}", file=sys.stderr)
        sys.exit(1)

    df = load_sensor_data(data_path)
    print(f"Loaded DataFrame: {df.shape[0]} rows × {df.shape[1]} columns")

    # 2. Validate Schema Columns
    print("\n[2/8] Validating logical sensor schema...")
    is_valid, missing_cols = validate_sensor_columns(df, schema)
    if not is_valid:
        print(f"Warning: Missing required sensor columns: {missing_cols}", file=sys.stderr)
    else:
        print(f"Required sensor columns verified: {schema.required_sensor_columns}")

    # 3. Data Quality Analysis
    print("\n[3/8] Running Data Quality checks...")
    df_quality = analyze_data_quality(df, schema, output_path=reports_dir / "data_quality.csv")
    print(f"Saved: {reports_dir / 'data_quality.csv'}")

    # 4. Sensor & Station Statistics
    print("\n[4/8] Calculating sensor and station statistics...")
    df_sensor_stats = calculate_sensor_statistics(df, schema, output_path=reports_dir / "sensor_statistics.csv")
    print(f"Saved: {reports_dir / 'sensor_statistics.csv'}")

    df_stn_stats = calculate_station_statistics(df, schema, output_path=reports_dir / "station_statistics.csv")
    if not df_stn_stats.empty:
        print(f"Saved: {reports_dir / 'station_statistics.csv'}")

    # 5. Timestamp & Temporal Patterns
    print("\n[5/8] Analyzing sampling intervals and diurnal patterns...")
    df_sampling = analyze_sampling_intervals(df, schema, output_path=reports_dir / "sampling_statistics.csv")
    print(f"Saved: {reports_dir / 'sampling_statistics.csv'}")

    df_temporal = analyze_temporal_patterns(df, schema, output_path=reports_dir / "temporal_patterns.csv")
    print(f"Saved: {reports_dir / 'temporal_patterns.csv'}")

    # 6. Station & Cross-Station Dynamics
    print("\n[6/8] Analyzing station coverage and cross-station consistency...")
    df_stations = analyze_stations(df, schema, output_path=reports_dir / "station_coverage.csv")
    if not df_stations.empty:
        print(f"Saved: {reports_dir / 'station_coverage.csv'}")

    df_cross = analyze_cross_station(df, schema, output_path=reports_dir / "cross_station_summary.csv")
    if not df_cross.empty:
        print(f"Saved: {reports_dir / 'cross_station_summary.csv'}")

    # 7. Correlation Analysis & Suspicious Checks
    print("\n[7/8] Analyzing sensor correlations and exploratory suspicious flags...")
    df_corr = analyze_correlations(df, schema, output_path=reports_dir / "correlation_matrix.csv")
    print(f"Saved: {reports_dir / 'correlation_matrix.csv'}")

    df_suspicious = identify_potentially_suspicious(df, schema, output_path=reports_dir / "potentially_suspicious.csv")
    print(f"Saved: {reports_dir / 'potentially_suspicious.csv'} ({len(df_suspicious)} observations flagged)")

    # 8. Visualizations
    print("\n[8/8] Generating publication-grade EDA visualization suite...")
    generate_all_eda_plots(df, schema, output_dir=plots_dir)

    # Console Summary
    print("\n" + "=" * 60)
    print("EDA SUMMARY HIGHLIGHTS")
    print("=" * 60)
    print(f"Total Observations:    {df.shape[0]}")
    print(f"Total Features:        {df.shape[1]} ({', '.join(df.columns.tolist())})")
    if schema.station_id in df.columns:
        unique_stns = df[schema.station_id].unique().tolist()
        print(f"Active AWS Stations:   {len(unique_stns)} ({', '.join(str(s) for s in unique_stns)})")
    if schema.timestamp in df.columns:
        print(f"Observation Period:    {df[schema.timestamp].min()} to {df[schema.timestamp].max()}")

    if not df_sampling.empty:
        overall_sampling = df_sampling[df_sampling["scope"] == "OVERALL"]
        if not overall_sampling.empty:
            med_int = overall_sampling.iloc[0]["median_interval_minutes"]
            gaps = overall_sampling.iloc[0]["large_gaps_count"]
            print(f"Median Sampling Rate:  {med_int} minutes (Gaps detected: {gaps})")

    print("\nSensor Averages & Ranges:")
    for _, row in df_sensor_stats.iterrows():
        s_name = row["sensor"]
        print(f"  - {s_name.capitalize():<12}: Mean={row['mean']:.2f}, Median={row['median']:.2f}, Range=[{row['min']:.2f}, {row['max']:.2f}], Std={row['std']:.2f}")

    print("\nPairwise Pearson Correlations:")
    print(df_corr.to_string())

    print("\nExploratory Suspicious Flags:")
    if not df_suspicious.empty:
        reason_counts = df_suspicious["reason"].value_counts().to_dict()
        for r, cnt in reason_counts.items():
            print(f"  - {r}: {cnt} instances")
    else:
        print("  - None flagged under current heuristic thresholds.")

    print("\n" + "=" * 60)
    print("STATUS: STEP 2 COMPLETE - READY FOR STEP 3 (Feature Engineering)")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="SkyGuard AI - Step 2: EDA & Data Quality Pipeline")
    parser.add_argument("--data-path", type=str, default="data/raw", help="Path to raw CSV dataset or directory")
    parser.add_argument("--reports-dir", type=str, default="reports/eda", help="Path to output EDA CSV reports")
    parser.add_argument("--plots-dir", type=str, default="reports/eda/plots", help="Path to output EDA plots")
    args = parser.parse_args()

    run_eda(
        data_path=Path(args.data_path),
        reports_dir=Path(args.reports_dir),
        plots_dir=Path(args.plots_dir),
    )


if __name__ == "__main__":
    main()
