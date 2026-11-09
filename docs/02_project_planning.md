# Stage 2: Milestone-Based Project Planning 
## 20–30 Day Individual Engineering Plan
**Development Methodology**: HCLTech Embedded Systems & IoT Project Creation Framework

---

## 1. Project Work Breakdown Structure (WBS)
The project lifecycle is structured into four sequential phases spanning a typical 25-day academic sprint:
1. **Phase 1: Exploration & Requirements Analysis (Days 1 – 6)**
2. **Phase 2: Core Engineering & Development (Days 7 – 17)**
3. **Phase 3: System Integration & Optimization (Days 18 – 22)**
4. **Phase 4: Documentation, Verification & Presentation (Days 23 – 25)**

---

## 2. Milestone Schedule & Acceptance Criteria

```
+-----------------------------------------------------------------------------------------+
|                                25-DAY MILESTONE ROADMAP                                 |
+-----------------------------------------------------------------------------------------+
| Phase 1: EXPLORATION (Days 1 - 6)                                                       |
|   [M1.1] Problem Definition & Literature Survey                                         |
|   [M1.2] Software Requirements Specification (SRS) & Architecture Blueprint             |
+-----------------------------------------------------------------------------------------+
| Phase 2: DEVELOPMENT (Days 7 - 17)                                                      |
|   [M2.1] SQLite Relational Schema & Seeding Engine                                      |
|   [M2.2] Machine Physics Simulation Engine (4 Assets)                                   |
|   [M2.3] Isolation Forest ML Pipeline (Dataset Gen, Training, Fallback)                 |
|   [M2.4] MQTT Transport Layer & HiveMQ Cloud Integration                                |
|   [M2.5] Flask SCADA Web Interface, REST API & RBAC Security                            |
+-----------------------------------------------------------------------------------------+
| Phase 3: OPTIMIZATION (Days 18 - 22)                                                    |
|   [M3.1] Alert Cooldown Deduplication & Lifecycle Engine                                |
|   [M3.2] ReportLab Executive PDF & CSV Reporting Services                               |
|   [M3.3] Optional ESP32 Firmware & Hardware Prototyping Docs                            |
|   [M3.4] End-to-End Automated Test Suite Verification (32 Tests)                        |
+-----------------------------------------------------------------------------------------+
| Phase 4: PRESENTATION (Days 23 - 25)                                                    |
|   [M4.1] HCLTech Project Report & Technical Documentation                               |
|   [M4.2] Slide Deck Presentation Generation (PowerPoint)                                |
|   [M4.3] Live Demonstration Script & Final Packaging ZIP                               |
+-----------------------------------------------------------------------------------------+
```

### Detailed Milestone Breakdown

| Milestone ID | Phase | Target Timeline | Deliverable Description | Measurable Acceptance Criteria |
| :--- | :--- | :---: | :--- | :--- |
| **M1.1** | Exploration | Days 1–3 | Industrial IoT survey, problem statement formulation, digital twin architectural research. | Problem Statement document approved with quantified business rationale. |
| **M1.2** | Exploration | Days 4–6 | Formal Software Requirements Specification (SRS), Data Flow Diagrams, and technology stack selection. | Complete IEEE 830-aligned SRS with functional and non-functional requirements. |
| **M2.1** | Development | Days 7–8 | SQLite database architecture, schema migrations, indexing, and seed initialization. | Database initializes via `python database.py` with zero errors; default users created. |
| **M2.2** | Development | Days 9–10 | Multi-machine physics simulation engine supporting 7 operating regimes and fault injection. | Generates continuous telemetry every 3s across 4 machines; thread-safe start/stop verified. |
| **M2.3** | Development | Days 11–13 | Isolation Forest training on 12k normal samples; evaluation on 3k labeled anomaly samples. | Precision $\ge 70\%$, Recall $\ge 85\%$, F1 $\ge 0.75$; model saved to `.joblib`. |
| **M2.4** | Development | Days 14–15 | MQTT publisher and subscriber modules supporting HiveMQ Cloud TLS and local brokers. | Payload schema validated; corrupt JSON discarded safely without server crash. |
| **M2.5** | Development | Days 16–17 | Flask web application, modern dark SCADA dashboard, Chart.js trends, and RBAC authentication. | Secure login functional; operator restricted from admin routes; UI updates every 3s. |
| **M3.1** | Optimization | Days 18–19 | Alerting engine with threshold checks, 60s cooldown deduplication, and ACK/Resolve states. | Zero duplicate alerts created during 60s cooldown window; full lifecycle verified. |
| **M3.2** | Optimization | Days 20–21 | On-demand Excel-compatible CSV export (UTF-8 BOM) and ReportLab executive PDF generation. | Downloadable CSV opens cleanly in Excel; PDF generates multi-page styled layout. |
| **M3.3** | Optimization | Day 22 | ESP32 DevKit Arduino C++ firmware, MicroPython code, circuit schematic, and BOM in INR. | Firmware compiles without syntax errors; BOM documented with realistic INR costs. |
| **M3.4** | Optimization | Day 22 | Automated unit and integration test suite covering database, simulation, AI, alerts, reports, API. | 30 out of 30 tests pass with zero failures (`OK` status in `tests/test_results.txt`). |
| **M4.1** | Presentation | Day 23 | Comprehensive BTech Project Report (30+ page equivalent), User Manual, and Test Documentation. | All 12 required HCLTech documents completed in `docs/` folder. |
| **M4.2** | Presentation | Day 24 | Professional PowerPoint presentation slide deck and automated generation script. | PPTX presentation compiled and verified. |
| **M4.3** | Presentation | Day 25 | Live demonstration rehearsal, viva voice question prep, and source code archive ZIP packaging. | Self-contained, runnable ZIP package generated and verified. |

---

## 3. Project Risk Assessment & Mitigation Strategy

| Risk Factor | Severity | Probability | Mitigation Strategy Implemented in Project |
| :--- | :---: | :---: | :--- |
| **No Internet / Cloud Broker Outage** | High | Medium | Simulator operates 100% offline using internal thread loop. MQTT is purely optional. |
| **Missing AI Model / Cold Start** | High | Low | If `.joblib` model file is absent, system auto-trains on startup or falls back to `RULE_BASED_FALLBACK` detector. |
| **Alert Storms (Alarm Fatigue)** | High | High | Implemented in-memory sliding cooldown (`Config.ALERT_COOLDOWN_SECONDS = 60`) per asset. |
| **Telemetry Flooding / Concurrency** | Medium | Medium | SQLite configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and parameterized query timeouts. |
| **Windows PowerShell Execution Policy** | Medium | High | Documented direct execution path using `.venv\Scripts\python.exe` without requiring script activation permissions. |
