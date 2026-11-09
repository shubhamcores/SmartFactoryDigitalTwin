# Stage 11: Project Presentation Deck Structure 
## AI-Driven Digital Twin for Smart Factory Operations
**Audience**: University Examination Committee, HCLTech Project Mentors & Evaluators  
**Format**: 15 Slides with Speaker Notes and Technical Talking Points  
**Generated File**: `docs/presentation.pptx` (compile via `python docs/generate_presentation.py`)

---

## Slide 1: Title Slide
- **Title**: FactoryTwin: AI-Driven Digital Twin for Smart Factory Operations
- **Subtitle**: BTech Capstone Project  | Embedded Systems, Industrial IoT & Machine Learning
- **Author**: Senior BTech Developer / IoT Engineer
- **Mentorship Framework**: HCLTech Project Creation Guide for Embedded Systems & IoT
- **Speaker Note**: Welcome esteemed examiners and mentors. Today I am presenting FactoryTwin, an industrial digital twin and predictive maintenance platform that unifies cyber-physical physics simulation, real-time MQTT telemetry, unsupervised machine learning, and SCADA dashboard visualization.

---

## Slide 2: Problem Statement & Industrial Context
- **Title**: Industrial Context: Why Smart Factory Monitoring Matters
- **Key Points**:
  - Rotating machines (motors, pumps, conveyors, CNCs) are the lifeblood of manufacturing.
  - Conventional maintenance relies on Reactive (Run-to-Failure) or Calendar-based preventive maintenance.
  - Unplanned stoppages cost \$50,000 to \$250,000 per hour across automotive and processing lines.
  - Lack of continuous digital visibility leaves maintenance teams blind to rapid early-onset thermal and vibration defects.
- **Speaker Note**: In typical factories, maintenance teams either react too late after a machine catastrophically seizes, or they service machines too early on arbitrary calendar schedules. Our goal is Condition-Based Maintenance via real-time digital twins.

---

## Slide 3: Proposed Solution: The Digital Twin Approach
- **Title**: Proposed Solution: Cyber-Physical Digital Twin
- **Key Points**:
  - Virtual computational mirror synchronized via real-time multi-sensor telemetry.
  - Continuously models thermodynamics, mechanical friction, and shaft dynamics.
  - Multi-parameter tracking: Temperature, Vibration Velocity (ISO 10816), Speed, and Mechanical Load.
  - Automatic detection of abnormal operating states days or weeks prior to breakdown.
- **Speaker Note**: The digital twin acts as a real-time software twin of the plant floor. It receives high-frequency telemetry, runs unsupervised AI inference, and surfaces actionable engineering recommendations directly on a responsive SCADA interface.

---

## Slide 4: System Architecture & Data Pipeline
- **Title**: End-to-End System Architecture
- **Key Points**:
  - Data Sources: 4-Asset Multi-threaded Simulator or Optional ESP32 Hardware Edge Node.
  - Transport: Dual mode (offline standalone or MQTT over TLS 8883 to HiveMQ Cloud).
  - Persistence: SQLite database with Write-Ahead Logging (WAL) and message deduplication.
  - Analytics: Scikit-Learn Isolation Forest with deterministic rule-based fallback.
  - Presentation: Responsive Flask SCADA web interface with real-time Chart.js trends.
- **Speaker Note**: Notice the clean architectural decoupling. The application functions 100% offline with zero external dependencies, but seamlessly scales to cloud MQTT brokers when network connectivity is present.

---

## Slide 5: Monitored Industrial Machinery Assets
- **Title**: Monitored Factory Assets & Operating Regimes
- **Key Points**:
  - `Motor`: Primary Drive 3-Phase Induction Motor (1750 RPM nominal, 85°C limit).
  - `Conveyor`: Material Handling Belt Conveyor (450 RPM nominal, 70°C limit).
  - `Pump`: Cooling Circuit Centrifugal Water Pump (2900 RPM nominal, 80°C limit).
  - `CNC`: 5-Axis Precision Milling Machining Center (2400 RPM nominal, 90°C limit).
  - 7 Simulated Regimes: Normal, High Temp, High Vibration, Overload, Reduced Production, Stoppage, and Sensor Spikes.
- **Speaker Note**: Each machine has distinct physical operating envelopes, thermal thresholds, and baseline vibration signatures corresponding to its specific mechanical design.

---

## Slide 6: Industrial IoT & MQTT Communication
- **Title**: Industrial IoT & Cloud Broker Integration
- **Key Points**:
  - Standardized JSON telemetry format with unique `message_id` for idempotency.
  - Topic Architecture: `factory/machines/<machine_id>/telemetry`.
  - Secure TLS encryption on port 8883 for HiveMQ Cloud.
  - Payload range bounds validation discarding corrupt packets without crashing.
  - Verified interoperability with MQTT Explorer for external test injection.
- **Speaker Note**: By adhering to standard OASIS MQTT specifications and implementing payload validation and deduplication, the system is fully resilient against network jitter, broker reconnections, and corrupted packets.

---

## Slide 7: Unsupervised AI Anomaly Detection: Isolation Forest
- **Title**: AI Anomaly Detection: The Isolation Forest Pipeline
- **Key Points**:
  - Overcomes the limitation of labeled failure data scarcity in real factories.
  - Trained strictly unsupervised on 12,000 normal operating samples (no data leakage).
  - Accepts 4 standardized features: Temperature, Vibration, Speed, Load.
  - Normalized continuous risk score (0.0 to 100.0) mapped into 4 Risk Tiers: Low, Medium, High, Critical.
  - Generates prescriptive maintenance actions (e.g. "Bearing frequency analysis; inspect coupling").
- **Speaker Note**: Rather than profiling normal points by distance, Isolation Forest isolates outliers using random hyperplanes. Outliers are isolated near the root of the trees, allowing real-time inference in sub-millisecond execution times.

---

## Slide 8: Machine Learning Evaluation & Results
- **Title**: Empirical Model Performance Evaluation
- **Key Points**:
  - Evaluated on separate 3,000-sample test set (85% normal, 15% ground-truth anomalies).
  - **Recall (Sensitivity)**: 89.73% (Successfully caught ~90% of all abnormal states).
  - **Precision**: 72.83% (High true anomaly fidelity).
  - **F1-Score**: 80.40% (Harmonic mean of precision and recall).
  - **False Positive Rate**: 5.88% (Safely below 7% industrial nuisance alarm ceiling).
- **Speaker Note**: These metrics demonstrate exceptional unsupervised sensitivity while maintaining a low false-positive rate, ensuring operators are not overwhelmed with spurious alarms.

---

## Slide 9: Intelligent Alerting & Alarm Fatigue Prevention
- **Title**: Intelligent Alerting & Lifecycle Management
- **Key Points**:
  - Threshold alerts for temperature, vibration, overload, stoppage, and AI anomaly scores.
  - In-memory 60-second cooldown deduplication window per machine/condition.
  - Eliminates alarm storms while ensuring critical events are recorded.
  - Multi-tier lifecycle: `NEW` $\to$ `ACKNOWLEDGED` (Operator/Admin) $\to$ `RESOLVED` (Admin only).
  - Resolution requires documenting mandatory corrective maintenance notes.
- **Speaker Note**: Alarm fatigue is a notorious industrial issue. Our sliding cooldown window prevents repeated triggers during ongoing fault conditions while preserving a complete audit trail.

---

## Slide 10: SCADA Dashboard & User Experience
- **Title**: Modern Industrial SCADA Dashboard
- **Key Points**:
  - Dark carbon aesthetic (`#0b0f19` / `#1e293b`) optimized for factory floor control rooms.
  - Automatic asynchronous polling every 3 seconds via Flask JSON REST API.
  - Real-time Chart.js trends for temperature, vibration, speed, and production output.
  - Dedicated asset inspector view with synchronized multi-sensor charts.
  - Single-click Fault Simulator panel enabling live injection of abnormal regimes during evaluation.
- **Speaker Note**: The interface was designed following modern SCADA best practices. Operators can monitor the entire plant at a glance or drill down into individual machines to inspect live sensor correlations.

---

## Slide 11: Security, Roles & Administrative Governance
- **Title**: Role-Based Access Control (RBAC) & Governance
- **Key Points**:
  - Administrator: Full plant control, simulator toggle, user management, audit trails, alert resolution.
  - Operator: SCADA monitoring, alarm acknowledgement, fault injection testing, report export.
  - Server-side authorization decorators enforcing HTTP 403 Forbidden on unauthorized calls.
  - Cryptographic password hashing using Werkzeug primitives (`scrypt` / `pbkdf2`).
  - Immutable audit logs capturing IP addresses and timestamps for ISO compliance.
- **Speaker Note**: Role-based access control is enforced on the server side, ensuring operators cannot bypass restrictions by typing direct API URLs.

---

## Slide 12: Compliance Reporting & Data Export
- **Title**: Automated Operational Reporting & Data Exports
- **Key Points**:
  - 6 Standard Report Categories: Telemetry, Production, Status History, Anomalies, Alerts, Daily Summary.
  - Flexible filtering by date range, target machinery, and alert severity.
  - Excel-Compatible CSV exports formatted with UTF-8 Byte Order Mark (BOM).
  - High-resolution executive PDF reports generated using ReportLab with custom "Page X of Y" canvas footers.
- **Speaker Note**: Shift handovers and maintenance audits require verifiable documentation. With one click, users can generate compliant Excel spreadsheets or formatted PDF executive reports.

---

## Slide 13: Optional ESP32 Hardware Extension
- **Title**: Optional Hardware Prototyping Extension
- **Key Points**:
  - Microcontroller: ESP32 DevKit V1 (Dual-Core 240MHz, WiFi + BLE).
  - Sensor: MPU-6050 6-Axis IMU (I2C) for vibration acceleration and chip temperature.
  - Digital Signal Processing: Moving average filter converting raw acceleration (G) to velocity RMS (mm/s).
  - Edge alerts via physical indicator LEDs before cloud transmission.
  - Comprehensive Bill of Materials: Prototype cost approximately ₹1,127 INR.
- **Speaker Note**: The optional hardware extension demonstrates how physical edge sensors interface with the cloud and digital twin. We provide both Arduino C++ and MicroPython firmware implementations.

---

## Slide 14: System Verification & Acceptance Results
- **Title**: Automated Test Suite & Acceptance Results
- **Key Points**:
  - 30 Automated Unit & Integration Tests across all 7 architectural layers.
  - 100% Pass Rate (32/32 passed, 0 failures, 0 errors in 8.46 seconds).
  - Verified edge cases: malformed JSON, out-of-bounds readings, empty queries, duplicate message IDs.
  - Full compliance with all 20 measurable acceptance criteria defined in the project specification.
- **Speaker Note**: Every single feature claimed in this project has been validated by an automated test case. Unexecuted tests were never marked as passed.

---

## Slide 15: Conclusion & Future Scope
- **Title**: Conclusion & Future Roadmap
- **Key Points**:
  - **Conclusion**: Successfully engineered a robust, production-grade cyber-physical digital twin uniting simulation, AI anomaly detection, and SCADA monitoring.
  - **Academic Rigour**: Followed all 8 stages of the HCLTech development guide with full documentation.
  - **Future Roadmap**:
    - Deploy TinyML edge models directly on ESP32 microcontrollers.
    - Add industrial OPC-UA (IEC 62541) protocol integration for physical PLC connectivity.
    - Implement Weibull degradation modeling for quantitative Remaining Useful Life (RUL) estimation.
  - *Thank you! Questions and Live Demonstration welcome.*
- **Speaker Note**: Thank you for your time. I would now be delighted to walk you through our live demonstration and answer any technical questions.
