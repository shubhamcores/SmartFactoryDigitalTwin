# Stage 6: MQTT Industrial Communication & HiveMQ Guide (P_307)
## Topic Hierarchies, Cloud Broker Setup & MQTT Explorer Testing
**Standard**: OASIS MQTT v3.1.1 / v5.0 Specification  
**Default Topic Prefix**: `factory/machines/`

---

## 1. Overview of MQTT in Industrial IoT
MQTT (Message Queuing Telemetry Transport) is the de-facto standard publish-subscribe messaging protocol for Industrial IoT due to its minimal network bandwidth overhead, binary header efficiency (as small as 2 bytes), built-in Keep-Alive mechanisms, and support for Quality of Service (QoS) guarantees.

In FactoryTwin, MQTT enables:
- Physical edge nodes (such as the optional ESP32 DevKit) to push real-time sensor measurements into the platform over WiFi.
- Central SCADA ingestion decoupled from edge hardware.
- Optional multi-plant synchronization through cloud brokers like **HiveMQ Cloud**.

---

## 2. Topic Architecture

```
factory/
└── machines/
    ├── Motor/
    │   └── telemetry    <-- Real-time telemetry published by Motor edge node
    ├── Conveyor/
    │   └── telemetry    <-- Real-time telemetry published by Conveyor edge node
    ├── Pump/
    │   └── telemetry    <-- Real-time telemetry published by Pump edge node
    ├── CNC/
    │   └── telemetry    <-- Real-time telemetry published by CNC edge node
    └── alerts           <-- Broadcast emergency safety events
```

### Wildcard Subscription
The FactoryTwin background subscriber (`mqtt/subscriber.py`) listens on:
```
factory/machines/+/telemetry
```
The single-level wildcard `+` automatically captures incoming messages from any registered or newly deployed machine without modifying code.

---

## 3. Telemetry Payload Specification (JSON)

Every telemetry publish event must conform to the following JSON schema:

```json
{
  "message_id": "MQTT-Motor-1730000000",
  "machine_id": "Motor",
  "timestamp": "2026-11-01 10:15:30",
  "temperature": 64.8,
  "vibration": 1.72,
  "speed": 1748.0,
  "load": 65.2,
  "status": "RUNNING",
  "production_count": 240
}
```

### Data Dictionary & Physical Plausibility Limits

| Key | Type | Unit | Range / Constraints | Description |
| :--- | :--- | :---: | :---: | :--- |
| `message_id` | String | - | Alphanumeric (Unique) | Idempotent message tracking key for deduplication. |
| `machine_id` | String | - | Must exist in `Config.MACHINES` | Target equipment identifier. |
| `timestamp` | String | - | `YYYY-MM-DD HH:MM:SS` | UTC or local acquisition timestamp. |
| `temperature`| Float | °C | $-50.0$ to $+300.0$ | Surface or winding temperature. |
| `vibration` | Float | mm/s | $0.0$ to $100.0$ | ISO 10816 vibration velocity RMS. |
| `speed` | Float | RPM | $0.0$ to $15000.0$ | Shaft rotational speed. |
| `load` | Float | % | $0.0$ to $150.0$ | Electrical/mechanical load ratio. |
| `status` | String | - | `RUNNING`, `WARNING`, `CRITICAL`, `STOPPED`, `IDLE` | Edge-determined status. |
| `production_count`| Integer | Units | $\ge 0$ | Cumulative completed production units. |

---

## 4. HiveMQ Cloud Configuration Walkthrough

HiveMQ Cloud provides a free, highly reliable, enterprise-grade cloud MQTT broker supporting up to 100 concurrent devices with TLS 8883 encryption.

### Step 1: Create a Free HiveMQ Cloud Cluster
1. Navigate to [https://www.hivemq.com/mqtt-cloud-broker/](https://www.hivemq.com/mqtt-cloud-broker/) and sign up for a free "Serverless" tier account.
2. Click **Create Cluster**. Select AWS or Azure as the cloud host.
3. Once provisioned, note your cluster URL (e.g., `xxxxxxxx.s1.eu.hivemq.cloud`).

### Step 2: Configure Device Credentials
1. In your HiveMQ console, open the **Access Management** tab.
2. Add a new device credential:
   - **Username**: `factory_twin_device`
   - **Password**: `SecurePass@2026`
   - **Permissions**: Publish and Subscribe to `factory/#`.

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env` in the project root:
```ini
MQTT_ENABLED=True
MQTT_BROKER_HOST=xxxxxxxx.s1.eu.hivemq.cloud
MQTT_BROKER_PORT=8883
MQTT_USE_TLS=True
MQTT_USERNAME=factory_twin_device
MQTT_PASSWORD=SecurePass@2026
MQTT_TOPIC_PREFIX=factory/machines
```

---

## 5. Testing with MQTT Explorer (Step-by-Step)

[MQTT Explorer](https://mqtt-explorer.com/) is an indispensable graphical tool for visualizing topic trees, monitoring live telemetry, and injecting test payloads.

### Connection Setup in MQTT Explorer
1. Open MQTT Explorer on your computer.
2. Configure connection settings:
   - **Name**: `HiveMQ Cloud Test`
   - **Protocol**: `mqtts://` (for TLS) or `mqtt://` (for local Mosquitto)
   - **Host**: Your cluster host (e.g. `xxxxxxxx.s1.eu.hivemq.cloud`)
   - **Port**: `8883`
   - **Encryption (TLS)**: Enabled (`ON`)
   - **Username**: `factory_twin_device`
   - **Password**: `SecurePass@2026`
3. Click **Connect**.

### Publishing a Test Anomaly from MQTT Explorer
To simulate a physical bearing breakdown from outside the application:
1. In the **Publish** pane, enter the topic:
   ```
   factory/machines/Motor/telemetry
   ```
2. Select **raw** or **json** format.
3. Paste the following abnormal vibration payload:
   ```json
   {
     "message_id": "EXPLORER-TEST-001",
     "machine_id": "Motor",
     "temperature": 72.0,
     "vibration": 9.45,
     "speed": 1720.0,
     "load": 68.0,
     "status": "WARNING",
     "production_count": 500
   }
   ```
4. Click **Publish**.
5. Observe the FactoryTwin Central SCADA Dashboard:
   - The telemetry updates within 3 seconds.
   - The data source badge reflects `MQTT_LIVE`.
   - The AI Anomaly Risk Bar surges into `CRITICAL`.
   - A new `EXCESSIVE_VIBRATION` and `AI Anomaly` alert appears in the active alerts list!

---

## 6. Error Handling & Fault Containment Architecture
The FactoryTwin MQTT subscriber is engineered for industrial resilience:
1. **Network Interruption**: Uses Paho MQTT's automatic reconnection loop (`loop_start()`). When a WiFi router or broker restarts, the subscriber recovers seamlessly.
2. **Corrupted Payloads**: If a malformed string or invalid JSON arrives, `validate_telemetry_payload()` logs the error and safely drops the packet without crashing the server.
3. **QoS 1 Redelivery Protection**: The database checks `SELECT id FROM telemetry WHERE message_id = ?`. Repeated broker deliveries do not result in duplicate records.
4. **Offline Operation**: If `MQTT_ENABLED=False` or if the broker is unreachable, the system relies on the internal physics simulator with zero degradation in dashboard functionality.
