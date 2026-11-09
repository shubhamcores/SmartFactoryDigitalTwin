"""
Unit Tests for MQTT Payload Validation and Ingestion Logic 
"""

import unittest
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mqtt.config import validate_telemetry_payload

class TestMQTT(unittest.TestCase):
    """Test suite for MQTT payload validation, schema verification, and error containment."""

    def test_valid_telemetry_payload(self):
        """Verify compliant JSON telemetry string passes validation."""
        valid_json = json.dumps({
            "message_id": "TEST-MQTT-001",
            "machine_id": "Motor",
            "temperature": 68.5,
            "vibration": 1.75,
            "speed": 1740.0,
            "load": 62.0,
            "status": "RUNNING",
            "production_count": 150
        })

        is_valid, parsed, err = validate_telemetry_payload(valid_json)
        self.assertTrue(is_valid)
        self.assertEqual(parsed["machine_id"], "Motor")
        self.assertEqual(parsed["data_source"], "MQTT_LIVE")
        self.assertEqual(err, "")

    def test_malformed_json_syntax(self):
        """Verify broken JSON syntax is rejected cleanly without raising an unhandled exception."""
        broken_json = '{"machine_id": "Motor", "temperature": 65.0'  # Missing closing brace
        is_valid, parsed, err = validate_telemetry_payload(broken_json)
        self.assertFalse(is_valid)
        self.assertIn("Invalid JSON", err)

    def test_missing_required_fields(self):
        """Verify omission of mandatory sensor fields causes validation rejection."""
        incomplete_json = json.dumps({
            "machine_id": "Motor",
            "temperature": 68.0
            # vibration, speed, load missing
        })
        is_valid, parsed, err = validate_telemetry_payload(incomplete_json)
        self.assertFalse(is_valid)
        self.assertIn("Missing mandatory telemetry fields", err)

    def test_out_of_bounds_sensor_readings(self):
        """Verify physical plausibility bounds reject corrupt sensor numbers."""
        insane_temp_json = json.dumps({
            "machine_id": "Motor",
            "temperature": 999.0,  # Physically impossible for factory floor
            "vibration": 1.5,
            "speed": 1750.0,
            "load": 50.0
        })
        is_valid, parsed, err = validate_telemetry_payload(insane_temp_json)
        self.assertFalse(is_valid)
        self.assertIn("outside physical limits", err)

    def test_unknown_machine_id(self):
        """Verify unregistered machine identifier is rejected."""
        unknown_json = json.dumps({
            "machine_id": "FakeMachine_999",
            "temperature": 50.0,
            "vibration": 1.0,
            "speed": 1000.0,
            "load": 50.0
        })
        is_valid, parsed, err = validate_telemetry_payload(unknown_json)
        self.assertFalse(is_valid)
        self.assertIn("Unknown machine identifier", err)

if __name__ == "__main__":
    unittest.main()
