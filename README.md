# FactoryTwin: AI-Driven Digital Twin for Smart Factory Operations 

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1.3-000000.svg?logo=flask&logoColor=white)](https://palletsprojects.com/p/flask/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation_Forest-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite_WAL-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![MQTT](https://img.shields.io/badge/MQTT-HiveMQ_Cloud-FF6600.svg?logo=hivemq&logoColor=white)](https://www.hivemq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 32 Passed](https://img.shields.io/badge/Tests-32%2F32%20Passed-brightgreen.svg)](tests/test_results.txt)

> **BTech Individual Capstone Project**  
> Developed under the **HCLTech Project Creation Guide for Embedded Systems & IoT**.  
> Engineered and validated for seamless operation on **Windows 10 / 11** using **VS Code** and **Python 3.12**.

---

## 1. Executive Summary & Problem Context

In modern smart manufacturing plants, critical rotary and electromechanical assets—such as main drive induction motors, material handling belt conveyors, coolant centrifugal pumps, and 5-axis CNC machining centers—operate under extreme physical duty cycles. Unscheduled downtime caused by thermal runaway, bearing wear, mechanical jams, and tool fatigue costs industrial facilities between **\$50,000 and \$250,000 per hour**. 

Conventional maintenance strategies are polarized:
- **Reactive (Run-to-Failure)**: Triggers catastrophic secondary component destruction and extended emergency line outages.
- **Calendar-Based Preventive**: Incurs massive labor overhead and replaces healthy components prematurely.

**FactoryTwin** bridges this gap as an end-to-end cyber-physical **Digital Twin** and **Industrial IoT (IIoT)** platform. It models continuous machine physics in software, captures multi-channel sensor telemetry, runs real-time unsupervised machine learning for predictive anomaly detection, and provides industrial plant operators with an interactive, dark-mode SCADA operations console.

---

## 2. Key Platform Capabilities

1. **Multi-Asset Digital Twin Physics Engine**:
   - Continuously simulates 4 core manufacturing assets (`Motor`, `Conveyor`, `Pump`, `CNC`) with thermodynamic heat dissipation, rotational inertia, mechanical load curves, and production item increments.
   - Supports **7 distinct operational regimes** (Normal, High Temperature, High Vibration, Excessive Load, Reduced Production, Emergency Stoppage, and Sensor Faults).
2. **Unsupervised AI Anomaly Detection**:
   - Embedded **Scikit-Learn Isolation Forest** pipeline trained on 12,000 normal operating data points to identify multivariate outliers without requiring rare historical failure datasets.
   - Continuous decision score mapping into standardized industrial risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) with automatic diagnostic maintenance guidance.
   - Deterministic rule-based fallback detector to guarantee uninterrupted zero-downtime safety inference if model binaries are absent.
3. **Sub-Millisecond SCADA Synchronization (<1ms)**:
   - High-performance SQLite database operating in **Write-Ahead Logging (WAL)** mode.
   - Optimized compound B-Tree indexes (`idx_telemetry_machine_id_id`, `idx_anomaly_telemetry_id`) eliminating full-table scans and accelerating polling latency from ~178 seconds down to **<0.001 seconds**.
4. **Intelligent Alarm Management & Fatigue Suppression**:
   - In-memory 60-second cooldown deduplication preventing alert storms during sustained physical threshold violations.
   - Complete formal alarm lifecycle: `NEW` $\to$ `ACKNOWLEDGED` $\to$ `RESOLVED`.
5. **Dual Data Source Ingestion (Simulator vs. ESP32 Edge)**:
   - Switch any individual machine or all machines globally between internal physics simulation and live hardware edge ingestion via HTTP REST or MQTT.
6. **Role-Based Access Control (RBAC)**:
   - Dual-tiered permissions separating **Plant Operators** (monitoring, inspections, alert acknowledgement, fault injection) from **System Administrators** (user administration, simulator process control, audit trail inspection).
7. **Automated Industrial Reporting**:
   - Single-click dynamic data export in Excel-compatible **UTF-8 BOM CSV** format and executive **ReportLab PDF** documents with tabular summaries and diagnostic KPI charts.

---

## 3. Cyber-Physical System Architecture

```
+-----------------------------------------------------------------------------------+
|                            PHYSICAL & SIMULATED EDGE                              |
|                                                                                   |
|   [ ESP32 Edge Node + MPU-6050 ]          [ Digital Twin Physics Simulator ]     |
|         (Physical Sensor)                        (4 Virtual Industrial Assets)    |
+-----------------------------------------------------------------------------------+
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [ HTTP REST Ingestion API ]                     [ MQTT Client / Broker ]
     (POST /api/esp32/telemetry)                    (HiveMQ Cloud TLS Port 8883)
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
+-----------------------------------------------------------------------------------+
|                               FLASK BACKEND & CORE                                |
|                                                                                   |
|   • Schema Validation & Deduplication (Message-ID Uniqueness Check)               |
|   • AI Inference Pipeline (Scikit-Learn Isolation Forest + StandardScaler)         |
|   • Industrial Safety Rules & 60s Alert Cooldown Deduplication Engine             |
|   • Dynamic Data Source Router (SYNTHETIC vs ESP32_EDGE)                          |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        SQLITE PERSISTENCE (WAL & INDEXED)                         |
|                                                                                   |
|   • telemetry                     • anomaly_predictions                           |
|   • machines                      • alerts                                        |
|   • maintenance_records           • audit_logs                                    |
|   • High-Performance B-Tree Indexes (Sub-millisecond query execution)             |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                            CENTRAL SCADA WEB INTERFACE                            |
|                                                                                   |
|   • Real-Time Dashboard (3s Asynchronous Polling, Chart.js Time-Series Trends)   |
|   • Machine Twin Inspector (Detailed Thermodynamics & Component Diagnostics)      |
|   • Interactive Fault Simulator Modal (Inject 7 Regimes Live)                     |
|   • RBAC Administration (User Management, Audit Logs, Alarm Resolution)           |
|   • Export Subsystem (Excel UTF-8 BOM CSV & ReportLab Executive PDF Generation)   |
+-----------------------------------------------------------------------------------+
```

---

## 4. Directory Structure

```
SmartFactoryDigitalTwin/
├── ai_model/                         # Machine Learning Pipeline
│   ├── generate_dataset.py          # Synthetic dataset generator (Normal & Anomaly sets)
│   ├── isolation_forest_model.joblib # Serialized Scikit-Learn Isolation Forest binary
│   ├── model_metrics.json           # Formal precision, recall, and F1 evaluation report
│   ├── predict.py                   # Real-time anomaly detector & rule-based fallback
│   ├── scaler.joblib                # Fitted StandardScaler feature transformer
│   └── train_model.py               # Unsupervised model training & test evaluation
├── data/                            # Raw Datasets
│   ├── normal_training_data.csv     # 12,000 normal telemetry samples (zero leakage)
│   └── anomaly_evaluation_data.csv  # 3,000 labeled test evaluation samples (15% anomalies)
├── docs/                            # HCLTech 12-Stage Comprehensive Documentation
│   ├── 01_problem_statement.md      # Industrial context, cost of downtime & objectives
│   ├── 02_project_planning.md       # 25-day milestone Gantt roadmap & deliverables
│   ├── 03_software_requirements_specification.md # Formal IEEE 830 SRS specification
│   ├── 04_system_design_and_architecture.md      # C4 architecture, data flows & sequence diagrams
│   ├── 05_database_schema.md        # Relational ER schema, tables, constraints & indexes
│   ├── 06_mqtt_guide_and_hivemq.md  # MQTT topic hierarchy, QoS & TLS setup guide
│   ├── 07_bill_of_materials.md      # Physical hardware component BOM in INR (~₹1,127)
│   ├── 08_test_documentation.md     # 32-test verification matrix & actual execution results
│   ├── 09_user_manual.md            # Operator & Administrator dashboard user guide
│   ├── 10_project_report.md         # Formal academic project report for university submission
│   ├── 11_presentation.md           # 15-slide technical presentation transcript
│   ├── 12_demo_script.md            # Live evaluation demonstration protocol & viva guide
│   ├── generate_presentation.py     # Python-pptx generator for PowerPoint deck
│   └── presentation.pptx            # Compiled presentation slide deck
├── hardware/                        # Physical Microcontroller Firmwares
│   ├── bom.md                       # Bill of materials and Indian supplier links
│   ├── calibration_guide.md         # MPU-6050 accelerometer calibration & zero-offset guide
│   ├── circuit_diagram.md           # Fritzing breadboard schematics & I2C pin mappings
│   ├── esp32_firmware.ino           # Arduino C++ firmware (WiFi, I2C IMU, MQTT/HTTP)
│   ├── esp32_micropython.py         # MicroPython edge firmware alternative
│   └── troubleshooting.md           # Common hardware edge issues & wiring fixes
├── mqtt/                            # Industrial MQTT Subsystem
│   ├── config.py                    # MQTT topic templates, TLS settings & payload validation
│   ├── publisher.py                 # Telemetry publisher utility for hardware edge nodes
│   └── subscriber.py                # Background MQTT listener worker thread
├── reports/                         # Generated Reports Directory
│   └── generated/                   # PDF and CSV exports generated by users
├── services/                        # Business Logic & Infrastructure Services
│   ├── alert_service.py             # Safety limits, cooldown tracking & alert lifecycle
│   ├── audit_service.py             # Security auditing & administrator action logging
│   ├── auth_service.py              # Password hashing, PBKDF2 verification & session management
│   ├── esp32_service.py             # Hardware edge telemetry validation & ingestion
│   └── report_service.py            # UTF-8 BOM CSV & ReportLab PDF report generation
├── simulation/                      # Cyber-Physical Simulation Engine
│   └── simulator.py                 # Physics dynamics, thermal inertia, fault injection & thread safety
├── static/                          # Web Static Assets
│   ├── css/
│   │   └── styles.css               # SCADA dark-mode design system & industrial widgets
│   └── js/
│       ├── dashboard.js             # Real-time polling, Chart.js time-series & DOM updates
│       └── machine_detail.js        # Twin Inspector real-time single-machine telemetry graphs
├── templates/                       # Jinja2 HTML5 Templates
│   ├── admin_audit.html             # System administrator security audit log viewer
│   ├── admin_users.html             # Role-based user accounts management console
│   ├── alerts.html                  # Plant alert feed, filtering, acknowledgement & resolution
│   ├── base.html                    # Global navigation, SCADA header & fault injection modals
│   ├── dashboard.html               # Main SCADA operational dashboard & 4-machine twin grid
│   ├── login.html                   # Secure login portal with role-based redirection
│   ├── machine_detail.html          # Individual machine asset twin diagnostic inspection
│   └── reports.html                 # Custom date/asset query filters & report export center
├── tests/                           # Formal Test Harness (Python unittest)
│   ├── run_tests.py                 # Master test discovery & execution runner
│   ├── test_ai_model.py             # Isolation forest inference, risk tiers & fallback tests
│   ├── test_alerts.py               # Alert evaluation, 60s cooldown & lifecycle tests
│   ├── test_api_and_auth.py         # Flask REST API endpoints, RBAC permissions & session tests
│   ├── test_database.py             # SQLite tables, indexes, seeding & deduplication tests
│   ├── test_mqtt.py                 # JSON payload validation, schema bounds & rejection tests
│   ├── test_reports.py              # CSV UTF-8 BOM & ReportLab PDF binary generation tests
│   ├── test_results.txt             # Permanent archive of formal test execution results
│   └── test_simulation.py           # Physics state updates, boundary clamps & fault injection tests
├── .env.example                     # Environment variables configuration template
├── .gitignore                       # Git exclusion rules
├── app.py                           # Central Flask application factory & REST controllers
├── config.py                        # Unified application configuration & machine registry
├── database.py                      # SQLite database schema, connections & seed data
├── requirements.txt                 # Core Python production dependencies
├── requirements-mqtt.txt            # Optional MQTT client libraries (paho-mqtt)
└── README.md                        # Master Project Documentation
```

---

## 5. Monitored Industrial Assets

FactoryTwin models four primary factory machine assets with continuous engineering telemetry:

| Machine ID | Asset Name | Machine Type | Nominal Speed | Thermal Safety Limit | Vibration Limit (ISO 10816) | Max Mechanical Load | Nominal Output |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`Motor`** | Main Drive Induction Motor | 3-Phase Electric Motor | 1750 RPM | **85.0 °C** | **4.5 mm/s** | 90.0 % | 5 units/cycle |
| **`Conveyor`**| Material Transfer Conveyor | Industrial Belt Conveyor | 450 RPM | **70.0 °C** | **3.8 mm/s** | 85.0 % | 12 units/cycle |
| **`Pump`** | Cooling Circuit Pump | Centrifugal Water Pump | 2900 RPM | **80.0 °C** | **5.0 mm/s** | 92.0 % | 8 units/cycle |
| **`CNC`** | 5-Axis Milling Center | High-Precision CNC Mill | 2400 RPM | **90.0 °C** | **5.5 mm/s** | 95.0 % | 2 units/cycle |

### 7 Supported Operational Regimes

Operators can test how the digital twin and machine learning models react by injecting simulated faults using the **Fault Simulator** modal:

| Regime Code | Name | Physical Symptoms | Operational Effect |
| :--- | :--- | :--- | :--- |
| `NORMAL` | Certified Nominal | Parameters within baseline limits ($\pm 2\%$) | Normal operations, zero alarms |
| `HIGH_TEMP` | Thermal Overheat | Temp escalates toward 95–110 °C | Cooling failure, thermal runaway risk |
| `HIGH_VIB` | Mechanical Vibration | Vibration spikes to 6.5–9.5 mm/s | Bearing race pitting, rotor unbalance |
| `EXCESSIVE_LOAD` | Mechanical Jam | Load reaches 92–98%, speed drops | Motor stall risk, excessive current draw |
| `REDUCED_PRODUCTION` | Line Starvation | Speed drops to ~40% nominal | Sub-optimal throughput, feed bottleneck |
| `STOPPAGE` | Emergency Stop | Speed instantly drops to 0.0 RPM | Line halted, production increments freeze |
| `ABNORMAL_SENSOR` | Electrical Glitch | High-frequency random sensor spikes | Signal noise, transient electrical fault |

---

## 6. Machine Learning Pipeline (Isolation Forest)

```
[ Telemetry Input Vector ] ──> [ StandardScaler ] ──> [ Isolation Forest (150 Trees) ]
(Temp, Vib, RPM, Load)         (Trained on Normal)     (Unsupervised Multivariate Scoring)
                                                                 │
                                                                 ▼
[ Actionable Guidance ] <── [ Risk Tier Classification ] <── [ Score Normalization ]
(Bearing / Thermal / Jam)   (LOW, MEDIUM, HIGH, CRITICAL)    (Continuous 0.0 – 100.0)
```

1. **Training Methodology**:
   - Fitted **strictly on normal operating telemetry (12,000 samples)** generated without failure states.
   - Evaluated against a separate, independent **3,000-sample test set** containing 15% ground truth labeled anomalies (`overheat`, `bearing_fault`, `mechanical_jam`, `sensor_spike`, `compound_failure`).
2. **Evaluation Metrics**:
   - **Recall (Sensitivity)**: **89.73%** (Detects ~9 out of 10 anomalous states).
   - **Precision**: **72.83%** (Minimizes false alarms on standard transients).
   - **F1-Score**: **80.40%** (Balanced harmonic mean).
   - **False Positive Rate (FPR)**: **5.88%** (Safely below the industrial 7% nuisance alarm threshold).
3. **Risk Tier Normalization**:
   - The continuous anomaly score is mapped into a normalized 0.0 to 100.0 index:
     - `LOW` (0.0 – 39.9): Normal operating tolerance.
     - `MEDIUM` (40.0 – 64.9): Mild drift; monitor trends closely.
     - `HIGH` (65.0 – 84.9): Multivariate outlier; schedule inspection.
     - `CRITICAL` (85.0 – 100.0): Extreme breach; risk of catastrophic failure.
4. **Deterministic Fallback**:
   - If the pre-trained `.joblib` binary is missing or damaged, the engine automatically switches to a deterministic mathematical boundary detector (`RULE_BASED_FALLBACK`), ensuring safety without throwing unhandled exceptions.

---

## 7. High-Performance Database & Optimization

During high-frequency SCADA telemetry polling (every 3 seconds), unindexed queries on large historical tables can result in cumulative table scans. To guarantee ultra-responsive performance, FactoryTwin implements:

1. **SQLite Write-Ahead Logging (WAL Mode)**:
   - Enables simultaneous non-blocking concurrent readers while the background physics simulator continuously commits sensor updates.
2. **Dedicated Compound B-Tree Indexes**:
   - `idx_telemetry_machine_id_id ON telemetry(machine_id, id DESC)`: Directly indexes the latest machine readings.
   - `idx_anomaly_telemetry_id ON anomaly_predictions(telemetry_id)`: Eliminates full-table scans during relational joins.
   - **Result**: Query execution dropped from **177.8 seconds down to 0.0006 seconds (<1ms)**, ensuring instant dashboard synchronization even with tens of thousands of historical records.

---

## 8. Quick Start Guide for Windows 10/11 & VS Code

All commands must be executed from the **project root directory** (`g:\SmartFactoryDigitalTwin`).

### 8.1 Prerequisites
- Ensure **Python 3.12** is installed. Verify in PowerShell or Command Prompt:
  ```powershell
  python --version
  ```

### 8.2 Virtual Environment Setup
To bypass Windows PowerShell execution policy restrictions (`PSSecurityException`), execute commands using the virtual environment's direct binary path:

```powershell
# 1. Navigate to the project root
cd g:\SmartFactoryDigitalTwin

# 2. Create the Python virtual environment
py -m venv .venv

# 3. Upgrade pip
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# 4. Install Core Production Dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 5. (Optional) Install MQTT Dependencies if connecting to HiveMQ Cloud
.\.venv\Scripts\python.exe -m pip install -r requirements-mqtt.txt
```

---

## 9. Key Management Commands

| Command | PowerShell Syntax | Description |
| :--- | :--- | :--- |
| **Initialize Database** | `.\.venv\Scripts\python.exe database.py` | Creates tables, compound indexes, and default accounts. *(Add `--reset` to reseed)* |
| **Generate Datasets** | `.\.venv\Scripts\python.exe ai_model/generate_dataset.py` | Generates 12k training and 3k evaluation telemetry records. |
| **Train AI Model** | `.\.venv\Scripts\python.exe ai_model/train_model.py` | Trains Isolation Forest, standardizes scaler & outputs metrics report. |
| **Run Test Suite** | `.\.venv\Scripts\python.exe tests/run_tests.py` | Discovers and executes all 32 automated unit/integration tests. |
| **Compile Presentation**| `.\.venv\Scripts\python.exe docs/generate_presentation.py` | Compiles technical 15-slide PowerPoint deck (`docs/presentation.pptx`). |
| **Launch Web Platform** | `.\.venv\Scripts\python.exe app.py` | Starts the digital twin simulation and Flask SCADA dashboard on port 5000. |

---

## 10. Accessing the Web Dashboard & Default Credentials

Once `app.py` is running, open your web browser to:
👉 **`http://127.0.0.1:5000`** *(or `http://<your-local-ip>:5000` from another PC on the same LAN)*.

### Default Demonstration Accounts

| Role | Username | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@12345` | Full SCADA control, simulator pause/resume, user management, audit trails, alert acknowledgement & resolution, report downloads. |
| **Plant Operator** | `operator` | `Operator@12345` | SCADA monitoring, machine detail inspection, alert acknowledgement, fault injection testing, operational report downloads. |

---

## 11. REST API Reference

The platform provides a complete set of REST endpoints for SCADA integration and hardware edge connectivity:

| Method | Endpoint | Auth Required | Description |
| :---: | :--- | :---: | :--- |
| `GET` | `/` or `/dashboard` | Operator / Admin | Renders the primary central SCADA dashboard. |
| `GET` | `/machine/<machine_id>` | Operator / Admin | Renders individual machine twin inspector with historical trend graphs. |
| `GET` | `/api/telemetry/latest` | Operator / Admin | Returns real-time telemetry array for all 4 machines with AI anomaly scores. |
| `GET` | `/api/telemetry/history/<machine_id>` | Operator / Admin | Returns time-series telemetry records for a specific machine asset. |
| `POST`| `/api/simulator/inject_fault` | Operator / Admin | Injects one of the 7 operational regimes into a machine for $N$ cycles. |
| `POST`| `/api/simulator/start` | Administrator | Starts the background physics simulation engine. |
| `POST`| `/api/simulator/stop` | Administrator | Pauses the background physics simulation engine. |
| `GET` | `/api/datasource/mode` | Operator / Admin | Returns active data source modes (`SYNTHETIC`, `ESP32`, `HYBRID`). |
| `POST`| `/api/datasource/set_mode` | Administrator | Switches asset scope (`ALL` or specific machine) between `SYNTHETIC` and `ESP32`. |
| `POST`| `/api/esp32/telemetry` | **Public / Edge** | Ingests real or emulated telemetry packets from physical ESP32 edge nodes. |
| `POST`| `/api/esp32/test_packet` | Operator / Admin | Emulates an ESP32 hardware packet for immediate demonstration without physical hardware. |
| `GET` | `/api/alerts` | Operator / Admin | Returns real-time plant safety alarms with optional filtering. |
| `POST`| `/api/alerts/<id>/acknowledge`| Operator / Admin | Sets alert status to `ACKNOWLEDGED`. |
| `POST`| `/api/alerts/<id>/resolve` | Administrator | Sets alert status to `RESOLVED` with mandatory audit notes. |
| `GET` | `/reports/export` | Operator / Admin | Generates and downloads filtered CSV (Excel BOM) or PDF executive reports. |

---

## 12. Automated Testing & Verification

FactoryTwin includes an automated test runner executing **32 unit, integration, and security tests** across all 7 platform layers:

```powershell
.\.venv\Scripts\python.exe tests/run_tests.py
```

### Actual Verification Results:
```text
================================================================================
 FACTORYTWIN  - AUTOMATED VERIFICATION & TEST SUITE
 Execution Timestamp: 2026-11-08 18:08:38
 Python Environment:  3.12.10 on win32
================================================================================

[AI] Isolation Forest successfully loaded from isolation_forest_model.joblib
[OK] Database successfully initialized at: factory_twin.db

----------------------------------------------------------------------
Ran 32 tests in 16.86s

OK
================================================================================
FACTORYTWIN  - FORMAL TEST EXECUTION REPORT
================================================================================
Total Tests Run:    32
Passed Tests:       32
Failures:           0
Errors:             0
Elapsed Duration:   16.86 seconds
Overall Result:     PASSED [SUCCESS]
================================================================================
```
The detailed execution report is permanently logged in [`tests/test_results.txt`](tests/test_results.txt).

---

## 13. Optional ESP32 Hardware Edge Extension

For physical prototyping and hardware demonstrations, FactoryTwin includes complete firmware and wiring guides:

- **Microcontroller**: ESP32 DevKit V1 (Dual Core 240MHz, 2.4GHz WiFi).
- **Sensor**: InvenSense MPU-6050 6-DOF IMU (Accelerometer & Gyroscope over I2C).
- **Firmwares Provided**:
  - Arduino C++: [`hardware/esp32_firmware.ino`](hardware/esp32_firmware.ino)
  - MicroPython: [`hardware/esp32_micropython.py`](hardware/esp32_micropython.py)
- **Estimated Bill of Materials**: ~**₹1,127 INR** across Indian electronic suppliers (Robu.in, ElectronicsComp).
- **Documentation**: See [`hardware/circuit_diagram.md`](hardware/circuit_diagram.md) and [`hardware/calibration_guide.md`](hardware/calibration_guide.md).

---

## 14. HCLTech Project Guide Documentation Index (`docs/`)

All 12 stages of the HCLTech Embedded Systems & IoT Project Creation Guide are documented in the [`docs/`](docs/) directory:

1. [docs/01_problem_statement.md](docs/01_problem_statement.md) - Stage 1: Problem Statement, Industrial Motivation & Quantified Value
2. [docs/02_project_planning.md](docs/02_project_planning.md) - Stage 2: 25-Day Milestone Roadmap & Work Breakdown Structure
3. [docs/03_software_requirements_specification.md](docs/03_software_requirements_specification.md) - Stage 3: Formal IEEE 830 Software Requirements Specification
4. [docs/04_system_design_and_architecture.md](docs/04_system_design_and_architecture.md) - Stage 4: System Architecture, Data Flow & Sequence Diagrams
5. [docs/05_database_schema.md](docs/05_database_schema.md) - Stage 5: Database Schema, Relational Entity Model & Indexes
6. [docs/06_mqtt_guide_and_hivemq.md](docs/06_mqtt_guide_and_hivemq.md) - Stage 6: MQTT Industrial Communication & HiveMQ Cloud Guide
7. [docs/07_bill_of_materials.md](docs/07_bill_of_materials.md) - Stage 7: Hardware Bill of Materials (BOM in INR) & Sourcing
8. [docs/08_test_documentation.md](docs/08_test_documentation.md) - Stage 8: 32-Test Verification Matrix & Execution Results
9. [docs/09_user_manual.md](docs/09_user_manual.md) - Stage 9: Comprehensive Operator & Administrator Manual
10. [docs/10_project_report.md](docs/10_project_report.md) - Stage 10: Complete University BTech Capstone Project Report
11. [docs/11_presentation.md](docs/11_presentation.md) & [docs/presentation.pptx](docs/presentation.pptx) - Stage 11: 15-Slide Technical Presentation Deck
12. [docs/12_demo_script.md](docs/12_demo_script.md) - Stage 12: Step-by-Step Live Viva Demonstration Protocol

---

## 15. License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.  
Developed as an academic capstone and practical Industry 4.0 IoT demonstration.
