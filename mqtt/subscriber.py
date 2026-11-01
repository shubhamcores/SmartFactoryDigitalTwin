"""
MQTT Subscriber Worker for FactoryTwin (P_307)
Subscribes to 'factory/machines/+/telemetry', validates incoming JSON schemas,
deduplicates messages, persists live telemetry into SQLite, runs ML anomaly inference,
and evaluates industrial safety alerts.
"""

import sys
import ssl
import time
import json
import logging
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from database import get_db_connection
from config import Config
from mqtt.config import TELEMETRY_SUBSCRIBE_TOPIC, validate_telemetry_payload
from ai_model.predict import get_anomaly_detector
from services.alert_service import evaluate_telemetry_for_alerts

logger = logging.getLogger(__name__)

class MQTTSubscriber:
    """Background MQTT subscriber consumer engine."""

    def __init__(self):
        self.client_id = f"{Config.MQTT_CLIENT_ID_PREFIX}-Sub-{int(time.time())}"
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id
            )
        except AttributeError:
            self.client = mqtt.Client(client_id=self.client_id)

        self.is_connected = False
        self.processed_count = 0
        self.discarded_count = 0
        self._detector = None
        self._setup_client()

    def _setup_client(self):
        """Configure callbacks, TLS, and broker credentials."""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
            self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)

        if Config.MQTT_USE_TLS:
            context = ssl.create_default_context()
            self.client.tls_set_context(context)
            logger.info("Configured TLS for HiveMQ Cloud subscriber")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = getattr(rc, "value", rc)
        if rc_code == 0:
            self.is_connected = True
            logger.info(f"[MQTT] Subscriber connected. Subscribing to: {TELEMETRY_SUBSCRIBE_TOPIC}")
            self.client.subscribe(TELEMETRY_SUBSCRIBE_TOPIC, qos=1)
        else:
            self.is_connected = False
            logger.error(f"[MQTT] Subscriber connection failed with rc={rc_code}")

    def _on_disconnect(self, client, userdata, rc, properties=None, reason_code=None):
        self.is_connected = False
        logger.warning(f"[MQTT] Subscriber disconnected from broker (rc={rc})")

    def _on_message(self, client, userdata, msg):
        """Handle incoming telemetry message with validation and error containment."""
        try:
            payload_str = msg.payload.decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to decode message bytes as UTF-8: {e}")
            self.discarded_count += 1
            return

        is_valid, telemetry, err_msg = validate_telemetry_payload(payload_str)
        if not is_valid:
            logger.warning(f"Discarded malformed MQTT message on {msg.topic}: {err_msg}")
            self.discarded_count += 1
            return

        if not telemetry.get("timestamp"):
            telemetry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Process and persist reading
        try:
            self._process_valid_telemetry(telemetry)
            self.processed_count += 1
        except Exception as e:
            logger.error(f"Error persisting MQTT telemetry: {e}", exc_info=True)

    def _process_valid_telemetry(self, telemetry: dict):
        """Deduplicate, run AI inference, evaluate alerts, and store in SQLite."""
        if self._detector is None:
            self._detector = get_anomaly_detector()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Deduplication check via message_id
        msg_id = telemetry["message_id"]
        cursor.execute("SELECT id FROM telemetry WHERE message_id = ?", (msg_id,))
        if cursor.fetchone():
            logger.debug(f"Skipping duplicate message_id: {msg_id}")
            conn.close()
            return

        # AI Anomaly Inference
        anomaly_res = self._detector.predict(
            machine_id=telemetry["machine_id"],
            temperature=telemetry["temperature"],
            vibration=telemetry["vibration"],
            speed=telemetry["speed"],
            load=telemetry["load"]
        )

        # Insert Telemetry
        cursor.execute("""
            INSERT INTO telemetry (
                message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            msg_id,
            telemetry["machine_id"],
            telemetry["timestamp"],
            telemetry["temperature"],
            telemetry["vibration"],
            telemetry["speed"],
            telemetry["load"],
            telemetry["status"],
            telemetry["production_count"],
            "MQTT_LIVE"
        ))
        telemetry_id = cursor.lastrowid

        # Insert Anomaly Prediction
        cursor.execute("""
            INSERT INTO anomaly_predictions (
                telemetry_id, machine_id, timestamp, anomaly_score, is_anomaly, risk_category, detection_method, suggested_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telemetry_id,
            telemetry["machine_id"],
            telemetry["timestamp"],
            anomaly_res["anomaly_score"],
            1 if anomaly_res["is_anomaly"] else 0,
            anomaly_res["risk_category"],
            anomaly_res["detection_method"],
            anomaly_res["suggested_action"]
        ))

        # Check machine status change
        cursor.execute("SELECT current_status FROM machines WHERE machine_id = ?", (telemetry["machine_id"],))
        m_row = cursor.fetchone()
        old_status = m_row["current_status"] if m_row else "RUNNING"
        new_status = telemetry["status"]

        if old_status != new_status:
            cursor.execute("UPDATE machines SET current_status = ? WHERE machine_id = ?", (new_status, telemetry["machine_id"]))
            cursor.execute("""
                INSERT INTO machine_status_history (machine_id, old_status, new_status, reason)
                VALUES (?, ?, ?, ?)
            """, (telemetry["machine_id"], old_status, new_status, "Status updated from Live MQTT telemetry"))

        conn.commit()
        conn.close()

        # Evaluate safety alerts
        evaluate_telemetry_for_alerts(telemetry, anomaly_res)

    def start(self):
        """Connect and start background MQTT event loop."""
        try:
            logger.info(f"Connecting MQTT subscriber to {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}...")
            self.client.connect(Config.MQTT_BROKER_HOST, Config.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to start MQTT subscriber: {e}")
            self.is_connected = False
            return False

    def stop(self):
        """Stop MQTT event loop and disconnect."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            logger.info("MQTT subscriber stopped.")
        except Exception as e:
            logger.error(f"Error stopping MQTT subscriber: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("Starting FactoryTwin MQTT Subscriber Worker...")
    sub = MQTTSubscriber()
    if sub.start():
        print(f"Subscriber active on topic: {TELEMETRY_SUBSCRIBE_TOPIC}")
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down subscriber...")
            sub.stop()
    else:
        print("Failed to connect to broker. Check configuration.")
