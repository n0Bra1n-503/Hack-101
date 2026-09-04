#!/usr/bin/env python3
"""SkyGuard AI - Weather-vs-Sensor Decision Engine Runner."""

import argparse
from pathlib import Path
import sys
import pandas as pd
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
from src.statistical.config import StatisticalConfig
from src.statistical.detector import StatisticalBaselineDetector
from src.decision.decision_config import DecisionConfig
from src.decision.decision_engine import DecisionEngine

def evaluate_multi_class(y_true_binary: pd.Series, y_pred_classes: pd.Series) -> dict:
    """Evaluate mapping SENSOR_FAULT to True, GENUINE_WEATHER to False, ignoring UNCERTAIN"""
    # Create mask for definitive decisions
    mask = y_pred_classes != "UNCERTAIN"
    
    y_t = y_true_binary[mask].fillna(False).astype(bool)
    y_p = (y_pred_classes[mask] == "SENSOR_FAULT")
    
    if len(y_t) == 0:
        return {"precision": 0, "recall": 0, "f1": 0, "uncertain_rate": 1.0, "total": len(y_true_binary)}
        
    cm = confusion_matrix(y_t, y_p, labels=[False, True])
    tn, fp, fn, tp = cm.ravel()
    
    precision = precision_score(y_t, y_p, zero_division=0)
    recall = recall_score(y_t, y_p, zero_division=0)
    f1 = f1_score(y_t, y_p, zero_division=0)
    
    uncertain_count = (~mask).sum()
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "uncertain_rate": uncertain_count / len(y_true_binary),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "total": len(y_true_binary)
    }

def run_decision(
    raw_data_dir: str = "data/raw",
    injected_data_path: str = "data/processed/fault_injection/injected_dataset.csv",
    ground_truth_path: str = "data/processed/fault_injection/ground_truth.csv",
    hybrid_evidence_path: str = "data/processed/hybrid_evidence.csv",
    output_dir: str = "reports/decision"
):
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    
    schema = SensorSchema()
    
    print("1. Loading datasets and evidence...")
    df_raw = load_sensor_data(Path(raw_data_dir))
    df_injected = pd.read_csv(injected_data_path)
    df_gt = pd.read_csv(ground_truth_path)
    df_hybrid = pd.read_csv(hybrid_evidence_path)
    
    print("2. Re-generating Statistical Flags for Decision Context...")
    df_eval_feat, _ = build_features(df_injected, schema)
    stat_config = StatisticalConfig()
    detector = StatisticalBaselineDetector(config=stat_config, schema=schema)
    df_stat_eval = detector.fit_transform(df_eval_feat)
    
    print("3. Running Weather-vs-Sensor Decision Engine...")
    config = DecisionConfig()
    engine = DecisionEngine(config=config)
    df_dec = engine.generate_decisions(df_hybrid, df_stat_eval)
    
    # Save results
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    
    # Merge outputs with base identifiers for final output
    df_final = df_injected[[schema.timestamp, schema.station_id]].copy()
    df_final = pd.concat([df_final, df_hybrid, df_dec], axis=1)
    df_final.to_csv("data/processed/decision_results.csv", index=False)
    print("   -> Saved to data/processed/decision_results.csv")
    
    print("4. Evaluating Decisions Against Ground Truth...")
    metrics = evaluate_multi_class(df_gt["fault_present"], df_dec["final_classification"])
    pd.DataFrame([metrics]).to_csv(out_p / "overall_metrics.csv", index=False)
    
    print("\nOverall Classification Performance (Excluding UNCERTAIN):")
    for k in ["precision", "recall", "f1", "uncertain_rate"]:
        print(f"{k}: {metrics[k]:.4f}")
        
    print("\nClass Distribution:")
    print(df_dec["final_classification"].value_counts())
        
    fault_type_metrics = []
    if "fault_type" in df_gt.columns:
        for fault_type in df_gt["fault_type"].unique():
            if fault_type == "NORMAL":
                continue
            mask = (df_gt["fault_type"] == fault_type) | (df_gt["fault_present"] == False)
            df_gt_sub = df_gt[mask]
            df_pred_sub = df_dec["final_classification"][mask]
            
            if len(df_gt_sub[df_gt_sub["fault_present"]]) > 0:
                m = evaluate_multi_class(df_gt_sub["fault_present"], df_pred_sub)
                m["fault_type"] = fault_type
                m["events"] = df_gt_sub["fault_present"].sum()
                fault_type_metrics.append(m)
                
    if fault_type_metrics:
        df_ft = pd.DataFrame(fault_type_metrics)
        df_ft.to_csv(out_p / "fault_type_metrics.csv", index=False)
        print("\nFault Type Performance (Decision Engine):")
        print(df_ft[["fault_type", "events", "tp", "fn", "recall", "uncertain_rate"]])
        
    print("\n5. Extracting Representative Examples...")
    # Find one normal, one dropout, one frozen, one spike
    examples = []
    
    # Normal
    normal_idx = df_gt[~df_gt["fault_present"] & (df_dec["final_classification"] == "GENUINE_WEATHER")].index
    if len(normal_idx) > 0:
        examples.append(("NORMAL", normal_idx[0]))
        
    for ft in ["DROPOUT", "FROZEN", "SPIKE", "MULTIVARIATE_INCONSISTENCY"]:
        idx = df_gt[(df_gt["fault_type"] == ft) & (df_dec["final_classification"] == "SENSOR_FAULT")].index
        if len(idx) > 0:
            examples.append((ft, idx[0]))
            
    with open(out_p / "examples.txt", "w") as f:
        for name, i in examples:
            f.write(f"--- Example: {name} ---\n")
            f.write(f"Trust Score: {df_dec.loc[i, 'trust_score']}\n")
            f.write(f"Classification: {df_dec.loc[i, 'final_classification']}\n")
            f.write(f"Inferred Type: {df_dec.loc[i, 'fault_type_inferred']}\n")
            f.write(f"Reasons: {df_dec.loc[i, 'explanations']}\n\n")
            
    print(f"   -> Examples saved to {out_p / 'examples.txt'}")
    print("\nPipeline completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    run_decision()
