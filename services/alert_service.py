"""
Alert and Health Monitoring Service for FactoryTwin (P_307)
Processes incoming machine telemetry and AI anomaly predictions, generates alerts,
enforces cooldown deduplication, and manages operator acknowledgement and administrator resolution.
"""

import time
import logging
from datetime import datetime
from database import get_db_connection
from config import Config

logger = logging.getLogger(__name__)

# In-memory alert cooldown tracker: { "MachineID:AlertType": last_alert_epoch }
_cooldown_tracker = {}

def evaluate_telemetry_for_alerts(telemetry_data: dict, anomaly_result: dict = None):
    """
    Examine telemetry and anomaly scores against threshold rules.
    Generates new alerts when violations occur and cooldown has expired.
    """
    machine_id = telemetry_data["machine_id"]
    temp = float(telemetry_data["temperature"])
    vib = float(telemetry_data["vibration"])
    speed = float(telemetry_data["speed"])
    load = float(telemetry_data["load"])
    status = telemetry_data.get("status", "RUNNING")
    prod_count = int(telemetry_data.get("production_count", 0))

    cfg = Config.MACHINES.get(machine_id, {})
    max_temp = cfg.get("max_temp", 85.0)
    max_vib = cfg.get("max_vibration", 4.5)
    max_load = cfg.get("max_load", 90.0)
    base_rpm = cfg.get("base_rpm", 1800.0)

    generated_alerts = []

    # 1. Temperature Check
    if temp > (max_temp + 10.0):
        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="EXCESSIVE_TEMPERATURE",
            severity="CRITICAL",
            message=f"Critical thermal threshold breached: {temp:.1f}°C (Limit: {max_temp}°C). Thermal runaway risk.",
            action_taken="Emergency cooling cycle triggered. Inspect heat sinks, coolant lines, and ventilation fans."
        )
        if alert:
            generated_alerts.append(alert)
    elif temp > max_temp:
        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="EXCESSIVE_TEMPERATURE",
            severity="WARNING",
            message=f"High operating temperature: {temp:.1f}°C exceeds threshold of {max_temp}°C.",
            action_taken="Verify coolant pump operation and clean air intake filters."
        )
        if alert:
            generated_alerts.append(alert)

    # 2. Vibration Check
    if vib > (max_vib + 2.0):
        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="EXCESSIVE_VIBRATION",
            severity="CRITICAL",
            message=f"Severe mechanical vibration: {vib:.2f} mm/s (Safety ceiling: {max_vib} mm/s). High risk of bearing failure.",
            action_taken="Stop machine immediately. Conduct ultrasonic bearing analysis and inspect shaft alignment."
        )
        if alert:
            generated_alerts.append(alert)
    elif vib > max_vib:
        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="EXCESSIVE_VIBRATION",
            severity="WARNING",
            message=f"Elevated vibration: {vib:.2f} mm/s exceeds guideline of {max_vib} mm/s.",
            action_taken="Check foundation torque, dynamic balance, and mechanical coupling."
        )
        if alert:
            generated_alerts.append(alert)

    # 3. Load Check
    if load > max_load:
        severity = "CRITICAL" if load >= 98.0 else "WARNING"
        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="OVERLOAD",
            severity=severity,
            message=f"Machine load overload: {load:.1f}% exceeds nominal capacity limit of {max_load}%.",
            action_taken="Reduce feed rate, check for mechanical binding or product jams in drive train."
        )
        if alert:
            generated_alerts.append(alert)

    # 4. Stoppage Check
    if status == "STOPPED" or (speed < 10.0 and status != "IDLE"):
        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="UNEXPECTED_STOPPAGE",
            severity="CRITICAL",
            message=f"Machine stoppage detected: Speed fell to {speed:.0f} RPM while in operational cycle.",
            action_taken="Inspect E-Stop circuit, VFD trip codes, and motor thermal overload breaker."
        )
        if alert:
            generated_alerts.append(alert)

    # 5. AI Anomaly Check
    if anomaly_result and anomaly_result.get("is_anomaly"):
        risk = anomaly_result.get("risk_category", "MEDIUM")
        score = anomaly_result.get("anomaly_score", 0.0)
        method = anomaly_result.get("detection_method", "ISOLATION_FOREST")
        severity = "CRITICAL" if risk == "CRITICAL" else "WARNING"

        alert = _create_alert_if_not_in_cooldown(
            machine_id=machine_id,
            alert_type="ANOMALY_DETECTED",
            severity=severity,
            message=f"AI Anomaly [{method}]: Multivariate outlier detected (Risk Score: {score:.1f}/100, Tier: {risk}).",
            action_taken=anomaly_result.get("suggested_action", "Audit sensor telemetry and schedule physical inspection.")
        )
        if alert:
            generated_alerts.append(alert)

    return generated_alerts

def _create_alert_if_not_in_cooldown(machine_id: str, alert_type: str, severity: str, message: str, action_taken: str):
    """Enforce deduplication cooldown before persisting alert in database."""
    cooldown_key = f"{machine_id}:{alert_type}"
    now_epoch = time.time()
    last_triggered = _cooldown_tracker.get(cooldown_key, 0)

    if (now_epoch - last_triggered) < Config.ALERT_COOLDOWN_SECONDS:
        # Suppress duplicate alert during cooldown
        return None

    _cooldown_tracker[cooldown_key] = now_epoch

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (machine_id, alert_type, severity, message, status, action_taken)
            VALUES (?, ?, ?, ?, 'NEW', ?)
        """, (machine_id, alert_type, severity, message, action_taken))
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.warning(f"New Alert [{severity}] for {machine_id}: {message} (ID={alert_id})")
        return {
            "id": alert_id,
            "machine_id": machine_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "status": "NEW",
            "action_taken": action_taken
        }
    except Exception as e:
        logger.error(f"Failed to persist alert: {e}")
        return None

def acknowledge_alert(alert_id: int, username: str) -> bool:
    """Mark an alert as acknowledged by an operator or admin."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alerts
        SET status = 'ACKNOWLEDGED', acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'NEW'
    """, (username, alert_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def resolve_alert(alert_id: int, username: str, resolution_notes: str = None) -> bool:
    """Mark an alert as resolved by an administrator."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE alerts
        SET status = 'RESOLVED', resolved_by = ?, resolved_at = CURRENT_TIMESTAMP,
            action_taken = CASE WHEN ? IS NOT NULL AND ? != '' THEN ? ELSE action_taken END
        WHERE id = ?
    """, (username, resolution_notes, resolution_notes, resolution_notes, alert_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_recent_alerts(limit: int = 50, machine_id: str = None, severity: str = None, status: str = None):
    """Query alerts with flexible filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM alerts WHERE 1=1"
    params = []

    if machine_id:
        query += " AND machine_id = ?"
        params.append(machine_id)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_alert_statistics():
    """Return summary statistics of active and historical alerts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'NEW' THEN 1 ELSE 0 END) as new_count,
            SUM(CASE WHEN status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as ack_count,
            SUM(CASE WHEN status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_count,
            SUM(CASE WHEN severity = 'CRITICAL' AND status != 'RESOLVED' THEN 1 ELSE 0 END) as active_critical
        FROM alerts
    """)
    row = cursor.fetchone()
    conn.close()
    return {
        "total": row["total"] or 0,
        "new": row["new_count"] or 0,
        "acknowledged": row["ack_count"] or 0,
        "resolved": row["resolved_count"] or 0,
        "active_critical": row["active_critical"] or 0
    }
