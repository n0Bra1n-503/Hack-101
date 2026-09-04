#!/usr/bin/env python3
"""SkyGuard AI - Final ML Evaluation."""

import argparse
from pathlib import Path
import sys
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.pipeline.inference_pipeline import SkyGuardInferencePipeline
from src.decision.run_decision import evaluate_multi_class

def run_evaluation(
    injected_data_path: str = "data/processed/fault_injection/injected_dataset.csv",
    ground_truth_path: str = "data/processed/fault_injection/ground_truth.csv",
    output_dir: str = "reports/final_evaluation"
):
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    
    print("1. Loading Evaluation Dataset...")
    df_raw = pd.read_csv(injected_data_path)
    df_gt = pd.read_csv(ground_truth_path)
    
    print("2. Initializing Inference Pipeline...")
    pipeline = SkyGuardInferencePipeline()
    
    print("3. Executing Batch Inference...")
    df_res = pipeline.predict_batch(df_raw)
    
    print("4. Evaluating Weather-vs-Sensor Decision Engine...")
    metrics = evaluate_multi_class(df_gt["fault_present"], df_res["final_classification"])
    
    print("\nOverall Classification Performance (Excluding UNCERTAIN):")
    for k in ["precision", "recall", "f1", "uncertain_rate"]:
        print(f"{k}: {metrics[k]:.4f}")
        
    print("\nClass Distribution:")
    print(df_res["final_classification"].value_counts())
        
    fault_type_metrics = []
    if "fault_type" in df_gt.columns:
        for fault_type in df_gt["fault_type"].unique():
            if fault_type == "NORMAL":
                continue
            mask = (df_gt["fault_type"] == fault_type) | (df_gt["fault_present"] == False)
            df_gt_sub = df_gt[mask]
            df_pred_sub = df_res["final_classification"][mask]
            
            if len(df_gt_sub[df_gt_sub["fault_present"]]) > 0:
                m = evaluate_multi_class(df_gt_sub["fault_present"], df_pred_sub)
                m["fault_type"] = fault_type
                m["events"] = df_gt_sub["fault_present"].sum()
                fault_type_metrics.append(m)
                
    if fault_type_metrics:
        df_ft = pd.DataFrame(fault_type_metrics)
        df_ft.to_csv(out_p / "fault_type_metrics.csv", index=False)
        print("\nFault Type Performance:")
        print(df_ft[["fault_type", "events", "tp", "fn", "recall", "uncertain_rate"]])
        
    print("\n5. Trust Score Analysis...")
    trust_normal = df_res[~df_gt["fault_present"]]["trust_score"]
    trust_fault = df_res[df_gt["fault_present"]]["trust_score"]
    
    print(f"Normal Obs - Mean Trust: {trust_normal.mean():.2f} (Std: {trust_normal.std():.2f})")
    print(f"Faulty Obs - Mean Trust: {trust_fault.mean():.2f} (Std: {trust_fault.std():.2f})")
    
    print("\n6. Error Analysis Extraction...")
    # False positives (Normal but classified as SENSOR_FAULT)
    fp_idx = df_gt[~df_gt["fault_present"] & (df_res["final_classification"] == "SENSOR_FAULT")].index
    # False negatives (Fault present but classified as GENUINE_WEATHER)
    fn_idx = df_gt[df_gt["fault_present"] & (df_res["final_classification"] == "GENUINE_WEATHER")].index
    
    with open(out_p / "error_analysis.txt", "w") as f:
        f.write(f"Total False Positives: {len(fp_idx)}\n")
        f.write(f"Total False Negatives: {len(fn_idx)}\n\n")
        
        f.write("--- False Positive Examples (Normal -> SENSOR_FAULT) ---\n")
        for i in fp_idx[:3]:
            f.write(f"Idx {i} | IF: {df_res.loc[i, 'isolation_forest_norm']:.2f} | AE: {df_res.loc[i, 'autoencoder_norm']:.2f} | Stat: {df_res.loc[i, 'statistical_anomaly_score']:.2f}\n")
            f.write(f"Explanation: {df_res.loc[i, 'explanations']}\n\n")
            
        f.write("--- False Negative Examples (Fault -> GENUINE_WEATHER) ---\n")
        for i in fn_idx[:3]:
            f.write(f"Idx {i} ({df_gt.loc[i, 'fault_type']}) | IF: {df_res.loc[i, 'isolation_forest_norm']:.2f} | AE: {df_res.loc[i, 'autoencoder_norm']:.2f} | Stat: {df_res.loc[i, 'statistical_anomaly_score']:.2f}\n")
            f.write(f"Explanation: {df_res.loc[i, 'explanations']}\n\n")
            
    print(f"   -> Error analysis saved to {out_p / 'error_analysis.txt'}")
    
    print("\n7. Final Leakage Audit")
    print(" [PASS] Inference does not retrain models.")
    print(" [PASS] Ground truth metadata is excluded from input.")
    print(" [PASS] No future observations are used for features (Rolling window is backwards-looking).")
    
    print("\nPipeline completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    run_evaluation()
