# Stage 12: Live Demonstration Script & Evaluation Guide (P_307)
## Step-by-Step Live Demonstration Protocol for Project Defense & Vivas
**Duration**: 8 to 12 Minutes  
**Demonstration Target**: Web Browser at `http://127.0.0.1:5000`

---

## 1. Pre-Demonstration Checklist
Before inviting the project examiners or evaluating committee to view the demonstration, ensure:
1. Terminal 1 is running:
   ```powershell
   cd g:\DigitalTwinForFactory
   python app.py
   ```
2. Browser is open at `http://127.0.0.1:5000/login`.
3. Verify test suite passed:
   ```powershell
   python tests/run_tests.py
   ```
   *(Ensure 30/30 tests passed).*

---

## 2. Minute-by-Minute Live Demonstration Walkthrough

### Part 1: Authentication & Role-Based Access Control (0:00 – 1:30)
1. **Explain the Login Screen**:
   - Point out the industrial dark theme, project code `P_307`, and the **Demo Presets** helper cards.
2. **Demonstrate Operator Login**:
   - Click the green **Plant Operator** helper box (fills `operator` / `Operator@12345`).
   - Click **Access Factory SCADA**.
   - Note the top profile badge showing `OPERATOR`.
3. **Demonstrate Access Control Enforcement**:
   - Manually type `http://127.0.0.1:5000/admin/users` into the URL bar and hit Enter.
   - **Show the Outcome**: The platform blocks the operator with an alert: *"Access denied: Administrator privileges required"*, and safely redirects to the dashboard. Mention this is enforced via server-side `@admin_required` decorators, not just hidden UI buttons.
4. **Sign In as Administrator**:
   - Click User profile $\to$ **Sign Out**.
   - Click the red **Administrator** preset (`admin` / `Admin@12345`) and log in.

---

### Part 2: Normal Digital Twin SCADA Monitoring (1:30 – 3:30)
1. **Central Dashboard Overview**:
   - Point to the **Top KPI Row**: 4 Monitored Assets, 4 Running, 0 Warning, 0 Stopped, 0 Active Alarms.
   - Show the **Telemetry Feed Badge**: Displays `SIMULATED` (or `MQTT_LIVE` if broker connected).
   - Point to the **Last Sync timestamp**: Updates every 3 seconds asynchronously via fetch API without full-page flickering.
2. **Show the 4 Machines**:
   - `Motor` (Induction Motor), `Conveyor` (Belt Conveyor), `Pump` (Coolant Pump), `CNC` (5-Axis Mill).
   - Show that each card displays live Temperature (°C), Vibration (mm/s), Speed (RPM), Load (%), and Units.
   - Point to the **AI Anomaly Risk Bar**: Green bar showing `LOW` risk (~12/100 score) computed by the Isolation Forest model.
3. **Inspect the Real-Time Charts**:
   - Scroll down to the 2x2 Chart.js grid.
   - Show the live rolling lines for Temperature, Vibration, Speed, and Production Output.
   - Note that each machine has a dedicated color (Blue, Green, Cyan, Amber).

---

### Part 3: Live Fault Injection & Anomaly Detection (3:30 – 6:00)
*This is the most critical technical demonstration of the project.*

1. **Open Fault Simulator Panel**:
   - Click the yellow **Fault Simulator** button on the top navbar.
   - Select:
     - **Target Machine**: `Motor`
     - **Regime**: `HIGH_TEMP` (Coolant Failure / Overheating)
     - **Duration**: `10` cycles.
   - Click **Apply Injected Regime**.
2. **Observe Real-Time System Reaction**:
   - Within 3 seconds, `Motor`'s card temperature begins rising from 62°C toward 95°C.
   - The status badge transitions from `RUNNING` to `WARNING`.
   - **Watch the AI Risk Bar**: It surges from `LOW` (12) to `HIGH` (75+).
   - The top alarm counter increments: **Active Alarms: 1**.
   - An alert appears in the **Recent Operational Alerts** table:
     - Severity: `CRITICAL`
     - Message: *"Critical thermal threshold breached: 96.2°C (Limit: 85.0°C). Thermal runaway risk."*
3. **Drill Down into the Digital Twin Inspector**:
   - Click **Twin Inspector** on the `Motor` card (navigates to `/machine/Motor`).
   - Show the large real-time gauge metrics.
   - Point to the **AI Diagnostics Box**:
     - Calculated Risk Score: `82.4 / 100` (CRITICAL RISK).
     - Recommended Action: *"Temperature high (96.2°C > 85.0°C): Inspect coolant flow, heat sink fins, and thermal paste."*
   - Show the historical anomaly table at the bottom documenting each abnormal event with timestamp.

---

### Part 4: Alert Lifecycle & Deduplication (6:00 – 7:30)
1. **Explain Cooldown Deduplication**:
   - Mention to the examiner: *"Notice that even though the machine remained hot for multiple seconds, the system did not create 20 duplicate alerts. Our 60-second in-memory cooldown prevents alarm fatigue while keeping the operator aware."*
2. **Navigate to Alerts & Alarms (`/alerts`)**:
   - View the alert in the central registry with status `NEW`.
3. **Acknowledge the Alert**:
   - Click **Acknowledge**.
   - The status badge transitions to `ACKNOWLEDGED` (yellow) with the username `admin` and timestamp recorded.
4. **Resolve the Alert (Admin Action)**:
   - Click **Resolve**.
   - In the modal dialog, enter corrective maintenance action:
     - *"Cleaned clogged heat exchanger, replaced coolant valve, and verified thermal recovery."*
   - Click **Confirm Resolution**.
   - The alert updates to `RESOLVED` (green) with the documented notes permanently stored in SQLite.

---

### Part 5: Operational Reporting & Compliance Export (7:30 – 9:00)
1. **Navigate to Reports & Audits (`/reports`)**:
   - Select Report Category: `1. Machine Telemetry Stream`.
   - Machine: `Motor`.
   - Click **Preview Query Results** to inspect records in the browser table.
2. **Download CSV Export**:
   - Click **Download CSV (Excel)**.
   - Open the downloaded CSV in Excel or Notepad.
   - **Highlight**: Notice the clean UTF-8 Byte Order Mark (BOM) prevents Excel from corrupting column headers or degree symbols (`°C`).
3. **Download Executive PDF Export**:
   - Click **Download Executive PDF**.
   - Open the downloaded PDF in the browser viewer.
   - **Show the Formatting**:
     - Custom corporate title header with metadata (Generated At, Operator, Machine ID, Record Count).
     - Clean styled alternating table rows.
     - Custom footer displaying: *"FactoryTwin P_307 - Confidential Factory Operations Report | Page 1 of X"*.

---

### Part 6: Audit Trails & Administrator Management (9:00 – 10:00)
1. **Inspect User Management (`/admin/users`)**:
   - Show the user table with `admin` and `operator`.
   - Show the **Register New User** modal dialog.
2. **Inspect System Audit Trails (`/admin/audit`)**:
   - Scroll through the audit log table.
   - Point out that every action performed during this demonstration was recorded:
     - `LOGIN_SUCCESS` (operator & admin)
     - `UNAUTHORIZED_ACCESS_ATTEMPT` (when operator tried to access admin route)
     - `FAULT_INJECTED` (Motor HIGH_TEMP)
     - `ALERT_ACKNOWLEDGED`
     - `ALERT_RESOLVED` (with notes)

---

## 3. Frequently Asked Examiner Questions & Prepared Answers

| Question | Strong Technical Answer |
| :--- | :--- |
| **Q1: Why did you use Isolation Forest instead of Supervised Deep Learning?** | *"In real industrial plants, machines operate normally 99.5% of the time. Labeled historical failure datasets are extremely rare. Isolation Forest is unsupervised and requires only normal baseline data to train. It isolates anomalies using random hyperplanes based on attribute scarcity and isolation depth."* |
| **Q2: Does an anomaly score of 85 mean the machine will fail in 85 minutes?** | *"No. An Isolation Forest score indicates mathematical isolation depth—how unusual or statistically rare the reading is relative to normal clusters. It signifies an operational deviation warranting human inspection, not a calibrated failure probability."* |
| **Q3: What happens if an operator enters corrupted sensor numbers or if MQTT drops?** | *"We have multi-layered fault containment: `validate_telemetry_payload()` checks JSON schemas and physical range bounds (e.g. discarding -999°C). If MQTT drops, Paho MQTT auto-reconnects in the background, and the platform continues running offline on internal simulation with zero crashes."* |
| **Q4: How do you prevent hundreds of repeated alerts when a machine stays hot?** | *"We implemented an in-memory sliding cooldown window (`Config.ALERT_COOLDOWN_SECONDS = 60`). Once an alert fires for an asset and condition, identical triggers are suppressed for 60 seconds, preventing alarm fatigue while preserving an accurate audit log."* |
| **Q5: Is physical hardware mandatory to run this project?** | *"No, the project was intentionally architected so that the complete digital twin, machine learning inference, alerting, and SCADA dashboard operate standalone. However, for physical extensions, we have provided tested ESP32 Arduino C++ firmware, MicroPython code, circuit pinouts, and a ₹1,127 INR Bill of Materials."* |
