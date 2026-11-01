"""
Database Layer for FactoryTwin (P_307)
Handles SQLite database connection, initialization, schema migration, and transaction management.
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establish and return a connection to the SQLite database with row factory."""
    Config.ensure_directories()
    conn = sqlite3.connect(
        Config.DATABASE_PATH,
        timeout=20.0,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")  # High concurrency for simulator + web
    return conn

def init_db(force_recreate=False):
    """
    Initialize SQLite database tables, indexes, and initial seed data.
    If force_recreate=True, drops existing tables before re-creating.
    """
    Config.ensure_directories()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if force_recreate:
            cursor.executescript("""
                DROP TABLE IF EXISTS audit_logs;
                DROP TABLE IF EXISTS report_events;
                DROP TABLE IF EXISTS maintenance_records;
                DROP TABLE IF EXISTS alerts;
                DROP TABLE IF EXISTS anomaly_predictions;
                DROP TABLE IF EXISTS machine_status_history;
                DROP TABLE IF EXISTS telemetry;
                DROP TABLE IF EXISTS machines;
                DROP TABLE IF EXISTS users;
                DROP TABLE IF EXISTS system_settings;
            """)

        cursor.executescript("""
            -- Users Table for Role-Based Access Control (RBAC)
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'operator')),
                full_name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            );

            -- Industrial Machines Registry
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                machine_type TEXT NOT NULL,
                location TEXT NOT NULL,
                base_temp REAL NOT NULL,
                base_vibration REAL NOT NULL,
                base_rpm REAL NOT NULL,
                base_load REAL NOT NULL,
                max_temp REAL NOT NULL,
                max_vibration REAL NOT NULL,
                max_rpm REAL NOT NULL,
                max_load REAL NOT NULL,
                production_rate INTEGER DEFAULT 5,
                current_status TEXT DEFAULT 'RUNNING' CHECK(current_status IN ('RUNNING', 'IDLE', 'WARNING', 'STOPPED', 'CRITICAL')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Machine Telemetry Records
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE,
                machine_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                temperature REAL NOT NULL,
                vibration REAL NOT NULL,
                speed REAL NOT NULL,
                load REAL NOT NULL,
                status TEXT NOT NULL,
                production_count INTEGER NOT NULL,
                data_source TEXT NOT NULL CHECK(data_source IN ('SIMULATED', 'MQTT_LIVE', 'ESP32_EDGE')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
            );

            -- Machine Status History Audit
            CREATE TABLE IF NOT EXISTS machine_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT NOT NULL,
                old_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
            );

            -- Anomaly Predictions (Isolation Forest Inference Log)
            CREATE TABLE IF NOT EXISTS anomaly_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telemetry_id INTEGER,
                machine_id TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                anomaly_score REAL NOT NULL,
                is_anomaly INTEGER NOT NULL CHECK(is_anomaly IN (0, 1)),
                risk_category TEXT NOT NULL CHECK(risk_category IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
                detection_method TEXT NOT NULL CHECK(detection_method IN ('ISOLATION_FOREST', 'RULE_BASED_FALLBACK')),
                suggested_action TEXT,
                FOREIGN KEY (telemetry_id) REFERENCES telemetry(id) ON DELETE SET NULL,
                FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
            );

            -- Machine Health and Safety Alerts
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL CHECK(severity IN ('INFO', 'WARNING', 'CRITICAL')),
                message TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'NEW' CHECK(status IN ('NEW', 'ACKNOWLEDGED', 'RESOLVED')),
                acknowledged_by TEXT,
                acknowledged_at TIMESTAMP,
                resolved_by TEXT,
                resolved_at TIMESTAMP,
                action_taken TEXT,
                FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
            );

            -- Maintenance Service Schedules & Logs
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_id TEXT NOT NULL,
                scheduled_date TEXT NOT NULL,
                maintenance_type TEXT NOT NULL,
                description TEXT NOT NULL,
                performed_by TEXT,
                status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK(status IN ('SCHEDULED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (machine_id) REFERENCES machines(machine_id) ON DELETE CASCADE
            );

            -- Generated Reports Event Log
            CREATE TABLE IF NOT EXISTS report_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_type TEXT NOT NULL,
                file_format TEXT NOT NULL,
                generated_by TEXT NOT NULL,
                filters_applied TEXT,
                record_count INTEGER DEFAULT 0,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- System Audit Trails
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                ip_address TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Configurable System Settings Key-Value Store
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- High-Performance Indexes for Query Optimization
            CREATE INDEX IF NOT EXISTS idx_telemetry_machine_time ON telemetry(machine_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_telemetry_msg_id ON telemetry(message_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_machine_status ON alerts(machine_id, status);
            CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_anomaly_machine_time ON anomaly_predictions(machine_id, timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(timestamp DESC);
        """)

        # Seed Default Users
        seed_users(cursor)

        # Seed Configured Machines
        seed_machines(cursor)

        # Seed Default Maintenance Plans
        seed_maintenance_records(cursor)

        conn.commit()
        print(f"[OK] Database successfully initialized at: {Config.DATABASE_PATH}")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Database initialization failed: {e}")
        raise
    finally:
        conn.close()

def seed_users(cursor):
    """Seed initial administrator and operator user accounts."""
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash("Admin@12345")
        op_pass = generate_password_hash("Operator@12345")

        users_to_insert = [
            ("admin", admin_pass, "admin", "System Administrator", "admin@smartfactory.local"),
            ("operator", op_pass, "operator", "Plant Floor Operator", "operator@smartfactory.local")
        ]
        cursor.executemany("""
            INSERT INTO users (username, password_hash, role, full_name, email)
            VALUES (?, ?, ?, ?, ?)
        """, users_to_insert)
        print(" -> Seeded default users: admin, operator")

def seed_machines(cursor):
    """Seed initial industrial machine registry from Config.MACHINES."""
    for machine_id, m in Config.MACHINES.items():
        cursor.execute("SELECT id FROM machines WHERE machine_id = ?", (machine_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO machines (
                    machine_id, name, machine_type, location,
                    base_temp, base_vibration, base_rpm, base_load,
                    max_temp, max_vibration, max_rpm, max_load,
                    production_rate, current_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'RUNNING')
            """, (
                machine_id, m["name"], m["type"], m["location"],
                m["base_temp"], m["base_vibration"], m["base_rpm"], m["base_load"],
                m["max_temp"], m["max_vibration"], m["max_rpm"], m["max_load"],
                m.get("production_rate", 5)
            ))
            print(f" -> Registered machine: {machine_id} ({m['name']})")

def seed_maintenance_records(cursor):
    """Seed initial scheduled maintenance items."""
    cursor.execute("SELECT COUNT(*) FROM maintenance_records")
    if cursor.fetchone()[0] == 0:
        records = [
            ("Motor", "2026-11-15", "Lubrication", "Bearing regreasing and thermal imaging check", "Maintenance Team A"),
            ("Conveyor", "2026-11-20", "Belt Inspection", "Inspect drive belt tension and alignment rollers", "Mechanical Crew"),
            ("Pump", "2026-11-18", "Impeller Cleaning", "Descale centrifugal pump housing and check seals", "Fluid Systems"),
            ("CNC", "2026-11-25", "Spindle Calibration", "Laser interferometer runout check and toolholder cleaning", "Precision Tooling")
        ]
        cursor.executemany("""
            INSERT INTO maintenance_records (machine_id, scheduled_date, maintenance_type, description, performed_by)
            VALUES (?, ?, ?, ?, ?)
        """, records)
        print(" -> Seeded baseline maintenance schedules")

if __name__ == "__main__":
    import sys
    force = "--reset" in sys.argv or "-f" in sys.argv
    print(f"Initializing FactoryTwin Database (reset={force})...")
    init_db(force_recreate=force)
