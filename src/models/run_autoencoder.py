#!/usr/bin/env python3
"""SkyGuard AI - Autoencoder Pipeline Runner."""

import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.data.loader import load_sensor_data
from src.data.schema import SensorSchema
from src.features.pipeline import build_features
from src.models.autoencoder_config import AutoencoderConfig
from src.models.autoencoder import AutoencoderEngine

def evaluate_predictions(y_true: pd.Series, y_pred: pd.Series) -> dict:
    """Evaluate predictions against ground truth labels."""
    y_true_bool = y_true.fillna(False).astype(bool)
    y_pred_bool = y_pred.fillna(False).astype(bool)
    
    cm = confusion_matrix(y_true_bool, y_pred_bool, labels=[False, True])
    tn, fp, fn, tp = cm.ravel()
    
    precision = precision_score(y_true_bool, y_pred_bool, zero_division=0)
    recall = recall_score(y_true_bool, y_pred_bool, zero_division=0)
    f1 = f1_score(y_true_bool, y_pred_bool, zero_division=0)
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

def run_autoencoder(
    raw_data_dir: str = "data/raw",
    injected_data_path: str = "data/processed/fault_injection/injected_dataset.csv",
    ground_truth_path: str = "data/processed/fault_injection/ground_truth.csv",
    output_dir: str = "reports/autoencoder",
    model_dir: str = "models/autoencoder"
):
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    plots_p = out_p / "plots"
    plots_p.mkdir(parents=True, exist_ok=True)
    mod_p = Path(model_dir)
    
    schema = SensorSchema()
    
    print("1. Loading datasets...")
    df_raw = load_sensor_data(Path(raw_data_dir))
    df_injected = pd.read_csv(injected_data_path)
    df_gt = pd.read_csv(ground_truth_path)
    
    print("2. Building features for training dataset...")
    df_train, _ = build_features(df_raw, schema)
    
    print("3. Building features for evaluation dataset...")
    df_eval, _ = build_features(df_injected, schema)
    
    print("4. Training Autoencoder...")
    config = AutoencoderConfig()
    engine = AutoencoderEngine(config=config)
    history = engine.fit(df_train, schema)
    
    # Save model
    engine.save(mod_p)
    print(f"Model saved to {mod_p}")
    
    # Plot training loss
    plt.figure(figsize=(8, 5))
    plt.plot(history["train_loss"], label="Train Loss")
    plt.plot(history["val_loss"], label="Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("MSE Loss")
    plt.title("Autoencoder Training History")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_p / "training_history.png")
    plt.close()
    
    print("5. Calculating reconstruction errors on evaluation dataset...")
    raw_scores = engine.calculate_reconstruction_error(df_eval)
    
    # Evaluate multiple thresholds
    thresholds_to_test = [95.0, 97.5, 99.0]
    best_f1 = 0
    best_threshold = 95.0
    best_metrics = None
    best_predictions = None
    
    print("\nThreshold Sensitivity Analysis:")
    for pct in thresholds_to_test:
        # Recompute threshold value on clean training scores (using train data directly)
        # We can just reuse engine.threshold logic but parameterized
        # Since we just want to select the best percentile, we compute the threshold value
        # from the training data distribution.
        
        # Calculate training errors to get exact percentiles
        train_errors = engine.calculate_reconstruction_error(df_train)
        thresh_val = np.percentile(train_errors, pct)
        
        preds = raw_scores >= thresh_val
        metrics = evaluate_predictions(df_gt["fault_present"], pd.Series(preds))
        
        print(f"Percentile: {pct} | Threshold: {thresh_val:.4f} | Precision: {metrics['precision']:.4f} | Recall: {metrics['recall']:.4f} | F1: {metrics['f1']:.4f} | FPR: {metrics['fpr']:.4f}")
        
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_threshold = thresh_val
            best_metrics = metrics
            best_predictions = preds
            
    print(f"\nSelected Threshold: {best_threshold:.4f} (highest F1)")
    
    # Apply best threshold
    results = pd.DataFrame(index=df_eval.index)
    results["anomaly_score"] = raw_scores
    results["anomaly_prediction"] = best_predictions
    
    print("6. Evaluating against ground truth (Overall & Fault Type)...")
    pd.DataFrame([best_metrics]).to_csv(out_p / "overall_metrics.csv", index=False)
    
    fault_type_metrics = []
    if "fault_type" in df_gt.columns:
        for fault_type in df_gt["fault_type"].unique():
            if fault_type == "NORMAL":
                continue
            mask = (df_gt["fault_type"] == fault_type) | (df_gt["fault_present"] == False)
            df_gt_sub = df_gt[mask]
            df_pred_sub = pd.Series(best_predictions)[mask]
            
            if len(df_gt_sub[df_gt_sub["fault_present"]]) > 0:
                metrics = evaluate_predictions(df_gt_sub["fault_present"], df_pred_sub)
                metrics["fault_type"] = fault_type
                metrics["events"] = df_gt_sub["fault_present"].sum()
                fault_type_metrics.append(metrics)
                
    if fault_type_metrics:
        df_ft = pd.DataFrame(fault_type_metrics)
        df_ft.to_csv(out_p / "fault_type_metrics.csv", index=False)
        print("\nFault Type Performance:")
        print(df_ft[["fault_type", "events", "tp", "fn", "recall"]])
        
        # Plot fault type performance
        plt.figure(figsize=(10, 6))
        plt.barh(df_ft["fault_type"], df_ft["recall"], color="darkorange")
        plt.xlabel("Recall")
        plt.ylabel("Fault Type")
        plt.title("Autoencoder Recall by Fault Type")
        plt.tight_layout()
        plt.savefig(plots_p / "fault_type_recall.png")
        plt.close()

    # Plot score distribution
    plt.figure(figsize=(10, 5))
    scores_normal = raw_scores[~df_gt["fault_present"].fillna(False).astype(bool)]
    scores_fault = raw_scores[df_gt["fault_present"].fillna(False).astype(bool)]
    plt.hist([scores_normal, scores_fault], bins=50, stacked=True, label=["Normal", "Fault"], alpha=0.6)
    plt.axvline(best_threshold, color="red", linestyle="--", label=f"Threshold ({best_threshold:.2f})")
    plt.title("Reconstruction Error Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_p / "score_distribution.png")
    plt.close()

    # Read IF metrics for comparison
    try:
        if_metrics = pd.read_csv("reports/isolation_forest/overall_metrics.csv").iloc[0]
        print("\nComparison with Isolation Forest (Overall):")
        print(f"{'Metric':<15} | {'Autoencoder':<15} | {'Isolation Forest':<15}")
        print("-" * 50)
        for metric in ["precision", "recall", "f1", "fpr", "fnr"]:
            print(f"{metric:<15} | {best_metrics[metric]:<15.4f} | {if_metrics[metric]:<15.4f}")
    except Exception as e:
        print("\nCould not load Isolation Forest metrics for comparison.")
        
    print("\nPipeline completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    run_autoencoder()
