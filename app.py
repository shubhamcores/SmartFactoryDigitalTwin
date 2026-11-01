"""
FactoryTwin - AI-Driven Digital Twin for Smart Factory Operations
Main Flask Web Application and REST API Gateway.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, Response, send_file, abort
)
from werkzeug.security import generate_password_hash

# Core Configuration & Database
from config import Config
from database import get_db_connection, init_db

# Services & Logic
from ai_model.predict import get_anomaly_detector
from simulation.simulator import get_simulator
from services.auth_service import authenticate_user, login_required, admin_required
from services.audit_service import log_audit_event, get_recent_audit_logs
from services.alert_service import (
    acknowledge_alert, resolve_alert, get_recent_alerts, get_alert_statistics
)
from services.report_service import generate_csv_report, generate_pdf_report, fetch_report_data
from services.esp32_service import ingest_esp32_telemetry

# Optional MQTT Components
mqtt_subscriber_worker = None
if Config.MQTT_ENABLED:
    try:
        from mqtt.subscriber import MQTTSubscriber
        mqtt_subscriber_worker = MQTTSubscriber()
    except Exception as e:
        logging.warning(f"MQTT subscriber could not be loaded: {e}")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("FactoryTwin")

def create_app():
    """Application factory for FactoryTwin."""
    Config.ensure_directories()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME

    # Context Processor for Global Template Variables
    @app.context_processor
    def inject_global_template_data():
        return {
            "config": Config,
            "machines": Config.MACHINES,
            "current_year": datetime.now().year
        }

    # =========================================================================
    # AUTHENTICATION ROUTES
    # =========================================================================
    @app.route("/login", methods=["GET", "POST"], endpoint="auth.login")
    def login():
        if "user_id" in session:
            return redirect(url_for("dashboard.index"))

        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            user = authenticate_user(username, password, request.remote_addr)
            if user:
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                session["full_name"] = user["full_name"]
                flash(f"Welcome back, {user['full_name']}! Signed in as {user['role'].upper()}.", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("dashboard.index"))
            else:
                flash("Invalid username or password. Please verify your credentials.", "danger")

        return render_template("login.html")

    @app.route("/logout", endpoint="auth.logout")
    def logout():
        username = session.get("username", "Unknown")
        user_id = session.get("user_id")
        log_audit_event(user_id, username, "LOGOUT", request.remote_addr, "User signed out")
        session.clear()
        flash("You have been signed out safely.", "info")
        return redirect(url_for("auth.login"))

    # =========================================================================
    # SCADA DASHBOARD ROUTES
    # =========================================================================
    @app.route("/", endpoint="index")
    @login_required
    def index():
        return redirect(url_for("dashboard.index"))

    @app.route("/dashboard", endpoint="dashboard.index")
    @login_required
    def dashboard():
        return render_template("dashboard.html", machines=Config.MACHINES)

    @app.route("/machine/<machine_id>", endpoint="dashboard.machine_detail")
    @login_required
    def machine_detail(machine_id):
        if machine_id not in Config.MACHINES:
            abort(404, description=f"Machine asset '{machine_id}' does not exist.")

        machine_cfg = Config.MACHINES[machine_id]

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get Machine status row
        cursor.execute("SELECT * FROM machines WHERE machine_id = ?", (machine_id,))
        m_row = cursor.fetchone()

        # Get Scheduled Maintenance
        cursor.execute("""
            SELECT * FROM maintenance_records 
            WHERE machine_id = ? 
            ORDER BY scheduled_date ASC LIMIT 5
        """, (machine_id,))
        maintenance = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return render_template(
            "machine_detail.html",
            machine_id=machine_id,
            machine=machine_cfg,
            db_machine=dict(m_row) if m_row else {},
            maintenance=maintenance
        )

    # =========================================================================
    # ALERTS MANAGEMENT ROUTES
    # =========================================================================
    @app.route("/alerts", endpoint="alerts.index")
    @login_required
    def alerts_index():
        machine_id = request.args.get("machine_id", "ALL")
        severity = request.args.get("severity", "ALL")
        status = request.args.get("status", "ALL")

        alerts_list = get_recent_alerts(
            limit=100,
            machine_id=machine_id if machine_id != "ALL" else None,
            severity=severity if severity != "ALL" else None,
            status=status if status != "ALL" else None
        )
        stats = get_alert_statistics()

        return render_template(
            "alerts.html",
            alerts=alerts_list,
            stats=stats,
            current_filters={"machine_id": machine_id, "severity": severity, "status": status}
        )

    @app.route("/alerts/<int:alert_id>/acknowledge", methods=["POST"], endpoint="alerts.acknowledge")
    @login_required
    def acknowledge(alert_id):
        username = session.get("username", "Operator")
        success = acknowledge_alert(alert_id, username)
        if success:
            log_audit_event(session.get("user_id"), username, "ALERT_ACKNOWLEDGED", request.remote_addr, f"Alert ID: #{alert_id}")
            flash(f"Alert #{alert_id} acknowledged.", "success")
        else:
            flash("Alert acknowledgement could not be processed.", "warning")
        return redirect(request.referrer or url_for("alerts.index"))

    @app.route("/alerts/<int:alert_id>/resolve", methods=["POST"], endpoint="alerts.resolve")
    @admin_required
    def resolve(alert_id):
        username = session.get("username", "Administrator")
        action_notes = request.form.get("action_notes", "").strip()
        success = resolve_alert(alert_id, username, action_notes)
        if success:
            log_audit_event(session.get("user_id"), username, "ALERT_RESOLVED", request.remote_addr, f"Alert ID: #{alert_id}. Notes: {action_notes}")
            flash(f"Alert #{alert_id} marked as resolved.", "success")
        else:
            flash("Alert resolution could not be completed.", "warning")
        return redirect(request.referrer or url_for("alerts.index"))

    # =========================================================================
    # OPERATIONAL REPORTS ROUTES
    # =========================================================================
    @app.route("/reports", endpoint="reports.index")
    @login_required
    def reports_index():
        report_type = request.args.get("report_type", "telemetry")
        machine_id = request.args.get("machine_id", "ALL")
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")

        headers, rows = fetch_report_data(
            report_type=report_type,
            start_date=start_date or None,
            end_date=end_date or None,
            machine_id=machine_id if machine_id != "ALL" else None
        )

        # Get historical report generation events
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM report_events ORDER BY id DESC LIMIT 10")
        report_events = [dict(r) for r in cursor.fetchall()]
        conn.close()

        current_filters = {
            "report_type": report_type,
            "machine_id": machine_id,
            "start_date": start_date,
            "end_date": end_date
        }

        return render_template(
            "reports.html",
            headers=headers,
            rows=rows[:100],  # Limit preview to 100 rows
            report_events=report_events,
            current_filters=current_filters
        )

    @app.route("/reports/export/csv", endpoint="reports.export_csv")
    @login_required
    def export_csv():
        report_type = request.args.get("report_type", "telemetry")
        filters = {
            "machine_id": request.args.get("machine_id", "ALL"),
            "start_date": request.args.get("start_date", "") or None,
            "end_date": request.args.get("end_date", "") or None,
            "status": request.args.get("status", "ALL"),
            "severity": request.args.get("severity", "ALL")
        }
        username = session.get("username", "User")
        csv_bytes = generate_csv_report(report_type, filters, generated_by=username)

        filename = f"factory_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            csv_bytes,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    @app.route("/reports/export/pdf", endpoint="reports.export_pdf")
    @login_required
    def export_pdf():
        report_type = request.args.get("report_type", "telemetry")
        filters = {
            "machine_id": request.args.get("machine_id", "ALL"),
            "start_date": request.args.get("start_date", "") or None,
            "end_date": request.args.get("end_date", "") or None,
            "status": request.args.get("status", "ALL"),
            "severity": request.args.get("severity", "ALL")
        }
        username = session.get("username", "User")
        pdf_bytes = generate_pdf_report(report_type, filters, generated_by=username)

        filename = f"factory_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    # =========================================================================
    # PLANT ADMINISTRATION ROUTES (ADMIN ONLY)
    # =========================================================================
    @app.route("/admin/users", endpoint="admin.users")
    @admin_required
    def admin_users():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, email, role, created_at, last_login FROM users ORDER BY id ASC")
        users = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return render_template("admin_users.html", users=users)

    @app.route("/admin/users/create", methods=["POST"], endpoint="admin.create_user")
    @admin_required
    def admin_create_user():
        username = request.form.get("username", "").strip()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "operator")
        password = request.form.get("password", "")

        if not username or not full_name or not password:
            flash("All mandatory fields must be completed.", "danger")
            return redirect(url_for("admin.users"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for("admin.users"))

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            pwd_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, full_name, email)
                VALUES (?, ?, ?, ?, ?)
            """, (username, pwd_hash, role, full_name, email))
            conn.commit()
            log_audit_event(session.get("user_id"), session.get("username"), "USER_CREATED", request.remote_addr, f"Created user {username} ({role})")
            flash(f"User account '{username}' successfully registered.", "success")
        except Exception as e:
            conn.rollback()
            flash(f"Could not create user: Username '{username}' may already exist.", "danger")
        finally:
            conn.close()

        return redirect(url_for("admin.users"))

    @app.route("/admin/audit", endpoint="admin.audit")
    @admin_required
    def admin_audit():
        logs = get_recent_audit_logs(limit=100)
        return render_template("admin_audit.html", audit_logs=logs)

    # =========================================================================
    # REST APIs FOR DASHBOARD & INTEGRATIONS
    # =========================================================================
    @app.route("/api/telemetry/latest")
    @login_required
    def api_telemetry_latest():
        """Retrieve most recent telemetry record and anomaly prediction for each machine."""
        conn = get_db_connection()
        cursor = conn.cursor()

        results = []
        for m_id in Config.MACHINES.keys():
            cursor.execute("""
                SELECT t.*, a.anomaly_score, a.is_anomaly, a.risk_category, a.detection_method, a.suggested_action
                FROM telemetry t
                LEFT JOIN anomaly_predictions a ON a.telemetry_id = t.id
                WHERE t.machine_id = ?
                ORDER BY t.id DESC LIMIT 1
            """, (m_id,))
            row = cursor.fetchone()
            if row:
                results.append(dict(row))

        conn.close()
        sim = get_simulator()
        return jsonify({
            "telemetry": results,
            "simulator_running": sim.is_running(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    @app.route("/api/telemetry/history/<machine_id>")
    @login_required
    def api_telemetry_history(machine_id):
        limit = min(100, int(request.args.get("limit", 25)))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
            FROM telemetry
            WHERE machine_id = ?
            ORDER BY id DESC LIMIT ?
        """, (machine_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"machine_id": machine_id, "history": [dict(r) for r in rows]})

    @app.route("/api/anomalies/<machine_id>")
    @login_required
    def api_machine_anomalies(machine_id):
        limit = min(50, int(request.args.get("limit", 10)))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, machine_id, timestamp, anomaly_score, is_anomaly, risk_category, detection_method, suggested_action
            FROM anomaly_predictions
            WHERE machine_id = ? AND (is_anomaly = 1 OR anomaly_score >= 40.0)
            ORDER BY id DESC LIMIT ?
        """, (machine_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"machine_id": machine_id, "anomalies": [dict(r) for r in rows]})

    @app.route("/api/alerts")
    @login_required
    def api_alerts():
        limit = min(100, int(request.args.get("limit", 50)))
        alerts_list = get_recent_alerts(limit=limit)
        stats = get_alert_statistics()
        return jsonify({"alerts": alerts_list, "statistics": stats})

    @app.route("/api/alerts/count")
    @login_required
    def api_alerts_count():
        return jsonify(get_alert_statistics())

    @app.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
    @login_required
    def api_alert_acknowledge(alert_id):
        username = session.get("username", "Operator")
        success = acknowledge_alert(alert_id, username)
        if success:
            log_audit_event(session.get("user_id"), username, "API_ALERT_ACK", request.remote_addr, f"Alert #{alert_id}")
            return jsonify({"success": True, "message": f"Alert #{alert_id} acknowledged"})
        return jsonify({"success": False, "message": "Failed to acknowledge alert"}), 400

    @app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
    @admin_required
    def api_alert_resolve(alert_id):
        username = session.get("username", "Administrator")
        data = request.get_json(silent=True) or {}
        action_notes = data.get("action_notes", "Resolved via API")
        success = resolve_alert(alert_id, username, action_notes)
        if success:
            log_audit_event(session.get("user_id"), username, "API_ALERT_RESOLVE", request.remote_addr, f"Alert #{alert_id}")
            return jsonify({"success": True, "message": f"Alert #{alert_id} resolved"})
        return jsonify({"success": False, "message": "Failed to resolve alert"}), 400

    @app.route("/api/simulator/status")
    @login_required
    def api_simulator_status():
        sim = get_simulator()
        return jsonify(sim.get_status())

    @app.route("/api/simulator/start", methods=["POST"])
    @admin_required
    def api_simulator_start():
        sim = get_simulator()
        started = sim.start()
        log_audit_event(session.get("user_id"), session.get("username"), "SIMULATOR_START", request.remote_addr)
        return jsonify({"success": started, "message": "Simulator started" if started else "Already running"})

    @app.route("/api/simulator/stop", methods=["POST"])
    @admin_required
    def api_simulator_stop():
        sim = get_simulator()
        stopped = sim.stop()
        log_audit_event(session.get("user_id"), session.get("username"), "SIMULATOR_STOP", request.remote_addr)
        return jsonify({"success": stopped, "message": "Simulator stopped" if stopped else "Not running"})

    @app.route("/api/simulator/inject_fault", methods=["POST"])
    @login_required
    def api_simulator_inject_fault():
        data = request.get_json(silent=True) or {}
        machine_id = data.get("machine_id")
        condition = data.get("condition", "NORMAL")
        duration = int(data.get("duration_cycles", 15))

        if not machine_id or machine_id not in Config.MACHINES:
            return jsonify({"success": False, "message": f"Invalid machine ID: {machine_id}"}), 400

        valid_conditions = ["NORMAL", "HIGH_TEMP", "HIGH_VIB", "EXCESSIVE_LOAD", "REDUCED_PRODUCTION", "STOPPAGE", "ABNORMAL_SENSOR"]
        if condition.upper() not in valid_conditions:
            return jsonify({"success": False, "message": f"Invalid condition: {condition}"}), 400

        sim = get_simulator()
        success = sim.inject_fault(machine_id, condition, duration)
        log_audit_event(session.get("user_id"), session.get("username"), "FAULT_INJECTED", request.remote_addr, f"Machine: {machine_id}, Condition: {condition}, Cycles: {duration}")

        return jsonify({
            "success": success,
            "message": f"Regime '{condition}' applied to {machine_id} for {duration} cycles."
        })

    @app.route("/api/mqtt/status")
    @login_required
    def api_mqtt_status():
        return jsonify({
            "enabled": Config.MQTT_ENABLED,
            "broker": Config.MQTT_BROKER_HOST,
            "port": Config.MQTT_BROKER_PORT,
            "tls": Config.MQTT_USE_TLS,
            "connected": getattr(mqtt_subscriber_worker, "is_connected", False) if mqtt_subscriber_worker else False
        })

    # =========================================================================
    # DATA SOURCE SELECTION (SYNTHETIC SIMULATOR VS ESP32 HARDWARE NODE)
    # =========================================================================
    @app.route("/api/datasource/mode")
    @login_required
    def api_datasource_mode():
        sim = get_simulator()
        modes = sim.get_source_modes()
        all_esp32 = all(m == "ESP32" for m in modes.values())
        any_esp32 = any(m == "ESP32" for m in modes.values())
        global_mode = "ESP32" if all_esp32 else ("HYBRID" if any_esp32 else "SYNTHETIC")
        return jsonify({
            "global_mode": global_mode,
            "source_modes": modes,
            "mqtt_connected": getattr(mqtt_subscriber_worker, "is_connected", False) if mqtt_subscriber_worker else False,
            "mqtt_broker": Config.MQTT_BROKER_HOST if Config.MQTT_ENABLED else "Offline (Simulator Active)",
            "esp32_http_endpoint": f"http://{request.host}/api/esp32/telemetry"
        })

    @app.route("/api/datasource/set_mode", methods=["POST"])
    @login_required
    def api_datasource_set_mode():
        data = request.get_json(silent=True) or {}
        mode = data.get("mode", "SYNTHETIC").upper()
        machine_id = data.get("machine_id", "ALL")

        if mode not in ("SYNTHETIC", "ESP32"):
            return jsonify({"success": False, "message": "Invalid mode. Choose 'SYNTHETIC' or 'ESP32'."}), 400

        sim = get_simulator()
        success = sim.set_source_mode(machine_id, mode)
        if success:
            log_audit_event(
                session.get("user_id"),
                session.get("username", "User"),
                "DATA_SOURCE_MODE_CHANGED",
                request.remote_addr,
                f"Scope: {machine_id}, New Mode: {mode}"
            )
            return jsonify({
                "success": True,
                "message": f"Data source mode set to '{mode}' for {machine_id}.",
                "source_modes": sim.get_source_modes()
            })
        return jsonify({"success": False, "message": "Failed to update source mode."}), 400

    @app.route("/api/esp32/telemetry", methods=["POST"])
    def api_esp32_telemetry():
        """Public or device-facing REST ingestion endpoint for physical ESP32 edge nodes."""
        data = request.get_json(silent=True) or {}
        if not data:
            return jsonify({"success": False, "error": "Invalid or empty JSON body."}), 400

        success, res, err = ingest_esp32_telemetry(data)
        if success:
            return jsonify({"success": True, "message": "ESP32 telemetry ingested successfully", "telemetry": res}), 200
        return jsonify({"success": False, "error": err}), 400

    @app.route("/api/esp32/test_packet", methods=["POST"])
    @login_required
    def api_esp32_test_packet():
        """Simulate sending a real ESP32 hardware telemetry packet for testing and demonstration."""
        import time
        data = request.get_json(silent=True) or {}
        machine_id = data.get("machine_id", "Motor_1")
        temp = float(data.get("temperature", 68.4))
        vib = float(data.get("vibration", 2.15))
        speed = float(data.get("speed", 1745.0))
        load = float(data.get("load", 66.0))

        sample_packet = {
            "message_id": f"ESP32-EMU-{int(time.time() * 1000)}",
            "machine_id": machine_id,
            "temperature": temp,
            "vibration": vib,
            "speed": speed,
            "load": load,
            "status": "WARNING" if (vib > 4.5 or temp > 85.0) else "RUNNING",
            "production_count": 125,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        success, res, err = ingest_esp32_telemetry(sample_packet)
        if success:
            return jsonify({
                "success": True,
                "message": f"Simulated ESP32 packet successfully ingested for {machine_id}!",
                "telemetry": res
            })
        return jsonify({"success": False, "error": err}), 400

    # =========================================================================
    # ERROR HANDLERS
    # =========================================================================
    @app.errorhandler(403)
    def forbidden(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Forbidden: Administrator privileges required.", "status": 403}), 403
        return render_template("login.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found", "status": 404}), 404
        return render_template("dashboard.html", machines=Config.MACHINES), 404

    return app

# Main entry point
app = create_app()

def start_services():
    """Start database initialization, model training check, simulator, and MQTT."""
    logger.info("Initializing FactoryTwin runtime...")
    # 1. Initialize DB if not present
    init_db(force_recreate=False)

    # 2. Check AI Model
    detector = get_anomaly_detector()
    if detector.model is None:
        logger.info("Isolation Forest model file not found on disk. Initializing and training model...")
        try:
            from ai_model.train_model import train_and_evaluate
            train_and_evaluate()
            detector.load_model()
        except Exception as e:
            logger.error(f"Failed to auto-train AI model: {e}. Will use Rule-Based Fallback.")

    # 3. Start Simulator if enabled
    if Config.SIMULATION_ENABLED:
        sim = get_simulator()
        sim.start()
        logger.info("Factory machine digital twin simulation engine running.")

    # 4. Start MQTT Subscriber if enabled
    if Config.MQTT_ENABLED and mqtt_subscriber_worker:
        mqtt_subscriber_worker.start()
        logger.info("MQTT live telemetry subscriber worker running.")

if __name__ == "__main__":
    start_services()
    port = int(os.getenv("PORT", 5000))
    print("\n" + "=" * 70)
    print("SMART FACTORY DIGITAL TWIN")
    print(f" Web Dashboard: http://127.0.0.1:{port}")
    print(" Default Administrator: admin / Admin@12345")
    print(" Default Plant Operator: operator / Operator@12345")
    print("=" * 70 + "\n")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
