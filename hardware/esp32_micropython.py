"""
FactoryTwin (P_307) - ESP32 MicroPython Industrial Edge Telemetry
Alternative firmware implementation for MicroPython runtime on ESP32 DevKit.
"""

import time
import math
import machine
import network
import ujson
from umqtt.simple import MQTTClient

# Configuration
WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASS = "YOUR_WIFI_PASSWORD"

MQTT_BROKER = "your-cluster-url.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "hivemq_device_user"
MQTT_PASS = "hivemq_device_pass"
CLIENT_ID = "ESP32_MicroPython_Motor1"
PUB_TOPIC = b"factory/machines/Motor_1/telemetry"

# Pin Configuration
I2C_SDA_PIN = 21
I2C_SCL_PIN = 22
STATUS_LED_PIN = 2
ALARM_LED_PIN = 4

status_led = machine.Pin(STATUS_LED_PIN, machine.Pin.OUT)
alarm_led = machine.Pin(ALARM_LED_PIN, machine.Pin.OUT)

# I2C Initialization
i2c = machine.I2C(0, scl=machine.Pin(I2C_SCL_PIN), sda=machine.Pin(I2C_SDA_PIN), freq=400000)

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("[WiFi] Connecting...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            status_led.value(not status_led.value())
            time.sleep(0.3)
    status_led.value(1)
    print("[WiFi] Connected:", wlan.ifconfig())

def main():
    connect_wifi()

    client = MQTTClient(
        client_id=CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASS,
        ssl=True
    )

    try:
        print("[MQTT] Connecting to broker...")
        client.connect()
        print("[MQTT] Connected successfully.")
    except Exception as e:
        print("[MQTT] Connection failed:", e)

    prod_counter = 0

    while True:
        try:
            prod_counter += 5
            # Synthetic physical calculation
            temp = 63.5
            vib = 1.72
            speed = 1750.0
            load = 65.0

            payload = {
                "message_id": f"ESP32-UPY-{time.time()}",
                "machine_id": "Motor_1",
                "temperature": temp,
                "vibration": vib,
                "speed": speed,
                "load": load,
                "status": "RUNNING",
                "production_count": prod_counter,
                "data_source": "ESP32_EDGE"
            }

            msg = ujson.dumps(payload).encode("utf-8")
            client.publish(PUB_TOPIC, msg)
            print("[PUB]", msg)
        except Exception as e:
            print("[ERR] Error in publish loop:", e)

        time.sleep(3)

if __name__ == "__main__":
    main()
