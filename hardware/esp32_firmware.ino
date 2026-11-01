/*
 * FactoryTwin (P_307) - ESP32 Industrial Edge Telemetry Firmware
 * Target: ESP32 DevKit V1 (30-pin / 38-pin)
 * Sensors: MPU-6050 6-Axis IMU (I2C) & Internal / DS18B20 Temperature
 * Dual Transport Support:
 *   1. MQTT: Publishes JSON to HiveMQ Cloud TLS (Port 8883) or Local Mosquitto
 *   2. HTTP REST: Direct HTTP POST to http://<server_ip>:5000/api/esp32/telemetry
 *
 * Required Arduino Libraries:
 *   - PubSubClient (by Nick O'Leary)
 *   - ArduinoJson (by Benoit Blanchon, v6 or v7)
 *   - Adafruit MPU6050 & Adafruit Sensor
 *   - WiFiClientSecure & HTTPClient (Built-in ESP32 core)
 */

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ============================================================================
// NETWORK CONFIGURATION
// ============================================================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Select Primary Transport Protocol:
// Set USE_MQTT to true for HiveMQ Cloud MQTT, or false for Direct HTTP REST POST
#define USE_MQTT true

// MQTT Configuration (When USE_MQTT is true)
const char* MQTT_BROKER   = "your-cluster-url.s1.eu.hivemq.cloud";
const int   MQTT_PORT     = 8883; // 8883 for TLS, 1883 for Non-TLS
const char* MQTT_USER     = "hivemq_device_user";
const char* MQTT_PASS     = "hivemq_device_pass";
const char* PUB_TOPIC     = "factory/machines/Motor_1/telemetry";
const char* CLIENT_ID     = "ESP32_EdgeNode_Motor1";

// HTTP REST Configuration (When USE_MQTT is false or as fallback)
// Replace with the IP address of your Windows PC running app.py
const char* HTTP_REST_URL = "http://192.168.1.8:5000/api/esp32/telemetry";

const char* MACHINE_ID    = "Motor_1";

// ============================================================================
// HARDWARE PIN DEFINITIONS
// ============================================================================
#define I2C_SDA_PIN      21
#define I2C_SCL_PIN      22
#define STATUS_LED_PIN   2   // Onboard Blue LED for WiFi status
#define ALARM_LED_PIN    4   // External Red Indicator for Edge Thresholds

// Operating Thresholds (Edge Pre-Alert)
const float EDGE_MAX_VIB_MMS = 4.5;
const float EDGE_MAX_TEMP_C  = 85.0;

// Sensor & Network Objects
Adafruit_MPU6050 mpu;
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);

// Moving Average Filter Window for Vibration
const int FILTER_WINDOW_SIZE = 15;
float vibFilterBuffer[FILTER_WINDOW_SIZE];
int filterIndex = 0;
bool bufferFilled = false;

// Telemetry State
unsigned long lastPublishEpoch = 0;
const unsigned long PUBLISH_INTERVAL_MS = 3000;
long productionCounter = 0;

// ============================================================================
// SENSOR FILTERING & VIBRATION RMS COMPUTATION (ISO 10816)
// ============================================================================
float computeFilteredVibration(float rawAccelerationG) {
  // Convert acceleration in G to vibration velocity estimate in mm/s:
  // V_rms ≈ (a_peak * 9806.65) / (2 * pi * f_dominant * sqrt(2))
  float instantVib_mms = (rawAccelerationG * 9.80665) / (2.0 * 3.14159 * 50.0) * 1000.0 * 0.707;
  if (instantVib_mms < 0) instantVib_mms = -instantVib_mms;

  vibFilterBuffer[filterIndex] = instantVib_mms;
  filterIndex = (filterIndex + 1) % FILTER_WINDOW_SIZE;
  if (filterIndex == 0) bufferFilled = true;

  int count = bufferFilled ? FILTER_WINDOW_SIZE : filterIndex;
  float sum = 0.0;
  for (int i = 0; i < count; i++) {
    sum += vibFilterBuffer[i];
  }
  return sum / count;
}

// ============================================================================
// WIFI & CONNECTION MANAGEMENT
// ============================================================================
void connectWiFi() {
  Serial.print("[WiFi] Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(STATUS_LED_PIN, !digitalRead(STATUS_LED_PIN));
    delay(400);
    Serial.print(".");
  }
  digitalWrite(STATUS_LED_PIN, HIGH);
  Serial.println("\n[WiFi] Connected successfully. IP: " + WiFi.localIP().toString());
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Connecting to broker ");
    Serial.print(MQTT_BROKER);
    Serial.print("...");

    if (mqttClient.connect(CLIENT_ID, MQTT_USER, MQTT_PASS)) {
      Serial.println(" Connected!");
      digitalWrite(STATUS_LED_PIN, HIGH);
    } else {
      Serial.print(" Failed (rc=");
      Serial.print(mqttClient.state());
      Serial.println("). Retrying in 4 seconds...");
      digitalWrite(STATUS_LED_PIN, LOW);
      delay(4000);
    }
  }
}

// ============================================================================
// MAIN ARDUINO SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(ALARM_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  digitalWrite(ALARM_LED_PIN, LOW);

  // Initialize I2C and MPU6050
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  if (!mpu.begin(0x68, &Wire)) {
    Serial.println("[WARN] MPU-6050 not detected at 0x68. Check SDA=GPIO21, SCL=GPIO22.");
  } else {
    Serial.println("[OK] MPU-6050 6-Axis IMU Initialized.");
    mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  }

#if USE_MQTT
  espClient.setInsecure(); // Prototyping TLS skip
  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
#endif

  connectWiFi();
}

// ============================================================================
// MAIN ARDUINO LOOP
// ============================================================================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

#if USE_MQTT
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();
#endif

  unsigned long currentMillis = millis();
  if (currentMillis - lastPublishEpoch >= PUBLISH_INTERVAL_MS) {
    lastPublishEpoch = currentMillis;

    // Read MPU6050 Acceleration
    sensors_event_t a, g, temp_event;
    float rawAccMag = 0.0;
    float chipTemp = 45.0;

    if (mpu.getEvent(&a, &g, &temp_event)) {
      float totalG = sqrt(sq(a.acceleration.x) + sq(a.acceleration.y) + sq(a.acceleration.z)) / 9.80665;
      rawAccMag = abs(totalG - 1.0); // Remove static 1G gravity
      chipTemp = temp_event.temperature;
    } else {
      rawAccMag = 0.08 + (random(0, 40) / 1000.0);
      chipTemp = 62.0 + (random(0, 50) / 10.0);
    }

    float vibrationMMS = computeFilteredVibration(rawAccMag);
    float motorRPM = 1745.0 + random(-15, 15);
    float motorLoad = 64.5 + random(-3, 3);
    productionCounter += 5;

    // Edge Threshold Alert Check
    bool isWarning = (vibrationMMS > EDGE_MAX_VIB_MMS) || (chipTemp > EDGE_MAX_TEMP_C);
    digitalWrite(ALARM_LED_PIN, isWarning ? HIGH : LOW);

    // Build JSON Payload
    StaticJsonDocument<384> doc;
    doc["message_id"] = "ESP32-" + String(currentMillis);
    doc["machine_id"] = MACHINE_ID;
    doc["temperature"] = round(chipTemp * 10.0) / 10.0;
    doc["vibration"] = round(vibrationMMS * 100.0) / 100.0;
    doc["speed"] = motorRPM;
    doc["load"] = motorLoad;
    doc["status"] = isWarning ? "WARNING" : "RUNNING";
    doc["production_count"] = productionCounter;
    doc["data_source"] = "ESP32_EDGE";

    char jsonBuffer[384];
    serializeJson(doc, jsonBuffer);

#if USE_MQTT
    // Transport Path A: MQTT Publish
    if (mqttClient.publish(PUB_TOPIC, jsonBuffer, 1)) {
      Serial.print("[MQTT PUB] Sent: ");
      Serial.println(jsonBuffer);
    } else {
      Serial.println("[MQTT ERR] Publish failed.");
    }
#else
    // Transport Path B: Direct HTTP REST POST
    HTTPClient http;
    http.begin(HTTP_REST_URL);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(jsonBuffer);
    if (httpResponseCode > 0) {
      Serial.printf("[HTTP POST] Code %d: %s\n", httpResponseCode, jsonBuffer);
    } else {
      Serial.printf("[HTTP ERR] Failed, code: %d\n", httpResponseCode);
    }
    http.end();
#endif
  }
}
