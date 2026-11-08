"""
Unit Tests for Alerting Rules, Deduplication, and Lifecycle (P_307)
"""

import unittest
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config
from services.alert_service import (
    evaluate_telemetry_for_alerts, acknowledge_alert, resolve_alert,
    get_recent_alerts, _cooldown_tracker
)
from database import get_db_connection, init_db

class TestAlerts(unittest.TestCase):
    """Test suite for alert evaluation, threshold triggers, cooldown deduplication, and RBAC actions."""

    @classmethod
    def setUpClass(cls):
        init_db(force_recreate=False)

    def setUp(self):
        # Clear cooldown tracker before each test
        _cooldown_tracker.clear()

    def test_temperature_threshold_alert_generation(self):
        """Verify high temperature triggers an EXCESSIVE_TEMPERATURE alert."""
        reading = {
            "machine_id": "Motor",
            "temperature": 96.0,  # Max threshold is 85.0
            "vibration": 1.6,
            "speed": 1750.0,
            "load": 65.0,
            "status": "WARNING",
            "production_count": 50
        }

        alerts = evaluate_telemetry_for_alerts(reading)
        self.assertGreaterEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert["machine_id"], "Motor")
        self.assertEqual(alert["alert_type"], "EXCESSIVE_TEMPERATURE")
        self.assertEqual(alert["status"], "NEW")

    def test_alert_cooldown_deduplication(self):
        """Verify repeated violations during cooldown window do not flood the database."""
        reading = {
            "machine_id": "Motor",
            "temperature": 98.0,
            "vibration": 1.6,
            "speed": 1750.0,
            "load": 65.0,
            "status": "WARNING",
            "production_count": 55
        }

        # First call should generate alert
        first_call = evaluate_telemetry_for_alerts(reading)
        self.assertEqual(len(first_call), 1)

        # Immediate second call should be suppressed by cooldown
        second_call = evaluate_telemetry_for_alerts(reading)
        self.assertEqual(len(second_call), 0)

    def test_alert_acknowledgement_and_resolution_lifecycle(self):
        """Verify alert progresses from NEW -> ACKNOWLEDGED -> RESOLVED."""
        reading = {
            "machine_id": "Pump",
            "temperature": 54.0,
            "vibration": 8.0,  # Breaches 5.0
            "speed": 2900.0,
            "load": 70.0,
            "status": "WARNING",
            "production_count": 20
        }
        alerts = evaluate_telemetry_for_alerts(reading)
        self.assertGreaterEqual(len(alerts), 1)
        alert_id = alerts[0]["id"]

        # 1. Acknowledge by Operator
        ack_res = acknowledge_alert(alert_id, "operator_test")
        self.assertTrue(ack_res)

        # Verify DB status
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, acknowledged_by FROM alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        self.assertEqual(row["status"], "ACKNOWLEDGED")
        self.assertEqual(row["acknowledged_by"], "operator_test")

        # 2. Resolve by Admin
        res_res = resolve_alert(alert_id, "admin_test", "Replaced bearing assembly")
        self.assertTrue(res_res)

        cursor.execute("SELECT status, resolved_by, action_taken FROM alerts WHERE id = ?", (alert_id,))
        row = cursor.fetchone()
        self.assertEqual(row["status"], "RESOLVED")
        self.assertEqual(row["resolved_by"], "admin_test")
        self.assertIn("Replaced bearing", row["action_taken"])
        conn.close()

if __name__ == "__main__":
    unittest.main()
