#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

# Add project root to path so we can import src
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.data.loader import load_sensor_data
from src.data.schema import SensorSchema
from src.features.pipeline import build_features, save_feature_metadata, generate_feature_summary

def main():
    parser = argparse.ArgumentParser(description="SkyGuard AI Feature Engineering Pipeline")
    parser.add_argument("--input", "-i", type=str, default="data/raw/weather.csv", help="Path to input raw data CSV")
    parser.add_argument("--output", "-o", type=str, default="data/processed/features.csv", help="Path to output processed features CSV")
    parser.add_argument("--meta", "-m", type=str, default="reports/features/feature_metadata.json", help="Path to output metadata JSON")
    parser.add_argument("--summary", "-s", type=str, default="reports/features/feature_summary.csv", help="Path to output feature summary CSV")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist.")
        print("Note: If you don't have the real dataset yet, that's expected. Create a small dummy file to test.")
        sys.exit(1)
        
    print(f"Loading raw data from {input_path}...")
    df = load_sensor_data(input_path)
    schema = SensorSchema()
    
    print(f"Loaded {len(df)} rows.")
    print("Building features...")
    
    df_features, metadata = build_features(df, schema)
    
    print(f"Feature engineering complete. Total columns: {len(df_features.columns)} (Added {len(metadata)} new features)")
    
    # Save outputs
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving feature dataset to {output_path}...")
    df_features.to_csv(output_path, index=False)
    
    meta_path = Path(args.meta)
    print(f"Saving metadata to {meta_path}...")
    save_feature_metadata(metadata, meta_path)
    
    summary_path = Path(args.summary)
    print(f"Saving feature summary to {summary_path}...")
    generate_feature_summary(df_features, metadata, summary_path)
    
    print("Pipeline complete!")

if __name__ == "__main__":
    main()
