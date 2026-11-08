"""
Unit Tests for Database Initialization and Schema Integrity (P_307)
"""

import unittest
import sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config
from database import get_db_connection, init_db

class TestDatabase(unittest.TestCase):
    """Test suite for SQLite database schema, constraints, and seeding."""

    @classmethod
    def setUpClass(cls):
        init_db(force_recreate=False)

    def test_tables_exist(self):
        """Verify all mandatory tables exist in SQLite database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row["name"] for row in cursor.fetchall()]
        conn.close()

        expected = [
            "users", "machines", "telemetry", "machine_status_history",
            "anomaly_predictions", "alerts", "maintenance_records",
            "report_events", "audit_logs", "system_settings"
        ]
        for tbl in expected:
            self.assertIn(tbl, tables, f"Expected table '{tbl}' was not found in database schema.")

    def test_default_users_seeded(self):
        """Verify default admin and operator user accounts are seeded."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        users = {r["username"]: r["role"] for r in cursor.fetchall()}
        conn.close()

        self.assertIn("admin", users)
        self.assertEqual(users["admin"], "admin")
        self.assertIn("operator", users)
        self.assertEqual(users["operator"], "operator")

    def test_machines_registered(self):
        """Verify all 4 machines are properly registered."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT machine_id FROM machines")
        machines = [r["machine_id"] for r in cursor.fetchall()]
        conn.close()

        for m_id in ["Motor", "Conveyor", "Pump", "CNC"]:
            self.assertIn(m_id, machines)

    def test_telemetry_insert_and_deduplication(self):
        """Test telemetry insertion and uniqueness of message_id."""
        conn = get_db_connection()
        cursor = conn.cursor()
        test_msg_id = "TEST-MSG-DEDUP-001"

        # Cleanup if previously left
        cursor.execute("DELETE FROM telemetry WHERE message_id = ?", (test_msg_id,))
        conn.commit()

        # First insert
        cursor.execute("""
            INSERT INTO telemetry (
                message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
            ) VALUES (?, 'Motor', '2026-11-01 10:00:00', 65.0, 1.8, 1750.0, 60.0, 'RUNNING', 10, 'SIMULATED')
        """, (test_msg_id,))
        conn.commit()

        # Second insert with same message_id should raise IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            cursor.execute("""
                INSERT INTO telemetry (
                    message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
                ) VALUES (?, 'Motor', '2026-11-01 10:00:00', 65.0, 1.8, 1750.0, 60.0, 'RUNNING', 10, 'SIMULATED')
            """, (test_msg_id,))
            conn.commit()

        # Clean up
        cursor.execute("DELETE FROM telemetry WHERE message_id = ?", (test_msg_id,))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    unittest.main()
