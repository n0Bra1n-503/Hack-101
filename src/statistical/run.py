#!/usr/bin/env python3
"""SkyGuard AI - Statistical Anomaly Baseline Pipeline Runner."""

import argparse
from pathlib import Path
import sys

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.data.loader import load_sensor_data
from src.data.schema import SensorSchema
from src.features.pipeline import build_features
from src.statistical.config import StatisticalConfig
from src.statistical.detector import StatisticalBaselineDetector
from src.statistical.summary import generate_statistical_summary
from src.statistical.plots import generate_baseline_plots


def run_statistical_baseline(
    input_path: str = "data/processed/features.csv",
    config_path: str = "config/anomaly_thresholds.yaml",
    output_path: str = "reports/statistical_baseline/statistical_results.csv",
    summary_path: str = "reports/statistical_baseline/summary.csv",
    plots_dir: str = "reports/statistical_baseline/plots",
) -> None:
    """Run full statistical anomaly detection pipeline, save outputs and generate summaries."""
    in_p = Path(input_path)
    schema = SensorSchema()

    print("==================================================")
    print(" SKYGUARD AI - STATISTICAL BASELINE PIPELINE")
    print("==================================================")

    if in_p.exists():
        print(f"Loading pre-computed feature dataset from: {in_p}")
        df = load_sensor_data(in_p)
    else:
        print(f"Feature dataset not found at {in_p}. Loading raw data and computing features...")
        raw_p = Path("data/raw")
        if not raw_p.exists():
            raise FileNotFoundError("Neither feature dataset nor raw data directory exists.")
        df_raw = load_sensor_data(raw_p)
        df, _ = build_features(df_raw, schema=schema)
        # Save processed features
        in_p.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(in_p, index=False)
        print(f"Saved computed features to: {in_p}")

    print(f"Total observations to analyze: {len(df):,}")

    # Load configuration
    cfg_p = Path(config_path)
    if cfg_p.exists():
        print(f"Loading configuration from: {cfg_p}")
        config = StatisticalConfig.from_yaml(cfg_p)
    else:
        print("Using default statistical baseline configuration.")
        config = StatisticalConfig()

    print(f"Thresholds: Z={config.zscore_threshold}, Robust={config.robust_threshold}, Rolling={config.rolling_z_threshold}")

    # Run Detector
    print("Executing statistical anomaly baseline detector...")
    detector = StatisticalBaselineDetector(config=config, schema=schema)
    df_results = detector.fit_transform(df)

    # Save Results
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(out_p, index=False)
    print(f"Detailed results saved to: {out_p} ({len(df_results):,} rows, {len(df_results.columns)} columns)")

    # Summary
    sum_p = Path(summary_path)
    sum_p.parent.mkdir(parents=True, exist_ok=True)
    df_summary = generate_statistical_summary(df_results, schema=schema, output_path=sum_p)
    print(f"Summary report saved to: {sum_p}")

    # Visual Validation Plots
    pl_dir = Path(plots_dir)
    print(f"Generating visual validation plots in: {pl_dir}...")
    generate_baseline_plots(df_results, output_dir=pl_dir, schema=schema)
    print("Plots generated successfully.")

    # Print summary metrics to console
    print("\n---------------- SUMMARY METRICS ----------------")
    for _, row in df_summary.iterrows():
        print(f"  {row['metric']:<35}: {row['value']}")
    print("-------------------------------------------------\n")
    print("Statistical baseline execution completed successfully!")


def main():
    parser = argparse.ArgumentParser(description="SkyGuard AI Statistical Baseline Pipeline")
    parser.add_argument("--input", "-i", type=str, default="data/processed/features.csv", help="Input feature CSV path")
    parser.add_argument("--config", "-c", type=str, default="config/anomaly_thresholds.yaml", help="Threshold config YAML path")
    parser.add_argument("--output", "-o", type=str, default="reports/statistical_baseline/statistical_results.csv", help="Output results CSV path")
    parser.add_argument("--summary", "-s", type=str, default="reports/statistical_baseline/summary.csv", help="Summary CSV path")
    parser.add_argument("--plots", "-p", type=str, default="reports/statistical_baseline/plots", help="Plots directory")

    args = parser.parse_args()
    run_statistical_baseline(
        input_path=args.input,
        config_path=args.config,
        output_path=args.output,
        summary_path=args.summary,
        plots_dir=args.plots,
    )


if __name__ == "__main__":
    main()
