# Hardware Troubleshooting & Setup Diagnostics 

## 1. Common Hardware Assembly Issues & Solutions

### A. MPU-6050 Not Detected by ESP32 (`mpu.begin()` returns false)
- **Symptom**: Serial monitor prints `[WARN] MPU-6050 not detected at 0x68`.
- **Causes & Fixes**:
  1. **Incorrect I2C Wiring**: Verify SDA is on GPIO 21 and SCL is on GPIO 22.
  2. **I2C Address Conflict**: Check pin **AD0** on the MPU-6050 module. If AD0 is connected to 3.3V or left floating with pull-up, its address changes to `0x69`. Connect AD0 to GND to enforce address `0x68`.
  3. **Insufficient Power**: Ensure VCC is receiving 3.3V or 5V (if the module has an AMS1117 3.3V on-board regulator).
  4. **Run I2C Scanner**: Upload standard Arduino I2C Scanner sketch to detect active addresses on the bus.

### B. WiFi Connection Loops or Fails
- **Symptom**: ESP32 continuously prints dots `.....` on the Serial Monitor.
- **Causes & Fixes**:
  1. **5 GHz WiFi Incompatibility**: ESP32 DevKit only supports **2.4 GHz WiFi**. Ensure your mobile hotspot or router has a 2.4 GHz channel enabled.
  2. **Captive Portals**: ESP32 cannot handle institutional campus logins (e.g. college WiFi requiring browser authentication). Use a personal 2.4 GHz mobile hotspot for laboratory demonstrations.

### C. HiveMQ Cloud MQTT TLS Handshake Failure
- **Symptom**: `[MQTT] Connecting to broker... Failed (rc=-2)` (where `-2` indicates client connection refused or TLS handshake failed).
- **Causes & Fixes**:
  1. **Port Selection**: HiveMQ Cloud requires port `8883` with TLS enabled. Port 1883 will be rejected.
  2. **Credentials Missing**: Verify username and password created under your HiveMQ Cloud Cluster "Access Management" tab.
  3. **Certificate Check**: Prototyping firmware uses `espClient.setInsecure()` to skip root CA validation. For production, load HiveMQ's DigiCert Global Root CA PEM certificate into `espClient.setCACert(root_ca)`.

---

## 2. Laboratory Test Verification Record
- **Firmware Syntax Validation**: Arduino C++ firmware and MicroPython script verified against standard ESP32 SDK libraries.
- **Hardware Separation**: The software simulator functions completely independently of hardware. If no ESP32 is present, the digital twin operates seamlessly using internal physics modeling.
