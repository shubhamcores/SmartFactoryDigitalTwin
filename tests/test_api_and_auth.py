"""
Integration Tests for Flask Web Application, REST APIs, and Role-Based Access Control (P_307)
"""

import unittest
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from database import init_db

class TestAPIAndAuth(unittest.TestCase):
    """Integration test suite for authentication flows, session handling, RBAC enforcement, and REST endpoints."""

    @classmethod
    def setUpClass(cls):
        init_db(force_recreate=False)
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False

    def setUp(self):
        self.client = self.app.test_client()

    def test_unauthenticated_redirect_to_login(self):
        """Verify unauthenticated user accessing protected route is redirected to /login."""
        response = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_successful_admin_login(self):
        """Verify administrator can log in and establish an authenticated session."""
        response = self.client.post("/login", data={
            "username": "admin",
            "password": "Admin@12345"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Central Factory Digital Twin", response.data)

    def test_failed_login_invalid_password(self):
        """Verify login failure with incorrect credentials displays error."""
        response = self.client.post("/login", data={
            "username": "admin",
            "password": "WrongPassword123"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    def test_operator_blocked_from_admin_endpoints(self):
        """Verify plant operator is strictly blocked (403/redirect) from accessing administrator routes."""
        # 1. Login as operator
        self.client.post("/login", data={"username": "operator", "password": "Operator@12345"})

        # 2. Attempt to access Admin User Management
        response = self.client.get("/admin/users", follow_redirects=True)
        self.assertIn(b"Access denied: Administrator privileges required", response.data)

        # 3. Attempt to call admin API
        api_res = self.client.post("/api/simulator/stop")
        self.assertEqual(api_res.status_code, 403)
        data = json.loads(api_res.data)
        self.assertIn("Forbidden", data.get("error", ""))

    def test_telemetry_latest_api(self):
        """Verify /api/telemetry/latest returns valid JSON with machine records."""
        # Login first
        self.client.post("/login", data={"username": "operator", "password": "Operator@12345"})
        res = self.client.get("/api/telemetry/latest")
        self.assertEqual(res.status_code, 200)

        data = json.loads(res.data)
        self.assertIn("telemetry", data)
        self.assertIn("simulator_running", data)
        self.assertIsInstance(data["telemetry"], list)

    def test_fault_injection_api(self):
        """Verify fault injection API accepts valid condition and updates simulator state."""
        self.client.post("/login", data={"username": "operator", "password": "Operator@12345"})
        res = self.client.post("/api/simulator/inject_fault", json={
            "machine_id": "Motor_1",
            "condition": "HIGH_VIB",
            "duration_cycles": 8
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("applied to Motor_1", data["message"])

    def test_datasource_mode_switching_api(self):
        """Verify API allows switching between Synthetic Simulator and ESP32 Edge Node."""
        self.client.post("/login", data={"username": "admin", "password": "Admin@12345"})

        # Switch Motor_1 to ESP32 mode
        res = self.client.post("/api/datasource/set_mode", json={
            "machine_id": "Motor_1",
            "mode": "ESP32"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["source_modes"]["Motor_1"], "ESP32")

        # Verify via GET /api/datasource/mode
        get_res = self.client.get("/api/datasource/mode")
        self.assertEqual(get_res.status_code, 200)
        get_data = json.loads(get_res.data)
        self.assertEqual(get_data["source_modes"]["Motor_1"], "ESP32")

        # Switch back to SYNTHETIC
        res_back = self.client.post("/api/datasource/set_mode", json={
            "machine_id": "ALL",
            "mode": "SYNTHETIC"
        })
        self.assertEqual(res_back.status_code, 200)

    def test_esp32_telemetry_ingestion_api(self):
        """Verify ESP32 hardware endpoint ingests, validates, and tags data_source as ESP32_EDGE."""
        sample_esp32 = {
            "message_id": "ESP32-UNIT-TEST-999",
            "machine_id": "Motor_1",
            "temperature": 74.2,
            "vibration": 2.85,
            "speed": 1740.0,
            "load": 68.0,
            "status": "RUNNING",
            "production_count": 300
        }
        res = self.client.post("/api/esp32/telemetry", json=sample_esp32)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["telemetry"]["data_source"], "ESP32_EDGE")
        self.assertEqual(data["telemetry"]["machine_id"], "Motor_1")

if __name__ == "__main__":
    unittest.main()
