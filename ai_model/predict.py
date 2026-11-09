"""
Anomaly Inference Service for FactoryTwin 
Provides real-time machine telemetry evaluation using:
1. Primary: Scikit-learn Isolation Forest model (Trained Unsupervised Detector)
2. Fallback: Rule-Based Deterministic Boundary Detector (if model not trained)

Explicitly computes:
- is_anomaly (boolean)
- anomaly_score (0.0 to 100.0 normalized risk score)
- risk_category ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')
- detection_method ('ISOLATION_FOREST' or 'RULE_BASED_FALLBACK')
- suggested_action (Actionable engineering maintenance guidance)
"""

import sys
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
from config import Config

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = ["temperature", "vibration", "speed", "load"]

class AnomalyDetector:
    """Inference engine for detecting anomalous factory machine operating patterns."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        # If custom model_path passed, allow a fresh test instance
        if kwargs.get("model_path") or (args and args[0] is not None):
            instance = super(AnomalyDetector, cls).__new__(cls)
            instance._initialized = False
            return instance
        if cls._instance is None:
            cls._instance = super(AnomalyDetector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path=None, scaler_path=None):
        if getattr(self, "_initialized", False) and model_path is None:
            return

        self.model_path = Path(model_path or Config.MODEL_PATH)
        self.scaler_path = Path(scaler_path or Config.SCALER_PATH)
        self.model = None
        self.scaler = None
        self.load_model()
        self._initialized = True

    def load_model(self):
        """Attempt to load trained Isolation Forest model and standard scaler from disk."""
        if self.model_path.exists() and self.scaler_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"Loaded Isolation Forest model from {self.model_path}")
                print(f"[AI] Isolation Forest successfully loaded from {self.model_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load AI model: {e}. Defaulting to rule-based fallback.")
                self.model = None
                self.scaler = None
                return False
        else:
            logger.info("AI model not yet trained. Using deterministic Rule-Based Fallback detector.")
            self.model = None
            self.scaler = None
            return False

    def predict(self, machine_id: str, temperature: float, vibration: float, speed: float, load: float) -> dict:
        """
        Evaluate real-time telemetry reading for anomalous behavior.
        Returns detailed prediction dictionary.
        """
        machine_cfg = Config.MACHINES.get(machine_id, {})
        base_temp = machine_cfg.get("base_temp", 60.0)
        max_temp = machine_cfg.get("max_temp", 85.0)
        base_vib = machine_cfg.get("base_vibration", 1.8)
        max_vib = machine_cfg.get("max_vibration", 4.5)
        base_rpm = machine_cfg.get("base_rpm", 1800.0)
        max_rpm = machine_cfg.get("max_rpm", 2500.0)
        base_load = machine_cfg.get("base_load", 65.0)
        max_load = machine_cfg.get("max_load", 90.0)

        # 1. Primary AI Path: Isolation Forest
        if self.model is not None and self.scaler is not None:
            try:
                features = np.array([[temperature, vibration, speed, load]])
                features_scaled = self.scaler.transform(features)

                # raw_pred: 1 is inlier (normal), -1 is outlier (anomaly)
                raw_pred = self.model.predict(features_scaled)[0]
                raw_decision = self.model.decision_function(features_scaled)[0]

                # Map continuous decision function to 0-100 risk score
                normalized_score = max(0.0, min(100.0, (0.15 - raw_decision) * 220.0))

                # Hybrid Industrial Safety Rule: If physical threshold breached, flag as anomaly
                is_physical_breach = bool(
                    temperature > max_temp or
                    vibration > max_vib or
                    load > max_load or
                    (speed < base_rpm * 0.4 and load > 40.0)
                )

                if is_physical_breach:
                    normalized_score = max(normalized_score, 75.0)

                is_anomaly = bool(raw_pred == -1 or is_physical_breach or normalized_score >= 65.0)
                detection_method = "ISOLATION_FOREST"
            except Exception as e:
                logger.error(f"Inference error in Isolation Forest: {e}. Falling back to rules.")
                return self._rule_based_fallback(machine_id, temperature, vibration, speed, load, machine_cfg)
        else:
            # 2. Rule-Based Fallback Path
            return self._rule_based_fallback(machine_id, temperature, vibration, speed, load, machine_cfg)

        # Map normalized score to risk category
        risk_category = self._get_risk_category(normalized_score)
        suggested_action = self._determine_maintenance_action(
            machine_id, temperature, vibration, speed, load,
            base_temp, max_temp, base_vib, max_vib, base_rpm, max_rpm, base_load, max_load,
            risk_category, is_anomaly
        )

        return {
            "machine_id": machine_id,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(normalized_score), 1),
            "risk_category": risk_category,
            "detection_method": detection_method,
            "suggested_action": suggested_action
        }

    def _rule_based_fallback(self, machine_id: str, temperature: float, vibration: float, speed: float, load: float, cfg: dict) -> dict:
        """Deterministic threshold-based fallback detector when ML model is not available."""
        max_temp = cfg.get("max_temp", 85.0)
        max_vib = cfg.get("max_vibration", 4.5)
        max_rpm = cfg.get("max_rpm", 2500.0)
        max_load = cfg.get("max_load", 90.0)
        base_temp = cfg.get("base_temp", 60.0)
        base_vib = cfg.get("base_vibration", 1.8)
        base_rpm = cfg.get("base_rpm", 1800.0)
        base_load = cfg.get("base_load", 65.0)

        # Calculate deviation ratios
        temp_ratio = max(0.0, (temperature - base_temp) / (max_temp - base_temp + 1e-5))
        vib_ratio = max(0.0, (vibration - base_vib) / (max_vib - base_vib + 1e-5))
        load_ratio = max(0.0, (load - base_load) / (max_load - base_load + 1e-5))
        speed_dev = abs(speed - base_rpm) / (base_rpm + 1e-5)

        composite_ratio = max(temp_ratio, vib_ratio, load_ratio, speed_dev * 1.5)
        normalized_score = min(100.0, composite_ratio * 70.0)

        is_anomaly = bool(
            temperature > max_temp or
            vibration > max_vib or
            load > max_load or
            speed < (base_rpm * 0.4) or
            composite_ratio > 1.0
        )

        risk_category = self._get_risk_category(normalized_score)
        suggested_action = self._determine_maintenance_action(
            machine_id, temperature, vibration, speed, load,
            base_temp, max_temp, base_vib, max_vib, base_rpm, max_rpm, base_load, max_load,
            risk_category, is_anomaly
        )

        return {
            "machine_id": machine_id,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(normalized_score), 1),
            "risk_category": risk_category,
            "detection_method": "RULE_BASED_FALLBACK",
            "suggested_action": suggested_action
        }

    @staticmethod
    def _get_risk_category(score: float) -> str:
        """Categorize 0-100 risk score into standard industrial tiers."""
        if score >= 85.0:
            return "CRITICAL"
        elif score >= 65.0:
            return "HIGH"
        elif score >= 40.0:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _determine_maintenance_action(
        machine_id, temp, vib, rpm, load,
        base_temp, max_temp, base_vib, max_vib, base_rpm, max_rpm, base_load, max_load,
        risk_category, is_anomaly
    ) -> str:
        """Provide specific, actionable industrial maintenance recommendations."""
        actions = []

        if temp > max_temp:
            actions.append(f"Temperature high ({temp}°C > {max_temp}°C): Inspect coolant flow, heat sink fins, and thermal paste.")
        elif temp > (base_temp + (max_temp - base_temp) * 0.8):
            actions.append(f"Elevated thermal gradient ({temp}°C): Verify enclosure ventilation fan operation.")

        if vib > max_vib:
            actions.append(f"Excessive vibration ({vib} mm/s > {max_vib} mm/s): Immediate bearing envelope vibration analysis, check foundation anchor bolts and coupling alignment.")
        elif vib > (base_vib + (max_vib - base_vib) * 0.75):
            actions.append(f"Vibration creep ({vib} mm/s): Schedule dynamic rotor balancing inspection.")

        if load > max_load:
            actions.append(f"Mechanical overload ({load}% > {max_load}%): Inspect conveyor/transmission line for jams, verify motor winding resistance.")

        if rpm < (base_rpm * 0.5) and load > 50.0:
            actions.append(f"Stall condition detected ({rpm} RPM with {load}% load): Check VFD drive frequency output and emergency brake disengagement.")

        if not actions:
            if is_anomaly or risk_category in ("HIGH", "CRITICAL"):
                return f"Multivariate anomaly detected on {machine_id} (Unusual joint sensor pattern). Perform diagnostic sensor scan and audit control loop."
            elif risk_category == "MEDIUM":
                return f"{machine_id} operating under mild statistical drift. Continue monitoring via digital twin."
            else:
                return f"{machine_id} operating within normal certified parameters. Routine preventive schedule active."

        return " | ".join(actions)

# Module-level convenience function
_detector = None

def get_anomaly_detector() -> AnomalyDetector:
    global _detector
    if _detector is None:
        _detector = AnomalyDetector()
    return _detector
