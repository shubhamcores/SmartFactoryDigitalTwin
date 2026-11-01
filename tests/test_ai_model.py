"""
Unit Tests for Machine Learning Anomaly Detection (P_307)
"""

import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config
from ai_model.predict import AnomalyDetector, get_anomaly_detector

class TestAIModel(unittest.TestCase):
    """Test suite for Isolation Forest inference and fallback detection."""

    @classmethod
    def setUpClass(cls):
        cls.detector = get_anomaly_detector()

    def test_detector_inference_normal_reading(self):
        """Verify normal telemetry produces low anomaly score and LOW risk category."""
        cfg = Config.MACHINES["Motor_1"]
        pred = self.detector.predict(
            machine_id="Motor_1",
            temperature=cfg["base_temp"],
            vibration=cfg["base_vibration"],
            speed=cfg["base_rpm"],
            load=cfg["base_load"]
        )

        self.assertEqual(pred["machine_id"], "Motor_1")
        self.assertIn(pred["risk_category"], ["LOW", "MEDIUM"])
        self.assertLess(pred["anomaly_score"], 65.0)
        self.assertIn("operating within", pred["suggested_action"].lower())

    def test_detector_inference_severe_overheat(self):
        """Verify severe high temperature triggers anomaly and maintenance action."""
        pred = self.detector.predict(
            machine_id="Motor_1",
            temperature=110.0,  # Max threshold is 85.0
            vibration=1.8,
            speed=1750.0,
            load=65.0
        )

        self.assertTrue(pred["is_anomaly"])
        self.assertIn(pred["risk_category"], ["HIGH", "CRITICAL"])
        self.assertGreaterEqual(pred["anomaly_score"], 65.0)
        self.assertIn("temperature", pred["suggested_action"].lower())

    def test_detector_inference_severe_vibration(self):
        """Verify high vibration triggers bearing analysis guidance."""
        pred = self.detector.predict(
            machine_id="Pump_1",
            temperature=54.0,
            vibration=9.5,  # Max threshold is 5.0
            speed=2900.0,
            load=70.0
        )

        self.assertTrue(pred["is_anomaly"])
        self.assertIn("vibration", pred["suggested_action"].lower())
        self.assertIn("bearing", pred["suggested_action"].lower())

    def test_rule_based_fallback_when_model_missing(self):
        """Verify fallback detector runs correctly when model is simulated missing."""
        mock_detector = AnomalyDetector(model_path="non_existent_model.joblib")
        # Ensure it acts as fallback
        self.assertIsNone(mock_detector.model)

        pred = mock_detector.predict(
            machine_id="Conveyor_1",
            temperature=45.0,
            vibration=1.2,
            speed=450.0,
            load=50.0
        )
        self.assertEqual(pred["detection_method"], "RULE_BASED_FALLBACK")
        self.assertFalse(pred["is_anomaly"])

if __name__ == "__main__":
    unittest.main()
