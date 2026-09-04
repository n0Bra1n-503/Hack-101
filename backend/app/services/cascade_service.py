"""Cascade Simulator Service demonstrating the 3 core illustrative pipeline scenarios.

Scenario A: Faulty Extreme (Spike -> ML Anomaly -> Sensor Fault -> Low Trust -> Correction -> Risk Blocked)
Scenario B: Genuine Extreme (Multi-station Heat -> ML Anomaly -> Genuine Weather -> High Trust -> High Risk -> Citizen Alert)
Scenario C: Uncertain (Ambiguous -> ML Anomaly -> Uncertain -> Moderate Trust -> Manual Review -> No Public Alert)
"""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("skyguard.cascade_service")


class CascadeSimulatorService:
    """Provides illustrative end-to-end pipeline cascade flows."""

    def get_scenario(self, scenario_id: str) -> Dict[str, Any]:
        scenario_key = scenario_id.upper()
        if "A" in scenario_key:
            return self._scenario_a_faulty_extreme()
        elif "B" in scenario_key:
            return self._scenario_b_genuine_extreme()
        elif "C" in scenario_key:
            return self._scenario_c_uncertain()
        else:
            return self._scenario_a_faulty_extreme()

    def _scenario_a_faulty_extreme(self) -> Dict[str, Any]:
        return {
            "id": "scenario-a",
            "anomalyId": "scenario-a",
            "scenario": "SCENARIO_A",
            "title": "Scenario A: Sensor Fault Mitigation (Hardware Spike)",
            "description": "An isolated hardware thermistor failure causes a 55°C spike. The pipeline correctly identifies the sensor fault, blocks false disaster alarms, lowers trust score, and proposes an operational correction.",
            "mode": "illustrative_simulation",
            "illustrative": True,
            "withoutSkyguard": {
                "label": "FALSE HEATWAVE ALERT",
                "description": "Raw 55°C reading propagates directly into downstream forecast rules, triggering widespread citizen panic and unwarranted alerts.",
            },
            "withSkyguard": {
                "label": "NO FALSE ALERT",
                "description": "SkyGuard flags the reading as a sensor fault, blocks automated disaster alarms, lowers trust score, and proposes a peer-corroborated correction.",
            },
            "impactSummary": "One false public disaster alert prevented. Automated field maintenance ticket scheduled.",
            "stages": [
                {
                    "stage": 1,
                    "name": "Telemetry Ingestion",
                    "status": "completed",
                    "data": {
                        "station_id": "PUNE_CENTRAL_AWS",
                        "raw_temperature": 55.0,
                        "raw_pressure": 1009.2,
                        "raw_humidity": 78.0,
                        "timestamp": "2026-09-05T12:00:00Z",
                    },
                },
                {
                    "stage": 2,
                    "name": "ML Anomaly Detection",
                    "status": "completed",
                    "data": {
                        "anomaly": True,
                        "anomaly_score": 0.94,
                        "model": "hybrid",
                        "signals": {
                            "statistical": 0.91,
                            "isolation_forest": 0.96,
                            "autoencoder": 0.95,
                        },
                    },
                },
                {
                    "stage": 3,
                    "name": "Decision Intelligence",
                    "status": "completed",
                    "data": {
                        "decision": "sensor_fault",
                        "fault_type": "temperature_spike",
                        "confidence": 0.94,
                        "evidence": {
                            "cross_station": "3 neighboring stations report 31.0°C (support: 0%)",
                            "temporal": "+24.0°C jump in 1 hour exceeds physical threshold",
                            "cross_sensor": "Inconsistent heat and high humidity",
                        },
                    },
                },
                {
                    "stage": 4,
                    "name": "Trust Scoring",
                    "status": "completed",
                    "data": {
                        "trust_score": 18.0,
                        "rating": "UNTRUSTED",
                        "rationale": "High anomaly confidence with 0% peer station corroboration.",
                    },
                },
                {
                    "stage": 5,
                    "name": "Correction Proposal",
                    "status": "completed",
                    "data": {
                        "parameter": "temperature",
                        "raw_value": 55.0,
                        "suggested_value": 31.2,
                        "status": "pending_operator_approval",
                    },
                },
                {
                    "stage": 6,
                    "name": "Disaster Risk Evaluation",
                    "status": "completed",
                    "data": {
                        "risk_evaluation": "BLOCKED",
                        "risk_level": "NONE",
                        "reason": "False alarm prevented: sensor_fault decision blocked disaster risk assessment.",
                    },
                },
                {
                    "stage": 7,
                    "name": "Citizen Public Safety",
                    "status": "completed",
                    "data": {
                        "public_alert": "SUPPRESSED",
                        "advisory": "Normal regional safety advisory active. Panic avoided.",
                    },
                },
            ],
            "outcome": "FAULT_CONTAINED_SAFELY",
        }

    def _scenario_b_genuine_extreme(self) -> Dict[str, Any]:
        return {
            "id": "scenario-b",
            "anomalyId": "scenario-b",
            "scenario": "SCENARIO_B",
            "title": "Scenario B: Genuine Extreme Weather Event (Heatwave)",
            "description": "Multi-station regional heatwave reaches 44.5°C. Decision Intelligence confirms genuine weather through peer corroboration, assigns high trust, triggers disaster risk, and issues citizen advisories.",
            "mode": "illustrative_simulation",
            "illustrative": True,
            "withoutSkyguard": {
                "label": "DELAYED DISASTER ALERT",
                "description": "Traditional single-threshold systems require slow manual verification before alerting, losing crucial early warning response time.",
            },
            "withSkyguard": {
                "label": "VALIDATED REAL-TIME ADVISORY",
                "description": "Decision Intelligence cross-validates 5 peer stations, confirms authentic heatwave, and deploys high-confidence public safety warnings instantly.",
            },
            "impactSummary": "Timely high-confidence public safety advisory issued across 5 districts with verified peer station consensus.",
            "stages": [
                {
                    "stage": 1,
                    "name": "Telemetry Ingestion",
                    "status": "completed",
                    "data": {
                        "station_id": "AHMEDABAD_AIRPORT",
                        "raw_temperature": 44.5,
                        "raw_pressure": 1002.1,
                        "raw_humidity": 18.0,
                        "timestamp": "2026-09-05T14:00:00Z",
                    },
                },
                {
                    "stage": 2,
                    "name": "ML Anomaly Detection",
                    "status": "completed",
                    "data": {
                        "anomaly": True,
                        "anomaly_score": 0.88,
                        "model": "hybrid",
                        "signals": {
                            "statistical": 0.85,
                            "isolation_forest": 0.89,
                            "autoencoder": 0.90,
                        },
                    },
                },
                {
                    "stage": 3,
                    "name": "Decision Intelligence",
                    "status": "completed",
                    "data": {
                        "decision": "genuine_weather",
                        "fault_type": None,
                        "confidence": 0.92,
                        "evidence": {
                            "cross_station": "5 neighboring stations confirm extreme heat between 43.8°C and 44.8°C (support: 100%)",
                            "temporal": "Gradual diurnal solar heating curve (+1.2°C/hr)",
                            "cross_sensor": "Consistent thermodynamic drop in humidity (18%)",
                        },
                    },
                },
                {
                    "stage": 4,
                    "name": "Trust Scoring",
                    "status": "completed",
                    "data": {
                        "trust_score": 95.0,
                        "rating": "HIGHLY_TRUSTED",
                        "rationale": "High peer consensus confirms authentic extreme meteorological event.",
                    },
                },
                {
                    "stage": 5,
                    "name": "Correction Proposal",
                    "status": "completed",
                    "data": {
                        "action": "NONE",
                        "note": "Raw data is genuine atmospheric reality; no correction applied.",
                    },
                },
                {
                    "stage": 6,
                    "name": "Disaster Risk Assessment",
                    "status": "completed",
                    "data": {
                        "risk_level": "HIGH",
                        "event_type": "extreme_heatwave",
                        "confidence": 0.92,
                    },
                },
                {
                    "stage": 7,
                    "name": "Citizen Public Safety",
                    "status": "completed",
                    "data": {
                        "public_alert": "ACTIVE",
                        "advisory": "Severe Heatwave Warning for Ahmedabad: Avoid outdoor exertion between 11 AM - 4 PM. Stay hydrated.",
                    },
                },
            ],
            "outcome": "PUBLIC_SAFETY_ALERT_DEPLOYED",
        }

    def _scenario_c_uncertain(self) -> Dict[str, Any]:
        return {
            "id": "scenario-c",
            "anomalyId": "scenario-c",
            "scenario": "SCENARIO_C",
            "title": "Scenario C: Uncertain Anomaly Gating (Human Review)",
            "description": "An isolated reading shows unexpected temperature jump but peer network connectivity is sparse. The pipeline gates the event as UNCERTAIN, blocking automatic public alarms and escalating to manual operator review.",
            "mode": "illustrative_simulation",
            "illustrative": True,
            "withoutSkyguard": {
                "label": "UNCHECKED AMBIGUITY",
                "description": "Marginal anomalies in sparse network regions trigger either false alarms or total silence without contextual reasoning.",
            },
            "withSkyguard": {
                "label": "GATED OPERATOR ESCALATION",
                "description": "SkyGuard detects ambiguous evidence, gates automatic broadcast, holds provisional trust, and routes to human operator review.",
            },
            "impactSummary": "Automatic public alert safely gated; escalated to regional meteorologist dashboard for verification.",
            "stages": [
                {
                    "stage": 1,
                    "name": "Telemetry Ingestion",
                    "status": "completed",
                    "data": {
                        "station_id": "REMOTE_OUTPOST_AWS",
                        "raw_temperature": 41.0,
                        "raw_pressure": 1005.0,
                        "raw_humidity": 45.0,
                        "timestamp": "2026-09-05T13:30:00Z",
                    },
                },
                {
                    "stage": 2,
                    "name": "ML Anomaly Detection",
                    "status": "completed",
                    "data": {
                        "anomaly": True,
                        "anomaly_score": 0.72,
                        "model": "hybrid",
                        "signals": {
                            "statistical": 0.70,
                            "isolation_forest": 0.74,
                            "autoencoder": 0.73,
                        },
                    },
                },
                {
                    "stage": 3,
                    "name": "Decision Intelligence",
                    "status": "completed",
                    "data": {
                        "decision": "uncertain",
                        "fault_type": None,
                        "confidence": 0.55,
                        "evidence": {
                            "cross_station": "Insufficient regional peer density within 50km radius",
                            "temporal": "Moderate thermal gradient (+4.5°C/hr)",
                            "cross_sensor": "Plausible but unconfirmed",
                        },
                    },
                },
                {
                    "stage": 4,
                    "name": "Trust Scoring",
                    "status": "completed",
                    "data": {
                        "trust_score": 48.0,
                        "rating": "PROVISIONAL",
                        "rationale": "Ambiguous corroboration; held under review.",
                    },
                },
                {
                    "stage": 5,
                    "name": "Correction Proposal",
                    "status": "completed",
                    "data": {
                        "action": "HELD",
                        "note": "Correction withheld pending human operator confirmation.",
                    },
                },
                {
                    "stage": 6,
                    "name": "Disaster Risk Assessment",
                    "status": "completed",
                    "data": {
                        "risk_evaluation": "GATED",
                        "risk_level": "NONE",
                        "reason": "Uncertain classification blocks automated disaster risk elevation.",
                    },
                },
                {
                    "stage": 7,
                    "name": "Citizen Public Safety",
                    "status": "completed",
                    "data": {
                        "public_alert": "SUPPRESSED",
                        "advisory": "Standard baseline monitoring. Operator investigation in progress.",
                    },
                },
            ],
            "outcome": "ROUTED_TO_OPERATOR_QUEUE",
        }


cascade_service = CascadeSimulatorService()
