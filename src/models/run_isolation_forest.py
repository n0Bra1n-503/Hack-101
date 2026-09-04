#!/usr/bin/env python3
"""SkyGuard AI - Isolation Forest Pipeline Runner."""

import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_PLOT = True
except ImportError:
    HAS_PLOT = False

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.data.loader import load_sensor_data
from src.data.schema import SensorSchema
from src.features.pipeline import build_features
from src.models import IsolationForestConfig, IsolationForestEngine

def evaluate_predictions(df_pred: pd.DataFrame, df_gt: pd.DataFrame) -> dict:
    """Evaluate Isolation Forest predictions against ground truth labels."""
    y_true = df_gt["fault_present"].fillna(False).astype(bool)
    y_pred = df_pred["anomaly_prediction"].fillna(False).astype(bool)
    
    cm = confusion_matrix(y_true, y_pred, labels=[False, True])
    tn, fp, fn, tp = cm.ravel()
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp
    }

def run_isolation_forest(
    raw_data_dir: str = "data/raw",
    injected_data_path: str = "data/processed/fault_injection/injected_dataset.csv",
    ground_truth_path: str = "data/processed/fault_injection/ground_truth.csv",
    output_dir: str = "reports/isolation_forest",
    model_dir: str = "models/isolation_forest",
    contamination: float = 0.05
):
    """Run Isolation Forest training and evaluation pipeline."""
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    plots_p = out_p / "plots"
    plots_p.mkdir(parents=True, exist_ok=True)
    mod_p = Path(model_dir)
    mod_p.mkdir(parents=True, exist_ok=True)
    
    schema = SensorSchema()
    
    print("1. Loading datasets...")
    df_raw = load_sensor_data(Path(raw_data_dir))
    df_injected = pd.read_csv(injected_data_path)
    df_gt = pd.read_csv(ground_truth_path)
    
    print(f"Loaded {len(df_raw)} raw (training) observations.")
    print(f"Loaded {len(df_injected)} injected (evaluation) observations.")
    
    print("2. Building features for training dataset...")
    df_train, _ = build_features(df_raw, schema)
    
    print("3. Building features for evaluation dataset...")
    df_eval, _ = build_features(df_injected, schema)
    
    print("4. Training Isolation Forest...")
    # Use 95th percentile as threshold (assuming 5% anomalies)
    config = IsolationForestConfig(
        contamination="auto", 
        threshold_percentile=(1.0 - contamination) * 100
    )
    engine = IsolationForestEngine(config=config)
    engine.fit(df_train, schema)
    
    print(f"Model trained with {len(engine.features)} features.")
    
    print("5. Predicting on evaluation dataset...")
    predictions = engine.predict(df_eval)
    
    # Save the model
    engine.save(mod_p / "model.joblib")
    print(f"Model saved to {mod_p / 'model.joblib'}")
    
    # Merge predictions with metadata for detailed evaluation
    df_results = pd.concat([df_eval[[c for c in schema.metadata_columns if c in df_eval.columns]], predictions], axis=1)
    
    print("6. Evaluating against ground truth...")
    overall_metrics = evaluate_predictions(predictions, df_gt)
    
    # Save overall metrics
    pd.DataFrame([overall_metrics]).to_csv(out_p / "overall_metrics.csv", index=False)
    
    # By fault type
    fault_type_metrics = []
    if "fault_type" in df_gt.columns:
        for fault_type in df_gt["fault_type"].unique():
            if fault_type == "NORMAL":
                continue
            
            # Mask for specific fault type (treat all other faults as normal to isolate performance)
            # True if this specific fault is present, False otherwise (including normal and other faults)
            mask = (df_gt["fault_type"] == fault_type) | (df_gt["fault_present"] == False)
            df_gt_sub = df_gt[mask]
            df_pred_sub = predictions[mask]
            
            if len(df_gt_sub[df_gt_sub["fault_present"]]) > 0:
                metrics = evaluate_predictions(df_pred_sub, df_gt_sub)
                metrics["fault_type"] = fault_type
                metrics["events"] = df_gt_sub["fault_present"].sum()
                fault_type_metrics.append(metrics)
                
    if fault_type_metrics:
        df_ft = pd.DataFrame(fault_type_metrics)
        df_ft.to_csv(out_p / "fault_type_metrics.csv", index=False)
        print("\nFault Type Performance:")
        print(df_ft[["fault_type", "events", "tp", "fn", "recall"]])
        
        # Plot fault type performance
        if HAS_PLOT:
            plt.figure(figsize=(10, 6))
            plt.barh(df_ft["fault_type"], df_ft["recall"], color="steelblue")
            plt.xlabel("Recall")
            plt.ylabel("Fault Type")
            plt.title("Isolation Forest Recall by Fault Type")
            plt.tight_layout()
            plt.savefig(plots_p / "fault_type_recall.png")
            plt.close()
        
    if HAS_PLOT:
        # Plot score distribution
        plt.figure(figsize=(10, 5))
        scores_normal = predictions[~df_gt["fault_present"]]["anomaly_score"]
        scores_fault = predictions[df_gt["fault_present"]]["anomaly_score"]
        plt.hist([scores_normal, scores_fault], bins=50, stacked=True, label=["Normal", "Fault"], alpha=0.6)
        plt.axvline(engine.threshold, color="red", linestyle="--", label=f"Threshold ({engine.threshold:.2f})")
        plt.title("Anomaly Score Distribution")
        plt.legend()
        plt.tight_layout()
        plt.savefig(plots_p / "score_distribution.png")
        plt.close()
        
        # Plot Confusion Matrix
        plt.figure(figsize=(6, 5))
        cm = np.array([[overall_metrics["tn"], overall_metrics["fp"]], 
                       [overall_metrics["fn"], overall_metrics["tp"]]])
        im = plt.imshow(cm, interpolation='nearest', cmap="Blues")
        plt.colorbar(im)
        
        # Add text annotations
        for i in range(2):
            for j in range(2):
                plt.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
                
        plt.xticks([0, 1], ["Normal", "Anomaly"])
        plt.yticks([0, 1], ["Normal", "Anomaly"])
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.title("Isolation Forest Confusion Matrix")
        plt.tight_layout()
        plt.savefig(plots_p / "confusion_matrix.png")
        plt.close()

    print("\nOverall Performance:")
    print(f"Precision: {overall_metrics['precision']:.4f}")
    print(f"Recall:    {overall_metrics['recall']:.4f}")
    print(f"F1 Score:  {overall_metrics['f1']:.4f}")
    print(f"FPR:       {overall_metrics['fpr']:.4f}")
    
    print("\nPipeline completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--contamination", type=float, default=0.05, help="Estimated contamination fraction for thresholding")
    args = parser.parse_args()
    
    run_isolation_forest(contamination=args.contamination)
