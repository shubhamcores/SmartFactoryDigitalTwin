# Digital Twin
# AI-Driven Digital Twin for Smart Factory Operations

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask 3.1](https://img.shields.io/badge/Flask-3.1.3-emerald.svg)](https://palletsprojects.com/p/flask/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation_Forest-purple.svg)](https://scikit-learn.org/)
[![MQTT](https://img.shields.io/badge/MQTT-HiveMQ_Cloud-orange.svg)](https://www.hivemq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-gray.svg)](LICENSE)
[![Tests: 30 Passed](https://img.shields.io/badge/Tests-30%2F30%20Passed-brightgreen.svg)](tests/test_results.txt)

> **BTech Individual Capstone Project**  
> Developed under the **HCLTech Project Creation Guide for Embedded Systems & IoT**.  
> Designed for seamless execution on **Windows 10 / 11** using **VS Code** and **Python 3.12**.

---

## 1. Executive Summary & Overview

Industrial machinery—such as 3-phase induction motors, belt conveyors, centrifugal pumps, and 5-axis CNC machining centers—experiences ongoing vibration, overheating, electrical overload, and unexpected mechanical stoppages. Without real-time digital monitoring, maintenance is either reactive (incurring \$50k–\$250k/hr downtime) or calendar-based (wasting functional equipment life).

**FactoryTwin** is a complete cyber-physical **Digital Twin** and **Industrial IoT (IIoT)** platform that:
1. **Simulates 4 Industrial Assets**: Continuously models thermodynamics, rotational inertia, and mechanical dynamics across 7 operational regimes.
2. **Collects Multi-Parameter Telemetry**: Real-time acquisition of Temperature (°C), Vibration Velocity RMS (ISO 10816 mm/s), Rotational Speed (RPM), Mechanical Load (%), and Production Output.
3. **Applies Unsupervised AI Anomaly Detection**: Uses a Scikit-Learn **Isolation Forest** pipeline trained strictly on normal operations (12,000 samples) to detect subtle multivariate outliers without requiring rare failure history.
4. **Intelligently Manages Alarms**: Incorporates an in-memory 60-second cooldown window to prevent **alarm fatigue** / alert storms, with a complete `NEW` $\to$ `ACKNOWLEDGED` $\to$ `RESOLVED` lifecycle.
5. **Surfaces a Dark Industrial SCADA Dashboard**: Features responsive Bootstrap 5 cards, animated Chart.js trends, single-click fault injection for live evaluation, and Role-Based Access Control (RBAC).
6. **Generates Executive Reports**: One-click download of Excel-compatible CSVs (UTF-8 BOM) and ReportLab executive PDF reports.
7. **Supports Optional Hardware**: Includes tested ESP32 Arduino C++ and MicroPython firmware for physical MPU-6050 vibration sensing with an estimated ₹1,127 INR Bill of Materials.

---

## 2. Project Architecture & Subsystems

```
Machine Simulator or Optional ESP32
                 ↓
Telemetry Generation (Temp, Vib, RPM, Load, Units)
                 ↓
MQTT Transport (Offline Direct or HiveMQ Cloud TLS 8883)
                 ↓
SQLite Database (WAL Mode, Indexed, Deduplicated)
                 ↓
AI Anomaly Inference (Isolation Forest & Standardizer)
                 ↓
Alert & Health Service (Thresholds & 60s Cooldowns)
                 ↓
Flask Backend & REST APIs (/api/telemetry, /api/alerts)
                 ↓
Central SCADA Dashboard (Chart.js Real-time Trends)
                 ↓
CSV (Excel BOM) & ReportLab Executive PDF Reports
```

---

## 3. Quick Start Guide for Windows 10/11 & VS Code

All commands must be executed from the **project root directory** (`g:\DigitalTwinForFactory` where `app.py` and `requirements.txt` are located).

### 3.1 Prerequisites
- Ensure **Python 3.12** is installed. Verify in PowerShell or Command Prompt:
  ```powershell
  py --version
  # or
  python --version
  ```

### 3.2 Automated Windows Setup (Avoiding PowerShell Activation Restrictions)
In Windows PowerShell, script execution is frequently blocked by default policies (`PSSecurityException`). To avoid this, run Python directly via the virtual environment's executable path:

```powershell
# 1. Clone or navigate to the project root
cd g:\DigitalTwinForFactory

# 2. Create the Python virtual environment
py -m venv .venv

# 3. Upgrade pip
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# 4. Install Core Dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 5. (Optional) Install MQTT Dependencies if connecting to HiveMQ
.\.venv\Scripts\python.exe -m pip install -r requirements-mqtt.txt
```

---

## 4. Key Management Commands

All commands run directly from the project root:

| Task | PowerShell Command |
| :--- | :--- |
| **Initialize / Reset Database** | `.\.venv\Scripts\python.exe database.py` *(use `--reset` to reseed)* |
| **Generate Synthetic Telemetry Datasets** | `.\.venv\Scripts\python.exe ai_model/generate_dataset.py` |
| **Train Isolation Forest & Evaluate** | `.\.venv\Scripts\python.exe ai_model/train_model.py` |
| **Run Complete Automated Test Suite (30 Tests)** | `.\.venv\Scripts\python.exe tests/run_tests.py` |
| **Compile PowerPoint Presentation (.pptx)** | `.\.venv\Scripts\python.exe docs/generate_presentation.py` |
| **Launch FactoryTwin SCADA Platform** | `.\.venv\Scripts\python.exe app.py` |

---

## 5. Accessing the Web Dashboard & Default Credentials

Once `app.py` is running, open your web browser to:
👉 **`http://127.0.0.1:5000`**

### 5.1 Telemetry Data Source Selection (Synthetic Simulator vs ESP32 Hardware)
FactoryTwin allows you to seamlessly switch between **Synthetic Physics Simulation** and **Live ESP32 Hardware Edge Ingestion**:
- Click the **"Source: SYNTHETIC"** button on the top navigation bar (or the Feed Source KPI card).
- Select between:
  1. **Synthetic Physics Simulator**: Autonomous digital twin simulation engine running in the background. Zero physical hardware needed.
  2. **ESP32 Hardware Edge Node**: Pauses synthetic generation for selected asset(s) (e.g. `Motor`) and strictly awaits real physical telemetry from an ESP32 microcontroller!
- **Ingestion Channels for ESP32**:
  - **MQTT Topic**: `factory/machines/Motor/telemetry` (via HiveMQ Cloud or Mosquitto)
  - **Direct HTTP REST Endpoint**: `http://<server-ip>:5000/api/esp32/telemetry` (POST JSON)
- **One-Click Testing**: Inside the modal, click **"Send Test ESP32 Packet"** to instantly test and demonstrate ESP32 hardware ingestion without physical hardware attached.

### 5.2 Pre-Configured Demonstration Accounts

| Role | Username | Password | Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `Admin@12345` | Full SCADA control, simulator pause/resume, user management, audit trails, alert acknowledgement & resolution, report downloads. |
| **Plant Operator** | `operator` | `Operator@12345` | SCADA monitoring, machine detail inspection, alert acknowledgement, fault injection testing, operational report downloads. |

> [!WARNING]
> These credentials are for academic demonstration and testing purposes. In production deployments, change the default passwords immediately using the administrator console.

---

## 6. Machine Assets & Simulation Regimes

FactoryTwin continuously tracks four industrial assets:
1. **Motor**: Main drive 3-phase induction motor (1750 RPM base, 85°C thermal limit, 4.5 mm/s ISO 10816 vibration limit).
2. **Conveyor**: Logistics belt conveyor assembly (450 RPM base, 70°C limit, 3.8 mm/s vibration limit).
3. **Pump**: Centrifugal cooling circuit pump (2900 RPM base, 80°C limit, 5.0 mm/s vibration limit).
4. **CNC**: 5-axis precision milling machining center (2400 RPM base, 90°C limit, 5.5 mm/s vibration limit).

### 7 Supported Operational Regimes:
- `NORMAL`: Certified operating parameters with ambient thermal/mechanical noise.
- `HIGH_TEMP`: Thermal rise beyond machine thermal rating (coolant failure).
- `HIGH_VIB`: Elevated vibration velocity exceeding ISO 10816 limits (bearing race defect).
- `EXCESSIVE_LOAD`: High mechanical drag (>90% capacity) with speed drop (mechanical jam).
- `REDUCED_PRODUCTION`: Throttled operating speed with diminished unit increments.
- `STOPPAGE`: Emergency trip with immediate speed deceleration to 0.0 RPM.
- `ABNORMAL_SENSOR`: Transient erratic readings representing electrical sensor glitch.

*Use the **Fault Simulator** button on the top navigation bar to inject any of these regimes in real time.*

---

## 7. Machine Learning Pipeline (Isolation Forest)

- **Input Features**: `temperature`, `vibration`, `speed`, `load`.
- **Zero Data Leakage**: The unsupervised Isolation Forest is fitted strictly on 12,000 normal operating records. Labeled anomalies are used exclusively for evaluation on a separate 3,000-sample test set.
- **Empirical Evaluation Metrics**:
  - **Recall (Sensitivity)**: **89.73%** (Detected ~9 out of 10 anomalies).
  - **Precision**: **72.83%**.
  - **F1-Score**: **80.40%**.
  - **False Positive Rate**: **5.88%** (Safely below 7% nuisance alarm threshold).
- **Risk Tiers**:
  - `LOW` (0.0 – 39.9): Normal operating tolerance.
  - `MEDIUM` (40.0 – 64.9): Mild statistical drift; monitor trend.
  - `HIGH` (65.0 – 84.9): Significant operational outlier; schedule inspection.
  - `CRITICAL` (85.0 – 100.0): Extreme outlier; danger of thermal/mechanical damage.
- **Rule-Based Fallback**: If the model `.joblib` file is absent, a deterministic boundary detector handles incoming readings automatically and flags its output as `RULE_BASED_FALLBACK`.

---

## 8. MQTT & HiveMQ Cloud Integration

The platform functions 100% offline by default. To connect to an external MQTT broker (local Mosquitto or HiveMQ Cloud):

1. Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
2. Set configuration values in `.env`:
   ```ini
   MQTT_ENABLED=True
   MQTT_BROKER_HOST=your-cluster-url.s1.eu.hivemq.cloud
   MQTT_BROKER_PORT=8883
   MQTT_USE_TLS=True
   MQTT_USERNAME=your_username
   MQTT_PASSWORD=your_password
   MQTT_TOPIC_PREFIX=factory/machines
   ```
3. Restart `app.py`. The top navbar will display **Source: MQTT_LIVE** upon packet receipt.
4. *See [docs/06_mqtt_guide_and_hivemq.md](docs/06_mqtt_guide_and_hivemq.md) for MQTT Explorer testing instructions.*

---

## 9. Optional ESP32 Hardware Extension

For physical edge prototyping:
- **Firmware**: Arduino C++ (`hardware/esp32_firmware.ino`) & MicroPython (`hardware/esp32_micropython.py`).
- **Sensors**: ESP32 DevKit V1 + GY-521 (InvenSense MPU-6050 Accelerometer/Gyroscope).
- **Digital Signal Processing**: Moving average filter converts raw acceleration ($g$) to vibration velocity RMS (mm/s) according to ISO 10816 standards.
- **Estimated BOM**: ~₹1,127 INR across Indian suppliers (Robu.in, ElectronicsComp).
- *See [hardware/circuit_diagram.md](hardware/circuit_diagram.md) and [hardware/calibration_guide.md](hardware/calibration_guide.md).*

---

## 10. Automated Testing & Verification

The project includes an automated test runner executing 30 unit, integration, and security tests across all 7 layers:
```powershell
.\.venv\Scripts\python.exe tests/run_tests.py
```
**Actual Verification Results**:
- **30 Tests Run | 30 Passed | 0 Failures | 0 Errors (100% Pass Rate)**
- Test execution output is permanently logged in [tests/test_results.txt](tests/test_results.txt).

---

## 11. HCLTech Documentation Index (`docs/`)

All 8 stages of the HCLTech Embedded Systems & IoT Project Creation Guide are documented under `docs/`:
1. [docs/01_problem_statement.md](docs/01_problem_statement.md) - Stage 1: Problem Statement & Industrial Motivation
2. [docs/02_project_planning.md](docs/02_project_planning.md) - Stage 2: 25-Day Milestone-Based Project Plan
3. [docs/03_software_requirements_specification.md](docs/03_software_requirements_specification.md) - Stage 3: IEEE 830 Software Requirements Specification (SRS)
4. [docs/04_system_design_and_architecture.md](docs/04_system_design_and_architecture.md) - Stage 4: System Architecture, Mermaid & Data Flow Diagrams
5. [docs/05_database_schema.md](docs/05_database_schema.md) - Stage 5: Database Schema & Entity-Relationship Model
6. [docs/06_mqtt_guide_and_hivemq.md](docs/06_mqtt_guide_and_hivemq.md) - Stage 6: MQTT Industrial Communication & HiveMQ Guide
7. [docs/07_bill_of_materials.md](docs/07_bill_of_materials.md) - Stage 7: Hardware Bill of Materials (BOM in INR)
8. [docs/08_test_documentation.md](docs/08_test_documentation.md) - Stage 8: Test Plan, Test Cases & Actual Execution Matrix
9. [docs/09_user_manual.md](docs/09_user_manual.md) - Stage 9: Comprehensive Operator & Administrator Manual
10. [docs/10_project_report.md](docs/10_project_report.md) - Stage 10: Complete University BTech Project Report (Academic Format)
11. [docs/11_presentation.md](docs/11_presentation.md) & [docs/presentation.pptx](docs/presentation.pptx) - Stage 11: 15-Slide Presentation Deck
12. [docs/12_demo_script.md](docs/12_demo_script.md) - Stage 12: Step-by-Step Live Demonstration Protocol & Viva Preparation

---

## 12. Version Control & Git Workflow

A beginner-friendly daily Git workflow is established:
```bash
# Check status of modified files
git status

# Stage files for commit
git add .

# Commit with a descriptive conventional message
git commit -m "feat(ai_model): implement isolation forest anomaly inference"

# Tag formal final release
git tag -a v1.0 -m "Release v1.0: Complete BTech Project P_307"
```

---

## 13. License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
Developed for academic submission and practical Industrial IoT demonstration.
