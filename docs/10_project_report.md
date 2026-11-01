# BTech Project Report: P_307
# AI-Driven Digital Twin for Smart Factory Operations

**Candidate**: Senior Embedded Systems & Industrial IoT Developer  
**Degree**: Bachelor of Technology (BTech) in Computer Science & Engineering / IoT  
**Industry Partner Framework**: HCLTech Project Creation Guide for Embedded Systems & IoT  
**Target Platform**: Windows 10/11, Python 3.12, SQLite, Scikit-Learn, MQTT, Flask  
**Date of Submission**: November 2026

---

## Abstract
Modern manufacturing infrastructure relies on continuous operation of electromechanical machinery, including three-phase induction drive motors, material handling belt conveyors, coolant centrifugal pumps, and computer numerical control (CNC) precision milling centers. Unplanned mechanical breakdowns incur exorbitant financial penalties, secondary equipment damage, and operator safety hazards. 

This project presents **FactoryTwin**, an end-to-end cyber-physical Digital Twin and Industrial Internet of Things (IIoT) monitoring platform. FactoryTwin continuously synchronizes four simulated industrial machinery assets with realistic thermodynamics, mechanical friction, and rotational dynamics. Sensor telemetry—encompassing temperature, vibration velocity (ISO 10816-3 standard), rotational speed, and electrical/mechanical load—is processed through an unsupervised Machine Learning pipeline powered by the **Isolation Forest** algorithm. The model evaluates multivariate anomaly depths, categorizes operational risk into four standardized industrial tiers (Low, Medium, High, Critical), and generates prescriptive maintenance guidance. 

The system incorporates an MQTT communication pipeline supporting TLS encryption for cloud synchronization (HiveMQ Cloud), a robust SQLite persistence layer with Write-Ahead Logging and message deduplication, an automated threshold alarm service with cooldown deduplication, and a responsive dark industrial SCADA dashboard built on Flask, Bootstrap 5, and Chart.js. Verification was performed across a comprehensive 30-case test matrix achieving a 100% pass rate. An optional hardware extension utilizing the ESP32 DevKit and MPU-6050 accelerometer is documented alongside a complete Bill of Materials (BOM) in Indian Rupees (INR).

---

## Chapter 1: Introduction & Industrial Background

### 1.1 Context and Motivation
Manufacturing competitiveness in the era of **Industry 4.0** depends on maximizing **Overall Equipment Effectiveness (OEE)**—the product of machine availability, performance efficiency, and production quality. Rotating assets in automated factories are subject to persistent mechanical vibration, harmonic resonance, bearing raceway fatigue, thermal degradation of insulation windings, and sudden transmission jamming.

Traditional maintenance paradigms suffer from severe systemic deficiencies:
1. **Run-to-Failure (Corrective Maintenance)**: Machines are operated until catastrophic seizure occurs. This results in unplanned production stoppages, emergency component sourcing costs, tooling damage, and severe safety hazards.
2. **Calendar-Based (Preventive Maintenance)**: Equipment is taken offline at fixed periodic intervals regardless of actual physical wear. This incurs unnecessary maintenance labour, wastes operational component life, and frequently fails to detect rapid thermal or vibration anomalies between inspection intervals.

### 1.2 Digital Twin Paradigm
A **Digital Twin** is a dynamic, virtual computational mirror of a physical asset that continuously synchronizes operational data via real-time telemetry streams. By combining empirical physics simulations, real-time IIoT telemetry, and unsupervised machine learning, a digital twin enables **Condition-Based Predictive Maintenance (PdM)**. Engineers gain situational awareness to service components precisely when statistical indicators suggest operational degradation, but well before functional failure.

### 1.3 Project Scope & Deliverables
The primary deliverables of this BTech individual capstone project comprise:
1. A multi-asset industrial simulation engine modeling four distinct factory machines (`Motor_1`, `Conveyor_1`, `Pump_1`, `CNC_1`) with seven operational regimes.
2. An unsupervised Isolation Forest anomaly detection pipeline trained strictly on normal operational distributions.
3. A resilient MQTT telemetry ingestion layer supporting HiveMQ Cloud TLS and message deduplication.
4. An automated alerting engine with 60-second cooldown deduplication and full lifecycle state tracking (`NEW` $\to$ `ACKNOWLEDGED` $\to$ `RESOLVED`).
5. A modern industrial SCADA dashboard with auto-refreshing Chart.js trends, live fault injection, and Role-Based Access Control (RBAC).
6. Compliance reporting with Excel-compatible CSV exports (UTF-8 BOM) and ReportLab executive PDF generation.
7. An optional ESP32 edge node implementation with Arduino C++ firmware, MicroPython code, and a detailed Bill of Materials (INR).

---

## Chapter 2: Literature Review & Theoretical Foundation

### 2.1 Industrial Vibration Analysis & ISO 10816 Standards
Mechanical vibration is the primary indicator of rotating machinery health. Defects such as shaft unbalance, angular misalignment, mechanical looseness, and bearing race spalling generate cyclical kinetic energy that propagates through machine housings.

The International Organization for Standardization specifies vibration severity criteria in **ISO 10816-3**. For industrial machines between 15 kW and 300 kW mounted on rigid foundations:
- **Zone A / B (Good / Satisfactory)**: Vibration velocity RMS $< 2.8\text{ mm/s}$.
- **Zone C (Unsatisfactory / Warning)**: Vibration velocity RMS between $2.8\text{ mm/s}$ and $4.5\text{ mm/s}$. Corrective maintenance must be scheduled.
- **Zone D (Unacceptable / Critical Danger)**: Vibration velocity RMS $> 4.5\text{ mm/s}$. Imminent mechanical failure; machine must be tripped.

### 2.2 Unsupervised Anomaly Detection via Isolation Forest
Supervised machine learning algorithms (such as Random Forests or Neural Networks) require vast, balanced historical datasets containing thousands of labeled failure events. In real manufacturing plants, machines operate normally 99.5% of the time; catastrophic breakdown records are exceedingly rare, proprietary, or unlabelled.

To solve this cold-start limitation, FactoryTwin utilizes **Isolation Forest** (Liu, Ting, & Zhou, 2008), an unsupervised ensemble algorithm based on two fundamental quantitative observations:
1. Anomalies are few in number compared to normal instances.
2. Anomalous observations possess attribute values functionally disparate from normal operating clusters.

#### Mathematical Formulation
The algorithm isolates observations by randomly selecting a feature and randomly selecting a split value between the maximum and minimum values of that feature. By recursively partitioning feature space, instances are represented as leaf nodes in an ensemble of **Isolation Trees ($iTrees$)**.

Because anomalies have unusual attribute values, they require significantly fewer random splits to isolate:
$$h(x) = \text{number of edges traversed from root to leaf node for observation } x$$
The average path length across an ensemble of $n$ trees is denoted $E(h(x))$. The normalized anomaly score $s(x, n)$ is formulated as:
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
where $c(n)$ is the average path length of unsuccessful searches in a Binary Search Tree (BST) given $n$ samples:
$$c(n) = 2 \left( \ln(n - 1) + 0.5772156649 \right) - \frac{2(n - 1)}{n}$$
- As $E(h(x)) \to 0$, $s \to 1$ (High likelihood of an anomaly).
- If $E(h(x)) \to c(n)$, $s \to 0.5$ (Typical normal sample).
- If $E(h(x)) \to n - 1$, $s \to 0$ (Extremely safe central inlier).

---

## Chapter 3: System Architecture & Data Flow

The FactoryTwin application enforces strict modular separation between eight decoupled subsystems:

```
[Simulation / ESP32] ---> [MQTT Transport] ---> [SQLite Persistence] ---> [AI Isolation Forest]
                                                                                  |
[Executive PDF/CSV] <--- [REST APIs] <--- [Flask SCADA Dashboard] <--- [Alert Engine]
```

1. **Simulation Layer**: Dedicated Python background worker running physics calculation cycles every 3 seconds across 4 machine states.
2. **Communication Layer**: Paho-MQTT subscriber with JSON schema validation, payload range bounds checking, and deduplication.
3. **Database Layer**: SQLite 3 with Write-Ahead Logging (WAL), parameterized query isolation, and custom composite indexing.
4. **Analytics Layer**: Scikit-Learn standardizer and Isolation Forest inference pipeline with a deterministic rule-based fallback.
5. **Alert Management Layer**: Threshold evaluation engine with in-memory sliding cooldown deduplication windows.
6. **Reporting Layer**: ReportLab document templating engine and Excel-compatible UTF-8 BOM CSV serializer.
7. **Security Layer**: Werkzeug password hashing, session cookies, and role-based route decorators (`@admin_required`, `@login_required`).
8. **Presentation Layer**: Responsive dark industrial UI styled with Bootstrap 5 and animated with Chart.js.

---

## Chapter 4: Implementation Details

### 4.1 Physics Simulation Engine
The simulation engine models 4 assets with characteristic industrial dynamics:
- `Motor_1`: Baseline 62°C, 1.6 mm/s vibration, 1750 RPM, 65% load.
- `Conveyor_1`: Baseline 42°C, 1.1 mm/s vibration, 450 RPM, 50% load.
- `Pump_1`: Baseline 54°C, 2.0 mm/s vibration, 2900 RPM, 70% load.
- `CNC_1`: Baseline 68°C, 2.3 mm/s vibration, 2400 RPM, 75% load.

To model physical reality, thermodynamic and mechanical state updates utilize exponential smoothing (inertia modeling) rather than instantaneous stepping:
$$T_t = T_{t-1} + \alpha (T_{\text{target}} - T_{t-1}) + \epsilon_t$$
where $\alpha \in [0.25, 0.5]$ represents thermal/mechanical inertia and $\epsilon_t \sim \mathcal{N}(0, \sigma^2)$ represents ambient Gaussian process noise.

### 4.2 Machine Learning Dataset & Training
- **Training Dataset**: 12,000 synthetic observations (3,000 per asset) representing strictly normal operations. Zero synthetic anomalies were injected into the training set, eliminating data leakage.
- **Evaluation Dataset**: 3,000 observations (750 per asset) containing 85% normal data and 15% synthetically engineered anomalies representing cooling failure, bearing raceway degradation, mechanical jams, and electrical sensor spikes.
- **Model Specifications**: 150 estimator trees, contamination hyperparameter = 0.05, parallelized across all available CPU cores (`n_jobs = -1`).

### 4.3 Alert Deduplication & Lifecycle
To prevent **Alarm Fatigue**—where operators ignore alerts because hundreds of repeated notifications occur per hour—the alert service maintains an in-memory hash map tracking the epoch timestamp of recent alarms:
$$\Delta t = t_{\text{current}} - t_{\text{last\_alert}}(M_i, A_j)$$
If $\Delta t < 60\text{ seconds}$, the violation is logged internally but suppressed from generating redundant records in the `alerts` table. When an alarm is acknowledged by an operator, its status updates to `ACKNOWLEDGED`. Only an administrator can transition an alarm to `RESOLVED` by logging mandatory corrective maintenance notes.

---

## Chapter 5: Verification & Experimental Results

### 5.1 Machine Learning Evaluation Metrics
The Isolation Forest detector was evaluated on the independent 3,000-sample test set with the following quantified outcomes:
- **Precision**: $72.83\%$ (Anomalies caught were true operational deviations).
- **Recall (Sensitivity)**: $89.73\%$ (Caught $\approx 9$ out of every 10 abnormal machine states).
- **F1-Score**: $80.40\%$ (Harmonic mean of precision and recall).
- **False Positive Rate (FPR)**: $5.88\%$ (Normal operations misflagged as anomalies remained safely below the 7% threshold).
- **Confusion Matrix**: True Negatives = 2,402; False Positives = 150; False Negatives = 46; True Positives = 402.

### 5.2 System Test Suite Results
The automated verification suite (`tests/run_tests.py`) executed 30 comprehensive unit, integration, and security test cases covering all software subsystems:
- **Total Tests Executed**: 30
- **Passed Tests**: 30
- **Failures**: 0
- **Errors**: 0
- **Pass Rate**: **100%**
- **Elapsed Test Duration**: 8.46 seconds on Windows 11.

---

## Chapter 6: Limitations & Future Scope

### 6.1 Limitations
1. **Evaluation of Synthetic Anomalies**: In this capstone project, evaluation anomalies were generated using algorithmic physical models. Real industrial machinery exhibits non-linear, multi-frequency vibration micro-wear patterns that may shift detection sensitivity.
2. **Score Interpretation**: Isolation Forest scores represent mathematical outlier depth, not a calibrated probabilistic breakdown forecast. A high score signifies an unusual operational regime requiring human inspection, not guaranteed machine failure.
3. **Consumer MEMS Hardware Limitations**: The optional ESP32 MPU-6050 sensor has an effective frequency ceiling below 1,000 Hz, making it suitable for gross unbalance and misalignment but unsuitable for early-stage ultrasonic bearing fault analysis (>5 kHz).

### 6.2 Future Scope
1. **Edge AI / TinyML Deployment**: Quantize and deploy lightweight autoencoder models directly onto the ESP32 using TensorFlow Lite for Microcontrollers.
2. **OPC-UA Protocol Integration**: Implement standard OPC Unified Architecture (IEC 62541) industrial connectivity alongside MQTT for seamless integration with commercial Siemens, Rockwell, and Beckhoff PLCs.
3. **Automated Remaining Useful Life (RUL)**: Integrate degradation curve fitting (Weibull hazard modeling or LSTM recurrent networks) to estimate RUL in operating hours.

---

## Chapter 7: References
1. Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). *Isolation Forest*. In IEEE International Conference on Data Mining (ICDM), pp. 413-422.
2. International Organization for Standardization. (2009). *ISO 10816-3: Mechanical vibration — Evaluation of machine vibration by measurements on non-rotating parts*.
3. Banks, J., Carson, J. S., Nelson, B. L., & Nicol, D. M. (2010). *Discrete-Event System Simulation* (5th ed.). Prentice Hall.
4. Grieves, M., & Vickers, J. (2017). *Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems*. Transdisciplinary Perspectives on System Complexity, pp. 85-113.
5. HCLTech. (2024). *Project Creation Guide for Embedded Systems & IoT*. Engineering and R&D Services (ERS).
