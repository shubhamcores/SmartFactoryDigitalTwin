# Stage 9: Comprehensive User Manual (P_307)
## Plant Operator & Administrator Operational Guide
**Platform**: FactoryTwin Industrial SCADA & Digital Twin (Version 1.0.0)

---

## 1. System Setup & Initial Launch on Windows

### 1.1 Prerequisites
- Windows 10 or Windows 11 (64-bit)
- Python 3.12 installed (check with `py --version` or `python --version`)
- Visual Studio Code (recommended) or any modern web browser (Edge, Chrome, Firefox)

### 1.2 Step-by-Step Launch Procedure
Open your command terminal (PowerShell or Command Prompt) and navigate to the project directory:

```powershell
cd g:\DigitalTwinForFactory

# (Optional) Create virtual environment if starting from fresh install
python -m venv .venv

# Install required dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Start the FactoryTwin server
.\.venv\Scripts\python.exe app.py
```

Upon launch, the terminal displays:
```
======================================================================
 FACTORYTWIN (P_307) - SMART FACTORY SCADA & DIGITAL TWIN
 Web Dashboard: http://127.0.0.1:5000
 Default Administrator: admin / Admin@12345
 Default Plant Operator: operator / Operator@12345
======================================================================
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 2. Authentication & User Roles

### 2.1 Sign In Screen
When accessing the portal, you will be prompted to authenticate:

```
+---------------------------------------------------------+
|                      FACTORYTWIN                        |
|       AI-Driven Digital Twin & SCADA Operations         |
|                                                         |
|  Username: [ admin               ]                      |
|  Password: [ **********          ]                      |
|                                                         |
|  [     Access Factory SCADA     ]                       |
|                                                         |
|  DEMO / EVALUATOR PRESETS:                              |
|  [ Administrator (admin) ]   [ Operator (operator) ]    |
+---------------------------------------------------------+
```

- **Quick Presets**: For demonstration convenience, click **Administrator** or **Operator** to auto-populate credentials.
- **Default Credentials**:
  - **Administrator**: `admin` / `Admin@12345`
  - **Plant Operator**: `operator` / `Operator@12345`

---

## 3. Central SCADA Dashboard Walkthrough

After login, you land on the **Central Factory Digital Twin** overview:

```
+----------------------------------------------------------------------------------------------------+
| FACTORYTWIN   [Pulse] Engine: Active   [Fault Simulator] [Pause Sim]  [Alerts (0)]  (Admin) Logout |
+----------------------------------------------------------------------------------------------------+
| Monitored Assets | Running Status | Degraded/Warning | Stopped/Trip | Active Alarms | Telemetry Feed |
|        4         |       4        |        0         |      0       |       0       |   SIMULATED    |
+----------------------------------------------------------------------------------------------------+
| [ Motor (Drive) ]   [ Conveyor (Line) ]  [ Pump (Coolant) ]   [ CNC (Milling) ]            |
| Temp: 62.4 °C         Temp: 42.1 °C          Temp: 54.3 °C          Temp: 68.2 °C                  |
| Vib:  1.61 mm/s       Vib:  1.12 mm/s        Vib:  2.01 mm/s        Vib:  2.34 mm/s                |
| Speed: 1748 RPM       Speed: 452 RPM         Speed: 2904 RPM        Speed: 2402 RPM                |
| Load: 64 %            Load: 51 %             Load: 71 %             Load: 74 %                     |
| AI Risk: [LOW 12/100] AI Risk: [LOW 9/100]   AI Risk: [LOW 14/100]  AI Risk: [LOW 15/100]          |
+----------------------------------------------------------------------------------------------------+
| [ Chart 1: Thermal Trends ]                  [ Chart 2: Vibration Velocity (ISO 10816) ]           |
|                                                                                                    |
| [ Chart 3: Drive Speed (RPM) ]               [ Chart 4: Production Output (Units) ]                |
+----------------------------------------------------------------------------------------------------+
```

### Key Screen Elements:
1. **Top KPI Cards**: Real-time counter of online machines, warning states, emergency trips, and active alarm count.
2. **Asset Cards**: Live gauges showing Temperature (°C), Vibration (mm/s), Speed (RPM), Load (%), and AI Anomaly Risk Bar.
3. **Real-Time Charts**: 4 synchronized Chart.js graphs displaying 20-sample rolling trends updating every 3 seconds.
4. **Recent Alerts Feed**: Real-time table displaying recent threshold warnings with an immediate **Acknowledge** button.

---

## 4. Telemetry Data Source Selection: Synthetic vs ESP32 Hardware

FactoryTwin provides an interactive runtime toggle allowing operators to choose between synthetic digital twin simulation and real ESP32 edge telemetry:

1. Click the **Source: SYNTHETIC** button on the top navigation bar (or click the **Feed Source** card on the dashboard).
2. The **Telemetry Data Source Configuration** modal opens:
   - **Synthetic Physics Simulator**: Autonomous digital twin simulation engine running in the background. Zero physical hardware needed.
   - **ESP32 Hardware Edge Node**: Pauses synthetic generation for selected asset(s) (e.g. `Motor`) and strictly awaits real physical telemetry from an ESP32 microcontroller!
3. **Asset Scope**:
   - You can toggle all machines globally, or set an individual machine (e.g., `Motor`) to ESP32 mode while `Conveyor`, `Pump`, and `CNC` continue on simulation.
4. **Ingestion Channels for ESP32**:
   - **MQTT Topic**: `factory/machines/Motor/telemetry` (via HiveMQ Cloud or Mosquitto)
   - **Direct HTTP REST Endpoint**: `http://<server-ip>:5000/api/esp32/telemetry` (POST JSON)
5. **One-Click Testing**: Inside the modal, click **"Send Test ESP32 Packet"** to instantly test and demonstrate ESP32 hardware ingestion without physical hardware attached.

---

## 5. Digital Twin Asset Inspector

To inspect an individual machine in depth, click **Twin Inspector** on any card or select the machine in the sidebar:
- **Comprehensive Gauges**: Compares instantaneous measurements against certified baseline limits and maximum thresholds.
- **AI Diagnostics Box**: Displays the computed Isolation Forest outlier score, normalized risk tier (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and specific engineering maintenance recommendations.
- **Synchronized Multi-Parameter Chart**: Dual Y-axis historical chart showing temperature, vibration, and mechanical load interactions over time.
- **Asset Maintenance Schedule**: View scheduled work orders (e.g., lubrication, laser alignment, impeller inspection).

---

## 5. Live Fault Simulation & Demonstration Panel

To demonstrate how the platform detects and responds to physical machine failures in real time:

1. Click the **Fault Simulator** button on the top navigation bar.
2. The modal dialog appears:
   - **Target Machine**: Select e.g. `Motor`.
   - **Operational Regime**: Choose one of:
     - `HIGH_TEMP`: Simulates cooling failure / thermal runaway.
     - `HIGH_VIB`: Simulates severe bearing raceway spalling.
     - `EXCESSIVE_LOAD`: Simulates mechanical transmission jam.
     - `REDUCED_PRODUCTION`: Simulates supply line starvation.
     - `STOPPAGE`: Simulates emergency E-Stop trip.
     - `ABNORMAL_SENSOR`: Simulates transient electrical glitch.
     - `NORMAL`: Restores certified normal baseline.
   - **Duration**: Specify duration in simulation cycles (e.g. 12 cycles).
3. Click **Apply Injected Regime**.
4. **Observe the Reaction**:
   - Within 3 seconds, the target machine card shows elevated telemetry.
   - The status badge transitions to `WARNING` or `CRITICAL`.
   - The AI Anomaly Risk Bar increases from `LOW` to `HIGH` or `CRITICAL`.
   - The recommended maintenance action updates dynamically.
   - A new alarm is registered in the alerts registry!

---

## 6. Alerts & Alarms Management

Navigate to **Alerts & Alarms** from the sidebar:
- **Filter Bar**: Filter by Machine, Severity (`CRITICAL`, `WARNING`, `INFO`), and Status (`NEW`, `ACKNOWLEDGED`, `RESOLVED`).
- **Acknowledging an Alarm (Operator or Admin)**: Click **Acknowledge** to indicate that plant floor staff have been dispatched to investigate.
- **Resolving an Alarm (Admin Only)**:
  1. Click **Resolve**.
  2. In the modal, document the corrective maintenance action taken (e.g., "Replaced mechanical coupling and regreased bearing cavity").
  3. Click **Confirm Resolution**.
  4. The alarm transitions to `RESOLVED` and is archived in the permanent SQLite audit ledger.

---

## 7. Generating Operational Reports & Data Exports

Navigate to **Reports & Audits** from the sidebar:
1. Select the **Report Category**:
   - `Machine Telemetry Stream`
   - `Production Output & Efficiency`
   - `Machine State Transitions`
   - `AI Anomaly Predictions & Risk`
   - `Safety & Maintenance Alarms`
   - `Executive Daily Factory Summary`
2. Specify optional filters: Target Machine, Start Date, End Date.
3. Click **Preview Query Results** to inspect records in the browser table.
4. Export options:
   - **Download CSV (Excel)**: Downloads a clean, Excel-compatible CSV file with UTF-8 BOM encoding.
   - **Download Executive PDF**: Generates a high-resolution, formatted PDF document with summary headers, styled tables, and "Page X of Y" canvas footers.

---

## 8. Plant Administration (Admin Role)

### 8.1 User Management (`/admin/users`)
- View all authorized personnel and their last login timestamps.
- Register new operators or administrators with designated roles.

### 8.2 Security Audit Trails (`/admin/audit`)
- View immutable chronological logs of all login events, fault injections, alert resolutions, and configuration updates with client IP addresses.
