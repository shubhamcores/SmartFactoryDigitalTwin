"""
MQTT Configuration and Payload Validation (P_307)
Provides settings for local MQTT and HiveMQ Cloud (TLS 8883) brokers,
and enforces payload schema and range validation.
"""

import os
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

# MQTT Topics
BASE_TOPIC = Config.MQTT_TOPIC_PREFIX
TELEMETRY_SUBSCRIBE_TOPIC = f"{BASE_TOPIC}/+/telemetry"
ALERT_TOPIC = f"{BASE_TOPIC}/alerts"

def get_machine_telemetry_topic(machine_id: str) -> str:
    """Generate canonical publish topic for a specific machine."""
    return f"{BASE_TOPIC}/{machine_id}/telemetry"

def validate_telemetry_payload(payload_str: str) -> tuple[bool, dict, str]:
    """
    Validate incoming MQTT telemetry message.
    Returns: (is_valid: bool, parsed_dict: dict, error_message: str)
    """
    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError as e:
        return False, {}, f"Invalid JSON format: {e}"

    if not isinstance(data, dict):
        return False, {}, "Payload must be a JSON object"

    # Required field verification
    required_fields = ["machine_id", "temperature", "vibration", "speed", "load"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return False, {}, f"Missing mandatory telemetry fields: {missing}"

    # Machine ID validation
    machine_id = str(data["machine_id"])
    if machine_id not in Config.MACHINES:
        return False, {}, f"Unknown machine identifier: {machine_id}"

    # Numeric and Range Validations
    try:
        temp = float(data["temperature"])
        vib = float(data["vibration"])
        speed = float(data["speed"])
        load = float(data["load"])
    except (ValueError, TypeError) as e:
        return False, {}, f"Sensor values must be numeric: {e}"

    # Physical plausibility limits
    if not (-50.0 <= temp <= 300.0):
        return False, {}, f"Temperature {temp}°C outside physical limits (-50 to 300°C)"
    if not (0.0 <= vib <= 100.0):
        return False, {}, f"Vibration {vib} mm/s outside physical limits (0 to 100 mm/s)"
    if not (0.0 <= speed <= 15000.0):
        return False, {}, f"Speed {speed} RPM outside physical limits (0 to 15000 RPM)"
    if not (0.0 <= load <= 150.0):
        return False, {}, f"Load {load}% outside physical limits (0 to 150%)"

    # Normalize sanitized dictionary
    sanitized = {
        "message_id": str(data.get("message_id", f"MQTT-{machine_id}-{int(os.times().elapsed * 1000)}")),
        "machine_id": machine_id,
        "timestamp": str(data.get("timestamp", "")),
        "temperature": round(temp, 2),
        "vibration": round(vib, 3),
        "speed": round(speed, 1),
        "load": round(load, 1),
        "status": str(data.get("status", "RUNNING")).upper(),
        "production_count": int(data.get("production_count", 0)),
        "data_source": "MQTT_LIVE"
    }

    return True, sanitized, ""
