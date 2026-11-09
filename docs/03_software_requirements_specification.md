# Stage 3: Software Requirements Specification (SRS) 
## AI-Driven Digital Twin for Smart Factory Operations
**Standard**: IEEE 830-1998 Recommended Practice for SRS  
**Project Code**: P_307 | Version 1.0.0

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for the **FactoryTwin** smart factory monitoring platform. FactoryTwin provides continuous digital twin synchronization, multi-machine telemetry ingestion, unsupervised Machine Learning anomaly detection using Isolation Forest, hierarchical alert management, role-based SCADA access control, and executive reporting.

### 1.2 Scope of the System
The system monitors four critical industrial machinery classes:
1. `Motor`: Primary drive 3-phase induction motor (1750 RPM nominal).
2. `Conveyor`: Material handling belt conveyor system (450 RPM nominal).
3. `Pump`: Cooling circuit centrifugal water pump (2900 RPM nominal).
4. `CNC`: 5-axis precision milling machining center (2400 RPM nominal).

The core software operates completely standalone on Windows 10/11 with zero mandatory hardware or internet connection requirements. An optional MQTT module connects to local Mosquitto or cloud brokers (HiveMQ Cloud via TLS 8883), and an optional ESP32 edge node enables physical MEMS vibration acquisition.

---

## 2. User Roles and Access Control (RBAC)

The system defines two discrete user roles:

### 2.1 Administrator (`role = 'admin'`)
- Full visibility across all 4 machine assets and live charts.
- Access to plant configuration, simulation controls (start, stop, fault injection).
- User management: create new users, view credentials, assign roles.
- Alert management: both acknowledge and resolve alerts with corrective maintenance notes.
- Access to immutable system audit trails.
- On-demand CSV and executive PDF report exports.

### 2.2 Plant Operator (`role = 'operator'`)
- Central SCADA dashboard monitoring and asset detail inspection.
- Real-time telemetry visualization and trend inspection.
- Alert visibility and single-click alarm acknowledgement.
- Fault scenario testing via the demonstration injection panel.
- Export of operational reports for daily shift handover.
- **Restrictions**: Cannot create/delete users, view system audit logs, or resolve alerts (HTTP 403 Forbidden enforced on direct API/URL access).

---

## 3. Functional Requirements (FR)

### 3.1 Digital Twin Simulation & Telemetry Generation
- **FR-SIM-01**: The system shall generate synchronized telemetry every 2 to 5 seconds across all 4 monitored machinery assets.
- **FR-SIM-02**: Each telemetry record must contain: `message_id`, `machine_id`, `timestamp`, `temperature` (°C), `vibration` (mm/s), `speed` (RPM), `load` (%), `status` (RUNNING, WARNING, CRITICAL, IDLE, STOPPED), and cumulative `production_count`.
- **FR-SIM-03**: The simulator shall support 7 distinct operational regimes:
  1. `NORMAL`: Sensor values within certified baseline variance.
  2. `HIGH_TEMP`: Thermal rise beyond machine thermal rating (coolant failure).
  3. `HIGH_VIB`: Elevated vibration velocity exceeding ISO 10816 limits (bearing fault).
  4. `EXCESSIVE_LOAD`: High mechanical drag (>90% capacity) accompanied by speed sag (jam).
  5. `REDUCED_PRODUCTION`: Throttled operating speed with diminished unit increments.
  6. `STOPPAGE`: Emergency trip with immediate speed deceleration to 0.0 RPM.
  7. `ABNORMAL_SENSOR`: Transient wild readings representing electrical sensor glitch.
- **FR-SIM-04**: The system shall provide single-instance thread safety preventing duplicate simulation workers from launching concurrently.
- **FR-SIM-05**: The system shall clearly tag every telemetry record with its origin: `SIMULATED` vs `MQTT_LIVE` vs `ESP32_EDGE`.

### 3.2 MQTT Communication Layer
- **FR-MQTT-01**: The system shall subscribe to topic pattern `factory/machines/+/telemetry`.
- **FR-MQTT-02**: The system shall support TLS encryption (port 8883) for secure HiveMQ Cloud connectivity.
- **FR-MQTT-03**: The MQTT subscriber must validate payload JSON schema and reject out-of-bounds corrupt data safely without terminating the process.
- **FR-MQTT-04**: The subscriber shall perform deduplication on `message_id` before inserting records into SQLite.
- **FR-MQTT-05**: The web platform must continue operating seamlessly when MQTT is disabled or when the broker is offline.

### 3.3 Machine Learning & Anomaly Detection
- **FR-AI-01**: The system shall implement an unsupervised `IsolationForest` model trained strictly on normal operating telemetry (12,000 samples) with zero evaluation label leakage.
- **FR-AI-02**: The detector must accept 4 standardized input features: `temperature`, `vibration`, `speed`, and `load`.
- **FR-AI-03**: The model must output:
  - `is_anomaly`: Boolean indicator (True / False).
  - `anomaly_score`: Normalized continuous risk score between 0.0 and 100.0.
  - `risk_category`: Standardized industrial risk tiers: `LOW` (0–39.9), `MEDIUM` (40–64.9), `HIGH` (65–84.9), `CRITICAL` (85–100).
  - `detection_method`: Flagged as `ISOLATION_FOREST` or `RULE_BASED_FALLBACK`.
  - `suggested_action`: Engineering maintenance recommendation based on dominant feature deviations.
- **FR-AI-04**: The system shall provide a deterministic rule-based fallback if the trained model file is unavailable.
- **FR-AI-05**: The system documentation must explicitly declare that the Isolation Forest score indicates statistical outlier depth, not a calibrated probability of failure.

### 3.4 Alerts and Health Monitoring
- **FR-ALT-01**: The system shall evaluate telemetry against machine thresholds and AI risk classifications in real time.
- **FR-ALT-02**: The system shall trigger alerts for:
  - `EXCESSIVE_TEMPERATURE` (Warning if > max_temp; Critical if > max_temp + 10°C).
  - `EXCESSIVE_VIBRATION` (Warning if > max_vib; Critical if > max_vib + 2.0 mm/s).
  - `OVERLOAD` (Warning if > max_load; Critical if $\ge 98\%$).
  - `UNEXPECTED_STOPPAGE` (Critical if speed < 10 RPM while non-idle).
  - `ANOMALY_DETECTED` (Warning if High risk; Critical if Critical risk).
- **FR-ALT-03**: The system shall enforce an alert cooldown window (default 60 seconds) per machine/alert_type to eliminate alarm storms.
- **FR-ALT-04**: The system shall support transition through alert states: `NEW` $\to$ `ACKNOWLEDGED` (Operator/Admin) $\to$ `RESOLVED` (Admin only).

### 3.5 Operational Reporting
- **FR-REP-01**: The system shall provide filterable reports for:
  1. Machine Telemetry Stream
  2. Production Output & Efficiency
  3. Machine State Transitions
  4. AI Anomaly Predictions & Risk
  5. Safety & Maintenance Alarms
  6. Executive Daily Factory Summary
- **FR-REP-02**: The system shall export CSV files formatted with UTF-8 BOM (`\xef\xbb\xbf`) for native Microsoft Excel compatibility.
- **FR-REP-03**: The system shall generate multi-page executive PDF reports using ReportLab with custom "Page X of Y" canvas numbering, summary metadata, and tabular styles.

---

## 4. Non-Functional Requirements (NFR)

### 4.1 Performance & Latency
- **NFR-PERF-01**: REST API response latency for `/api/telemetry/latest` shall remain below 100 milliseconds under standard single-user monitoring.
- **NFR-PERF-02**: Ingestion pipeline shall process and persist telemetry, run AI inference, and evaluate alerts in under 30 milliseconds per reading.

### 4.2 Reliability & Availability
- **NFR-REL-01**: SQLite shall operate with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) to ensure zero-lock concurrency between background simulation ingestion and foreground dashboard read requests.
- **NFR-REL-02**: Malformed MQTT messages, database locks, or unexpected exceptions shall be contained within try-except blocks with zero unhandled crashes.

### 4.3 Security & Session Protection
- **NFR-SEC-01**: User passwords must be hashed using cryptographic algorithms (`scrypt` or `pbkdf2:sha256`) via Werkzeug security primitives. Plaintext passwords shall never be persisted.
- **NFR-SEC-02**: Session cookies must be protected with `HttpOnly=True` and `SameSite='Lax'` flags.
- **NFR-SEC-03**: All administrative mutations and authentication attempts must be recorded into the SQLite `audit_logs` table.

### 4.4 Portability & Simplicity
- **NFR-PORT-01**: The codebase shall execute on Windows 10 and Windows 11 using Python 3.12 without requiring compilation of external C++ extensions or third-party web servers.
- **NFR-PORT-02**: The platform must execute directly from the project root without modifying system environment paths.

---

## 5. System Constraints
1. **Operating System**: Windows 10/11 64-bit architecture.
2. **Runtime**: Python 3.12.x.
3. **Storage Engine**: SQLite 3 embedded database.
4. **Network**: Fully functional offline; Internet connection needed only if connecting to remote HiveMQ Cloud.
5. **Browser Compatibility**: Google Chrome, Microsoft Edge, Mozilla Firefox (Modern HTML5/ES6 support).
