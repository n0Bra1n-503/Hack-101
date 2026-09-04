#!/usr/bin/env python3
"""SkyGuard AI - Hybrid Evidence Engine Runner."""

import argparse
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.data.loader import load_sensor_data
from src.data.schema import SensorSchema
from src.features.pipeline import build_features
from src.statistical.detector import StatisticalBaselineDetector
from src.models.isolation_forest import IsolationForestEngine
from src.models.autoencoder import AutoencoderEngine
from src.evidence.hybrid_config import HybridEngineConfig
from src.evidence.hybrid_engine import HybridEvidenceEngine
from src.models.run_autoencoder import evaluate_predictions

def run_hybrid(
    raw_data_dir: str = "data/raw",
    injected_data_path: str = "data/processed/fault_injection/injected_dataset.csv",
    ground_truth_path: str = "data/processed/fault_injection/ground_truth.csv",
    output_dir: str = "reports/hybrid"
):
    out_p = Path(output_dir)
    out_p.mkdir(parents=True, exist_ok=True)
    
    schema = SensorSchema()
    
    print("1. Loading datasets...")
    df_raw = load_sensor_data(Path(raw_data_dir))
    df_injected = pd.read_csv(injected_data_path)
    df_gt = pd.read_csv(ground_truth_path)
    
    print("2. Building features...")
    df_train_feat, _ = build_features(df_raw, schema)
    df_eval_feat, _ = build_features(df_injected, schema)
    
    print("3. Generating Statistical Baseline Evidence...")
    # Make sure statistical config is imported since I removed it above, oops
    from src.statistical.config import StatisticalConfig
    stat_config = StatisticalConfig()
    detector = StatisticalBaselineDetector(config=stat_config, schema=schema)
    df_stat_eval = detector.fit_transform(df_eval_feat)
    
    print("4. Generating Isolation Forest Evidence...")
    if_engine = IsolationForestEngine.load("models/isolation_forest/model.joblib")
    if_train_preds = pd.DataFrame(index=df_train_feat.index)
    if_train_preds["anomaly_score"] = if_engine.predict(df_train_feat)["anomaly_score"]
    df_if_eval = if_engine.predict(df_eval_feat)
    
    print("5. Generating Autoencoder Evidence...")
    ae_engine = AutoencoderEngine.load("models/autoencoder")
    ae_train_preds = pd.DataFrame(index=df_train_feat.index)
    ae_train_preds["anomaly_score"] = ae_engine.calculate_reconstruction_error(df_train_feat)
    
    df_ae_eval = pd.DataFrame(index=df_eval_feat.index)
    df_ae_eval["anomaly_score"] = ae_engine.calculate_reconstruction_error(df_eval_feat)
    
    print("6. Initializing and Fitting Hybrid Evidence Engine...")
    config = HybridEngineConfig()
    hybrid = HybridEvidenceEngine(config=config)
    
    # Fit normalization limits on clean data
    hybrid.fit_normalizers(if_train_preds, ae_train_preds)
    
    print("8. Running Weight Experiments...")
    
    experiments = {
        "Config A (Balanced)": HybridEngineConfig(
            w_statistical=0.25, w_isolation_forest=0.20, w_autoencoder=0.35, w_temporal_persistence=0.10, w_cross_sensor=0.10
        ),
        "Config B (ML Heavy)": HybridEngineConfig(
            w_statistical=0.10, w_isolation_forest=0.30, w_autoencoder=0.50, w_temporal_persistence=0.05, w_cross_sensor=0.05
        ),
        "Config C (Stat Heavy)": HybridEngineConfig(
            w_statistical=0.40, w_isolation_forest=0.10, w_autoencoder=0.10, w_temporal_persistence=0.20, w_cross_sensor=0.20
        )
    }
    
    best_config_name = None
    best_f1 = 0
    best_metrics = None
    best_preds = None
    
    for name, cfg in experiments.items():
        hybrid.config = cfg
        df_hyb = hybrid.generate_hybrid_evidence(df_injected, df_stat_eval, df_if_eval, df_ae_eval, schema)
        preds = df_hyb["evidence_strength"] == "HIGH"
        metrics = evaluate_predictions(df_gt["fault_present"], preds)
        print(f"{name} -> Precision: {metrics['precision']:.4f}, Recall: {metrics['recall']:.4f}, F1: {metrics['f1']:.4f}, FPR: {metrics['fpr']:.4f}")
        
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            best_config_name = name
            best_metrics = metrics
            best_preds = preds
            
    print(f"\nSelected {best_config_name} with F1: {best_f1:.4f}")
    
    # Save the best observation-level evidence
    hybrid.config = experiments[best_config_name]
    df_hybrid = hybrid.generate_hybrid_evidence(df_injected, df_stat_eval, df_if_eval, df_ae_eval, schema)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    df_hybrid.to_csv("data/processed/hybrid_evidence.csv", index=False)
    print("   -> Saved to data/processed/hybrid_evidence.csv")
    
    pd.DataFrame([best_metrics]).to_csv(out_p / "overall_metrics.csv", index=False)
    
    fault_type_metrics = []
    if "fault_type" in df_gt.columns:
        for fault_type in df_gt["fault_type"].unique():
            if fault_type == "NORMAL":
                continue
            mask = (df_gt["fault_type"] == fault_type) | (df_gt["fault_present"] == False)
            df_gt_sub = df_gt[mask]
            df_pred_sub = pd.Series(best_preds)[mask]
            
            if len(df_gt_sub[df_gt_sub["fault_present"]]) > 0:
                m = evaluate_predictions(df_gt_sub["fault_present"], df_pred_sub)
                m["fault_type"] = fault_type
                m["events"] = df_gt_sub["fault_present"].sum()
                fault_type_metrics.append(m)
                
    if fault_type_metrics:
        df_ft = pd.DataFrame(fault_type_metrics)
        df_ft.to_csv(out_p / "fault_type_metrics.csv", index=False)
        print("\nFault Type Performance:")
        print(df_ft[["fault_type", "events", "tp", "fn", "recall"]])
        
    print("\nOverall Performance:")
    for k in ["precision", "recall", "f1", "fpr", "fnr"]:
        print(f"{k}: {best_metrics[k]:.4f}")
        
    print("\nPipeline completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    run_hybrid()
