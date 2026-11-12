"""
Configuration Module for FactoryTwin 
AI-Driven Digital Twin for Smart Factory Operations
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class MachineRegistry(dict):
    """Dictionary supporting canonical machine IDs (Motor, Conveyor, Pump, CNC) with backward-compatible aliases."""
    ALIASES = {
        "Motor_1": "Motor",
        "Motor": "Motor",
        "Conveyor_1": "Conveyor",
        "Conveyor": "Conveyor",
        "Pump_1": "Pump",
        "Pump": "Pump",
        "CNC_1": "CNC",
        "CNC": "CNC"
    }

    def __getitem__(self, key):
        return super().__getitem__(self.ALIASES.get(key, key))

    def __contains__(self, key):
        return super().__contains__(self.ALIASES.get(key, key))

    def get(self, key, default=None):
        return super().get(self.ALIASES.get(key, key), default)

class Config:
    """Application configuration parameters and industrial operating limits."""

    # Project Metadata
    PROJECT_NAME = "FactoryTwin"
    PROJECT_TITLE = "AI-Driven Digital Twin for Smart Factory Operations"
    PROJECT_CODE = ""
    VERSION = "1.0.0"

    # Base Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    REPORTS_DIR = BASE_DIR / "reports"
    GENERATED_REPORTS_DIR = BASE_DIR / "reports" / "generated"
    AI_MODEL_DIR = BASE_DIR / "ai_model"
    DOCS_DIR = BASE_DIR / "docs"
    TESTS_DIR = BASE_DIR / "tests"

    # Security & Sessions
    SECRET_KEY = os.getenv("SECRET_KEY", "factorytwin-dev-secret-key-307-2026")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = int(os.getenv("PERMANENT_SESSION_LIFETIME", 7200)) # 2 hours

    # Database
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "factory_twin.db")

    # Data Source Modes: 'SYNTHETIC' (Internal Simulator) or 'ESP32' (Hardware Edge Node)
    DEFAULT_DATA_SOURCE_MODE = os.getenv("DATA_SOURCE_MODE", "SYNTHETIC").upper()

    # Simulator Settings
    SIMULATION_ENABLED = os.getenv("SIMULATION_ENABLED", "True").lower() in ("true", "1", "yes")
    SIMULATION_INTERVAL = float(os.getenv("SIMULATION_INTERVAL_SECONDS", 3.0))

    # MQTT Settings
    MQTT_ENABLED = os.getenv("MQTT_ENABLED", "False").lower() in ("true", "1", "yes")
    MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
    MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "False").lower() in ("true", "1", "yes")
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    MQTT_TOPIC_PREFIX = os.getenv("MQTT_TOPIC_PREFIX", "factory/machines")
    MQTT_CLIENT_ID_PREFIX = os.getenv("MQTT_CLIENT_ID_PREFIX", "FactoryTwin")

    # Machine Learning Settings
    MODEL_PATH = BASE_DIR / os.getenv("MODEL_PATH", "ai_model/isolation_forest_model.joblib")
    SCALER_PATH = BASE_DIR / os.getenv("SCALER_PATH", "ai_model/scaler.joblib")
    METRICS_PATH = BASE_DIR / "ai_model" / "model_metrics.json"
    ANOMALY_CONTAMINATION = float(os.getenv("ANOMALY_CONTAMINATION", 0.05))

    # Alert Cooldown (seconds between repeated alerts for the same condition on a machine)
    ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", 60))

    # Supported Industrial Machines & Default Profiles
    MACHINES = MachineRegistry({
        "Motor": {
            "name": "Main Drive Induction Motor",
            "type": "Electric Motor",
            "location": "Bay A - Primary Drive Section",
            "base_temp": 62.0,
            "base_vibration": 1.6,
            "base_rpm": 1750.0,
            "base_load": 65.0,
            "max_temp": 85.0,
            "max_vibration": 4.5,
            "max_rpm": 2200.0,
            "max_load": 90.0,
            "production_rate": 5 # units per cycle
        },
        "Conveyor": {
            "name": "Material Transfer Conveyor",
            "type": "Belt Conveyor",
            "location": "Bay B - Logistics Transfer",
            "base_temp": 42.0,
            "base_vibration": 1.1,
            "base_rpm": 450.0,
            "base_load": 50.0,
            "max_temp": 70.0,
            "max_vibration": 3.8,
            "max_rpm": 600.0,
            "max_load": 85.0,
            "production_rate": 12
        },
        "Pump": {
            "name": "Cooling Circuit Centrifugal Pump",
            "type": "Hydraulic Pump",
            "location": "Bay C - Coolant Substation",
            "base_temp": 54.0,
            "base_vibration": 2.0,
            "base_rpm": 2900.0,
            "base_load": 70.0,
            "max_temp": 80.0,
            "max_vibration": 5.0,
            "max_rpm": 3400.0,
            "max_load": 92.0,
            "production_rate": 8
        },
        "CNC": {
            "name": "5-Axis Precision Milling Center",
            "type": "CNC Mill",
            "location": "Bay D - Machining Cell 1",
            "base_temp": 68.0,
            "base_vibration": 2.3,
            "base_rpm": 2400.0,
            "base_load": 75.0,
            "max_temp": 90.0,
            "max_vibration": 5.5,
            "max_rpm": 3000.0,
            "max_load": 95.0,
            "production_rate": 2
        }
    })

    @classmethod
    def normalize_machine_id(cls, machine_id: str) -> str:
        """Resolve any alias (e.g. 'Motor_1' -> 'Motor')."""
        return MachineRegistry.ALIASES.get(machine_id, machine_id)

    # Anomaly Risk Thresholds (Score normalized 0 - 100)
    RISK_LEVELS = {
        "LOW": (0.0, 39.9),
        "MEDIUM": (40.0, 64.9),
        "HIGH": (65.0, 84.9),
        "CRITICAL": (85.0, 100.0)
    }

    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they do not exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.GENERATED_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cls.AI_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        cls.DOCS_DIR.mkdir(parents=True, exist_ok=True)
        cls.TESTS_DIR.mkdir(parents=True, exist_ok=True)
