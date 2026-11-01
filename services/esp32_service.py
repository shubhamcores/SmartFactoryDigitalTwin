"""
ESP32 Hardware Ingestion Service for FactoryTwin (P_307)
Processes live telemetry arriving directly from physical or simulated ESP32 edge nodes
(Supports HTTP REST POST and MQTT transports).
Performs schema validation, range checks, deduplication, Isolation Forest inference,
threshold evaluation, and database persistence with data_source = 'ESP32_EDGE'.
"""

import time
import logging
from datetime import datetime
from database import get_db_connection
from config import Config
from ai_model.predict import get_anomaly_detector
from services.alert_service import evaluate_telemetry_for_alerts

logger = logging.getLogger(__name__)

def ingest_esp32_telemetry(payload: dict) -> tuple[bool, dict, str]:
    """
    Ingest, validate, infer anomalies, and persist an ESP32 telemetry packet.
    Returns: (success: bool, result_dict: dict, error_message: str)
    """
    if not isinstance(payload, dict):
        return False, {}, "Payload must be a JSON object"

    # Required fields check
    required_fields = ["machine_id", "temperature", "vibration"]
    missing = [f for f in required_fields if f not in payload]
    if missing:
        return False, {}, f"Missing required ESP32 fields: {missing}"

    machine_id = str(payload["machine_id"])
    if machine_id not in Config.MACHINES:
        return False, {}, f"Unknown machine identifier: {machine_id}"

    # Parse and validate numerical values
    try:
        temp = float(payload["temperature"])
        vib = float(payload["vibration"])
        speed = float(payload.get("speed", Config.MACHINES[machine_id]["base_rpm"]))
        load = float(payload.get("load", Config.MACHINES[machine_id]["base_load"]))
        prod_count = int(payload.get("production_count", 0))
    except (ValueError, TypeError) as e:
        return False, {}, f"Invalid numerical sensor data: {e}"

    # Physical sanity checks
    if not (-50.0 <= temp <= 300.0):
        return False, {}, f"Temperature {temp}°C outside plausible physical range (-50 to 300°C)"
    if not (0.0 <= vib <= 100.0):
        return False, {}, f"Vibration {vib} mm/s outside plausible range (0 to 100 mm/s)"

    timestamp = payload.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message_id = payload.get("message_id") or f"ESP32-{machine_id}-{int(time.time() * 1000)}"
    status = str(payload.get("status", "RUNNING")).upper()

    telemetry_record = {
        "message_id": message_id,
        "machine_id": machine_id,
        "timestamp": timestamp,
        "temperature": round(temp, 2),
        "vibration": round(vib, 3),
        "speed": round(speed, 1),
        "load": round(load, 1),
        "status": status,
        "production_count": prod_count,
        "data_source": "ESP32_EDGE"
    }

    # Deduplication check & Database Persistence
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM telemetry WHERE message_id = ?", (message_id,))
        if cursor.fetchone():
            conn.close()
            return False, {}, f"Duplicate message ignored (message_id: {message_id})"

        # Run AI Anomaly Inference
        detector = get_anomaly_detector()
        anomaly_res = detector.predict(
            machine_id=machine_id,
            temperature=temp,
            vibration=vib,
            speed=speed,
            load=load
        )

        # Insert Telemetry Record
        cursor.execute("""
            INSERT INTO telemetry (
                message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id, machine_id, timestamp, temp, vib, speed, load, status, prod_count, "ESP32_EDGE"
        ))
        telemetry_id = cursor.lastrowid

        # Insert Anomaly Prediction
        cursor.execute("""
            INSERT INTO anomaly_predictions (
                telemetry_id, machine_id, timestamp, anomaly_score, is_anomaly, risk_category, detection_method, suggested_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telemetry_id, machine_id, timestamp,
            anomaly_res["anomaly_score"],
            1 if anomaly_res["is_anomaly"] else 0,
            anomaly_res["risk_category"],
            anomaly_res["detection_method"],
            anomaly_res["suggested_action"]
        ))

        # Check machine status change
        cursor.execute("SELECT current_status FROM machines WHERE machine_id = ?", (machine_id,))
        row = cursor.fetchone()
        old_status = row["current_status"] if row else "RUNNING"

        if old_status != status:
            cursor.execute("UPDATE machines SET current_status = ? WHERE machine_id = ?", (status, machine_id))
            cursor.execute("""
                INSERT INTO machine_status_history (machine_id, old_status, new_status, reason)
                VALUES (?, ?, ?, ?)
            """, (machine_id, old_status, status, "Status updated from live ESP32 hardware edge telemetry"))

        conn.commit()
        conn.close()

        # Evaluate safety alerts
        evaluate_telemetry_for_alerts(telemetry_record, anomaly_res)

        logger.info(f"ESP32 Edge telemetry ingested successfully for {machine_id} (ID={telemetry_id}, Temp={temp}°C, Vib={vib}mm/s)")

        return True, {
            "telemetry_id": telemetry_id,
            "machine_id": machine_id,
            "data_source": "ESP32_EDGE",
            "anomaly_score": anomaly_res["anomaly_score"],
            "risk_category": anomaly_res["risk_category"],
            "is_anomaly": anomaly_res["is_anomaly"],
            "suggested_action": anomaly_res["suggested_action"]
        }, ""

    except Exception as e:
        logger.error(f"Error persisting ESP32 telemetry: {e}", exc_info=True)
        return False, {}, f"Persistence error: {str(e)}"
