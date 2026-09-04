import pandas as pd
import numpy as np
from typing import Optional
from .decision_config import DecisionConfig

class DecisionEngine:
    def __init__(self, config: Optional[DecisionConfig] = None):
        self.config = config or DecisionConfig()
        
    def generate_decisions(self, df_hybrid: pd.DataFrame, df_stat: pd.DataFrame) -> pd.DataFrame:
        df_out = pd.DataFrame(index=df_hybrid.index)
        
        # Pull available fields
        stat_score = df_hybrid.get("statistical_anomaly_score", pd.Series(0.0, index=df_hybrid.index))
        if_score = df_hybrid.get("isolation_forest_norm", pd.Series(0.0, index=df_hybrid.index))
        ae_score = df_hybrid.get("autoencoder_norm", pd.Series(0.0, index=df_hybrid.index))
        
        # Statistical flags
        is_isolated = df_stat.get("is_isolated_sensor_anomaly", pd.Series(False, index=df_hybrid.index)).astype(float)
        is_concurrent = df_stat.get("is_concurrent_multisensor_anomaly", pd.Series(False, index=df_hybrid.index)).astype(float)
        rolling_dev = df_stat.get("rolling_deviation_high", pd.Series(False, index=df_hybrid.index)).astype(float)
        
        # 1. Compute Genuine Weather Score
        # Coordinated behavior across sensors without extreme ML outliers
        weather_score = (is_concurrent * 0.6) + (rolling_dev * 0.2) + ((1.0 - ae_score) * 0.2)
        weather_score = weather_score.clip(lower=0.0, upper=1.0)
        
        # 2. Compute Sensor Fault Score
        # Strong anomaly signals, isolated events, or explicit override for extreme AE
        base_fault = (is_isolated * 0.3) + (if_score * 0.2) + (ae_score * 0.3) + (stat_score * 0.2)
        
        # Explicit override logic (Autoencoder catches Dropouts nicely)
        ae_override_mask = ae_score >= self.config.ae_override_threshold
        # If AE is very high, push fault score to at least 0.8
        fault_score = np.where(ae_override_mask, np.maximum(base_fault, 0.8), base_fault)
        fault_score = pd.Series(fault_score, index=df_hybrid.index).clip(lower=0.0, upper=1.0)
        
        # 3. Compute Conflict Score
        # e.g., High ML anomaly but concurrent (weather-like), or strong IF but weak AE
        conflict_ml = np.abs(if_score - ae_score)
        conflict_w_vs_f = np.abs(weather_score - fault_score)
        
        # High conflict if weather and fault both high, OR if ML models violently disagree
        conflict_score = (conflict_w_vs_f * 0.5) + (conflict_ml * 0.5)
        # If both weather and fault are low, conflict shouldn't matter as much, it's just NORMAL.
        # But if both are HIGH (e.g. 0.8 vs 0.8, difference is 0), wait!
        # Actually, if both are high, conflict should be HIGH! My equation above is wrong for that.
        conflict_w_vs_f_overlap = (weather_score * fault_score)
        conflict_score = np.maximum(conflict_w_vs_f_overlap, conflict_ml)
        conflict_score = pd.Series(conflict_score, index=df_hybrid.index).clip(lower=0.0, upper=1.0)
        
        # 4. Final Classification
        classification = pd.Series("UNCERTAIN", index=df_hybrid.index)
        
        # If no significant evidence, just classify as GENUINE_WEATHER (Normal)
        is_normal = (fault_score < self.config.sensor_fault_threshold) & (weather_score < self.config.weather_threshold)
        classification[is_normal] = "GENUINE_WEATHER"
        
        # High conflict -> UNCERTAIN
        is_conflicting = conflict_score >= self.config.conflict_threshold
        
        # EXCEPTION: If AE is extremely high (override mask), we TRUST the AE and ignore the ML conflict
        # Because we know IF and Stat will miss Dropouts.
        is_conflicting = is_conflicting & ~ae_override_mask
        
        classification[is_conflicting] = "UNCERTAIN"
        
        # Weather
        is_weather = (weather_score >= self.config.weather_threshold) & (weather_score > fault_score) & ~is_conflicting
        classification[is_weather] = "GENUINE_WEATHER"
        
        # Fault
        is_fault = ((fault_score >= self.config.sensor_fault_threshold) & (fault_score > weather_score) & ~is_conflicting) | ae_override_mask
        classification[is_fault] = "SENSOR_FAULT"
        
        # 5. Fault Type Heuristic Inference
        fault_type = pd.Series("NONE", index=df_hybrid.index)
        
        mask_fault = (classification == "SENSOR_FAULT") | (classification == "UNCERTAIN")
        
        # Heuristics:
        # High AE + Low Stat usually means DROPOUT or FROZEN (since IF/Stat miss them)
        is_dropout_frozen = mask_fault & ae_override_mask & (stat_score < 0.4)
        fault_type[is_dropout_frozen] = "DROPOUT" # Or FROZEN, hard to distinguish without strict variance check
        
        # High Stat/Rolling + Low AE could be spikes
        is_spike = mask_fault & (rolling_dev > 0) & (ae_score < 0.4)
        fault_type[is_spike] = "SPIKE"
        
        # Cross sensor (concurrent) but still considered a fault? MULTIVARIATE
        is_multivariate = mask_fault & (is_concurrent > 0) & (ae_score > 0.5)
        fault_type[is_multivariate] = "MULTIVARIATE_INCONSISTENCY"
        
        # Catchall for remaining faults
        is_unknown = mask_fault & (fault_type == "NONE")
        fault_type[is_unknown] = "UNKNOWN"
        
        # 6. Trust Score
        trust = pd.Series(self.config.base_trust, index=df_hybrid.index)
        trust -= (fault_score * self.config.max_fault_penalty)
        trust -= (conflict_score * self.config.max_conflict_penalty)
        # Bonus for clear weather behavior
        weather_bonus = np.where(weather_score > 0.5, self.config.max_weather_bonus * (weather_score - 0.5)*2, 0)
        trust += weather_bonus
        
        trust = trust.clip(lower=0.0, upper=100.0).round(1)
        
        # 7. Generate Explanations
        explanations = []
        for i in range(len(df_hybrid)):
            reasons = []
            if fault_score.iloc[i] > 0.6:
                if ae_score.iloc[i] > 0.7:
                    reasons.append("Autoencoder reconstruction error is extremely high.")
                if is_isolated.iloc[i]:
                    reasons.append("Only one sensor is exhibiting abnormal behavior.")
                if stat_score.iloc[i] > 0.6:
                    reasons.append("Strong deviation from statistical baseline.")
            elif weather_score.iloc[i] > 0.6:
                reasons.append("Multiple sensors show coordinated, consistent changes.")
            
            if conflict_score.iloc[i] > 0.5:
                reasons.append("Evidence is conflicting (ML models disagree or weather/fault signals overlap).")
                
            if len(reasons) == 0:
                reasons.append("Behavior appears normal and consistent.")
                
            explanations.append("; ".join(reasons))
            
        df_out["sensor_fault_score"] = fault_score
        df_out["genuine_weather_score"] = weather_score
        df_out["evidence_conflict_score"] = conflict_score
        df_out["final_classification"] = classification
        df_out["fault_type_inferred"] = fault_type
        df_out["trust_score"] = trust
        df_out["explanations"] = explanations
        
        return df_out
