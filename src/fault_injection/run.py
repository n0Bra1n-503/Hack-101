#!/usr/bin/env python3
"""SkyGuard AI - Fault Injection Pipeline Runner."""

import argparse
from pathlib import Path
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Ensure repository root is on sys.path
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.data.loader import load_sensor_data
from src.data.schema import SensorSchema
from src.fault_injection import FaultConfig, FaultInjector

def plot_faults(df_original: pd.DataFrame, df_injected: pd.DataFrame, df_gt: pd.DataFrame, metadata: pd.DataFrame, schema: SensorSchema, output_dir: Path):
    """Generate representative validation plots for injected faults."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if metadata.empty:
        print("No faults injected, skipping plots.")
        return
        
    # Group by fault type to plot one example of each
    for fault_type, group in metadata.groupby("fault_type"):
        # Select first event of this type
        event = group.iloc[0]
        sensor = event["sensor"]
        
        # Define plotting window (e.g., 50 points before and after)
        start_idx = max(0, int(event["start_idx"]) - 50)
        end_idx = min(len(df_original), int(event["end_idx"]) + 50)
        
        window_orig = df_original.iloc[start_idx:end_idx]
        window_inj = df_injected.iloc[start_idx:end_idx]
        
        x_axis = window_orig.index.values
        if schema.timestamp in window_orig.columns:
            try:
                x_axis = pd.to_datetime(window_orig[schema.timestamp]).values
            except:
                pass
                
        plt.figure(figsize=(10, 4))
        plt.plot(x_axis, window_orig[sensor].values, label="Original", color="blue", alpha=0.5, linestyle="--")
        plt.plot(x_axis, window_inj[sensor].values, label="Injected", color="red", alpha=0.8)
        
        # Highlight the exact fault window
        fault_start_x = x_axis[int(event["start_idx"]) - start_idx]
        fault_end_x = x_axis[min(int(event["end_idx"]) - start_idx - 1, len(x_axis)-1)]
        plt.axvspan(fault_start_x, fault_end_x, color="red", alpha=0.1, label="Fault Region")
        
        plt.title(f"Example: {fault_type} on {sensor.capitalize()}")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / f"example_{fault_type.lower()}.png", dpi=200)
        plt.close()

def generate_summary(metadata: pd.DataFrame, total_obs: int, output_path: Path):
    """Generate a summary report of injected faults."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("==================================================\n")
        f.write(" SKYGUARD AI - FAULT INJECTION SUMMARY\n")
        f.write("==================================================\n\n")
        
        f.write(f"Total Observations: {total_obs:,}\n")
        
        if metadata.empty:
            f.write("No faults injected.\n")
            return
            
        f.write(f"Total Fault Events: {len(metadata):,}\n\n")
        
        f.write("--- By Fault Type ---\n")
        for k, v in metadata["fault_type"].value_counts().items():
            f.write(f"{k}: {v}\n")
            
        f.write("\n--- By Affected Sensor ---\n")
        for k, v in metadata["sensor"].value_counts().items():
            f.write(f"{k}: {v}\n")
            
        # Calculate affected observations
        affected_obs = (metadata["end_idx"] - metadata["start_idx"]).sum()
        pct_affected = (affected_obs / total_obs) * 100
        
        f.write(f"\nTotal Observations Affected: {affected_obs:,} ({pct_affected:.2f}%)\n")

def run_fault_injection(
    input_path: str = "data/raw/weather.csv",
    output_dir: str = "data/processed/fault_injection",
    reports_dir: str = "reports/fault_injection",
    seed: int = 42
):
    """Run fault injection pipeline."""
    in_p = Path(input_path)
    if not in_p.exists():
        # Fallback to data/raw directory directly
        in_p = Path("data/raw")
        if not in_p.exists():
             raise FileNotFoundError(f"Input path {input_path} not found.")
             
    print(f"Loading reference dataset from: {in_p}")
    df_original = load_sensor_data(in_p)
    schema = SensorSchema()
    
    # Sort just to be safe
    if schema.timestamp in df_original.columns:
        df_original["_dt"] = pd.to_datetime(df_original[schema.timestamp], errors="coerce")
        sort_keys = [c for c in [schema.station_id, "_dt"] if c in df_original.columns]
        df_original = df_original.sort_values(by=sort_keys).reset_index(drop=True)
        df_original = df_original.drop(columns=["_dt"])
        
    print(f"Loaded {len(df_original):,} observations.")
    
    config = FaultConfig(random_seed=seed)
    injector = FaultInjector(config=config, schema=schema)
    
    print("Injecting faults...")
    df_injected, df_gt = injector.inject(df_original)
    metadata = injector.get_metadata()
    
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    inj_path = out_dir / "injected_dataset.csv"
    gt_path = out_dir / "ground_truth.csv"
    meta_path = out_dir / "fault_metadata.csv"
    
    print(f"Saving injected dataset to: {inj_path}")
    df_injected.to_csv(inj_path, index=False)
    
    print(f"Saving ground truth to: {gt_path}")
    df_gt.to_csv(gt_path, index=False)
    
    print(f"Saving metadata to: {meta_path}")
    if not metadata.empty:
        metadata.to_csv(meta_path, index=False)
        
    rep_dir = Path(reports_dir)
    sum_path = rep_dir / "summary.txt"
    plots_dir = rep_dir / "plots"
    
    print("Generating summary report...")
    generate_summary(metadata, len(df_original), sum_path)
    
    print("Generating validation plots...")
    plot_faults(df_original, df_injected, df_gt, metadata, schema, plots_dir)
    
    print("Fault injection pipeline completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="SkyGuard AI Fault Injection Engine")
    parser.add_argument("--input", "-i", type=str, default="data/raw", help="Input raw dataset path")
    parser.add_argument("--output", "-o", type=str, default="data/processed/fault_injection", help="Output directory")
    parser.add_argument("--reports", "-r", type=str, default="reports/fault_injection", help="Reports output directory")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    run_fault_injection(
        input_path=args.input,
        output_dir=args.output,
        reports_dir=args.reports,
        seed=args.seed
    )

if __name__ == "__main__":
    main()
