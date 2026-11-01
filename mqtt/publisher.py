"""
MQTT Publisher Service for FactoryTwin (P_307)
Publishes real-time telemetry from machines or simulated edge nodes to the MQTT broker
(Supports local Mosquitto or HiveMQ Cloud TLS).
"""

import sys
import ssl
import time
import json
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from config import Config
from mqtt.config import get_machine_telemetry_topic

logger = logging.getLogger(__name__)

class MQTTPublisher:
    """Manages connection and message dispatching to an MQTT broker."""

    def __init__(self):
        self.client_id = f"{Config.MQTT_CLIENT_ID_PREFIX}-Pub-{int(time.time())}"
        # Paho MQTT 2.x callback API version compatibility
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id
            )
        except AttributeError:
            self.client = mqtt.Client(client_id=self.client_id)

        self.is_connected = False
        self._setup_client()

    def _setup_client(self):
        """Configure credentials, TLS, and connection callbacks."""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        if Config.MQTT_USERNAME and Config.MQTT_PASSWORD:
            self.client.username_pw_set(Config.MQTT_USERNAME, Config.MQTT_PASSWORD)

        if Config.MQTT_USE_TLS:
            context = ssl.create_default_context()
            self.client.tls_set_context(context)
            logger.info("Configured TLS for HiveMQ Cloud connectivity")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = getattr(rc, "value", rc)
        if rc_code == 0:
            self.is_connected = True
            logger.info(f"[MQTT] Publisher connected successfully to {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}")
        else:
            self.is_connected = False
            logger.error(f"[MQTT] Publisher connection failed with return code: {rc_code}")

    def _on_disconnect(self, client, userdata, rc, properties=None, reason_code=None):
        self.is_connected = False
        logger.warning(f"[MQTT] Publisher disconnected from broker (rc={rc})")

    def connect(self):
        """Connect to configured MQTT broker."""
        try:
            logger.info(f"Connecting to MQTT broker at {Config.MQTT_BROKER_HOST}:{Config.MQTT_BROKER_PORT}...")
            self.client.connect(Config.MQTT_BROKER_HOST, Config.MQTT_BROKER_PORT, keepalive=60)
            self.client.loop_start()
            # Wait briefly for connection handshake
            time.sleep(1.0)
            return True
        except Exception as e:
            logger.error(f"[MQTT] Failed to establish broker connection: {e}")
            self.is_connected = False
            return False

    def publish_telemetry(self, machine_id: str, telemetry: dict) -> bool:
        """Publish JSON telemetry to factory/machines/<machine_id>/telemetry."""
        if not self.is_connected:
            return False

        topic = get_machine_telemetry_topic(machine_id)
        payload = json.dumps(telemetry)
        try:
            res = self.client.publish(topic, payload, qos=1)
            return res.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Failed to publish telemetry to {topic}: {e}")
            return False

    def disconnect(self):
        """Gracefully disconnect from broker."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error during MQTT disconnect: {e}")

if __name__ == "__main__":
    print("Testing FactoryTwin MQTT Publisher...")
    pub = MQTTPublisher()
    if pub.connect():
        sample_payload = {
            "message_id": f"TEST-{int(time.time())}",
            "machine_id": "Motor_1",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": 65.4,
            "vibration": 1.75,
            "speed": 1748.0,
            "load": 64.2,
            "status": "RUNNING",
            "production_count": 120
        }
        success = pub.publish_telemetry("Motor_1", sample_payload)
        print(f"Published test message to Motor_1: {success}")
        time.sleep(2)
        pub.disconnect()
    else:
        print("Could not connect to broker. Verify MQTT broker host/credentials in .env")
