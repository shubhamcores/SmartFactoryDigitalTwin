# Stage 1: Problem Statement & Industrial Motivation (P_307)
## Project Title: AI-Driven Digital Twin for Smart Factory Operations
**Academic Track**: BTech Embedded Systems, Industrial IoT & Machine Learning  
**Development Framework**: HCLTech Project Creation Guide for Embedded Systems & IoT  
**Target Platform**: Windows 10/11, VS Code, Python 3.12, SQLite, MQTT, Isolation Forest

---

## 1. Executive Problem Statement
In modern manufacturing plants (automotive assembly, semiconductor packaging, continuous chemical processing, and CNC precision machining), rotating machinery and transmission systems undergo continuous physical stress. Over time, machines develop mechanical unbalance, bearing raceway spalling, thermal degradation of motor windings, transmission belt slippage, and sudden physical jams.

Traditional factory operations rely primarily on two outdated maintenance paradigms:
1. **Run-to-Failure (Reactive Maintenance)**: Machines are operated until sudden catastrophic breakdown occurs. This results in unplanned production line stoppages costing upwards of \$50,000 to \$250,000 per hour, secondary tooling damage, and severe operator safety hazards.
2. **Calendar-Based Preventive Maintenance**: Machines are taken offline for servicing at fixed calendar intervals regardless of their actual mechanical health. This introduces unnecessary downtime, wastes replacement components with substantial residual life, and fails to catch rapid early-onset thermal or vibration defects that develop between scheduled visits.

### The Digital Twin Paradigm
To bridge this gap, modern **Industry 4.0** leverages **Digital Twins**—virtual representations of physical manufacturing equipment synchronized via real-time Industrial IoT telemetry. By continuously collecting multi-parameter sensor streams (Temperature, Vibration Velocity, Rotational Speed, Electrical/Mechanical Load, and Production Output) and applying unsupervised Machine Learning algorithms, abnormal operating regimes can be identified days or weeks before catastrophic breakdown.

---

## 2. Intended Stakeholders & Users
The FactoryTwin solution is engineered for two primary industrial roles:
1. **Plant Floor Operators / Maintenance Technicians**:
   - Require real-time operational visibility into asset status (Running, Idle, Warning, Stopped).
   - Need clear, prioritized alarms with actionable engineering diagnostic guidance (e.g., "Elevated vibration: check coupling alignment and grease bearing raceway").
   - Ability to acknowledge alarms and download daily operational logs.
2. **Plant Administrators / Operations Directors**:
   - Require full governance over machine threshold configurations and user role assignments.
   - Access to immutable audit logs for regulatory and quality compliance (ISO 9001 / IATF 16949).
   - Executive PDF reporting and historical trend analytics for capital planning and Overall Equipment Effectiveness (OEE) calculations.

---

## 3. Project Objectives
1. **Digital Twin Simulation Engine**: Create a multi-machine physics-inspired digital twin modeling 4 industrial assets (`Motor_1`, `Conveyor_1`, `Pump_1`, `CNC_1`) with realistic thermal inertia, mechanical dynamics, and reproducible operational regimes.
2. **Industrial Communication Layer**: Implement dual-mode telemetry transport supporting standalone offline zero-dependency simulation and live MQTT telemetry publishing/subscribing over TLS to cloud brokers (HiveMQ Cloud).
3. **Unsupervised AI Anomaly Detection**: Implement a scikit-learn `IsolationForest` pipeline trained strictly on normal operational distributions to detect multivariate anomalies without requiring expensive labeled failure histories.
4. **Intelligent Alert Management**: Implement automated threshold evaluation, anomaly scoring, deduplication cooldowns (preventing alarm fatigue), and complete ACK/Resolve lifecycles.
5. **Role-Based Web Dashboard**: Build an industrial dark-themed SCADA dashboard with auto-refreshing Chart.js trends, single-click fault injection for live evaluation, and responsive layout.
6. **Executive Reporting**: Deliver on-demand Excel-compatible CSV exports and formatted PDF executive summaries using ReportLab.

---

## 4. Measurable Success Criteria
| Criterion | Target Metric | Verification Method |
| :--- | :--- | :--- |
| **Telemetry Ingestion Rate** | 2 to 5 seconds per asset | Database timestamp verification |
| **Data Integrity & Deduplication** | 100% duplicate message rejection | SQLite unique constraint on `message_id` |
| **Anomaly Detection Recall** | $\ge 85\%$ on test anomalies | Formal evaluation on labeled test set |
| **False Positive Rate (FPR)** | $\le 7.0\%$ on normal data | Unsupervised evaluation matrix |
| **Alert Cooldown Enforcement** | Zero redundant alerts within 60s window | In-memory cooldown unit test verification |
| **Report Generation Latency** | $< 1.5$ seconds for 500 records | Benchmark on CSV and PDF generators |
| **Test Coverage** | 100% pass rate across core test suite | Automated `unittest` runner execution |
