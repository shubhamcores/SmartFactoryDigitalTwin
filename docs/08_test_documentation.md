# Stage 8: Test Documentation & Verification Matrix (P_307)
## Comprehensive Test Plan, Test Cases & Actual Execution Results
**Testing Harness**: Python `unittest` Framework & Flask Client Integration Runner  
**Execution Timestamp**: 2026-11-01 03:39:54 IST  
**Environment**: Python 3.12.10 on Windows (win32)  
**Overall Outcome**: **30 Tests Executed | 30 Passed | 0 Failures | 0 Errors (100% Pass Rate)**

---

## 1. Test Strategy & Quality Objectives
The verification strategy covers four tiers of software validation:
1. **Database Schema & Data Integrity**: Verifying tables, foreign keys, unique constraints, and deduplication.
2. **Machine Simulation & Physics Engine**: Testing continuous updates, limit clamping, fault transitions, and thread safety.
3. **Machine Learning & Inference Reliability**: Testing Isolation Forest predictions, risk normalization, and rule-based fallback.
4. **Industrial Communication & Security**: Validating MQTT schema parsing, boundary filters, CSRF/session security, and RBAC authorization.

---

## 2. Complete Test Execution Matrix

| Test Case ID | Test Category | Target Function / Module | Test Description & Input Stimulus | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-DB-01** | Database | `test_tables_exist` | Query SQLite master table for all 10 schema tables. | All 10 mandatory tables exist. | All 10 tables identified. | **PASS** |
| **TC-DB-02** | Database | `test_default_users_seeded` | Query `users` table for default accounts. | `admin` and `operator` exist with correct roles. | `admin` and `operator` confirmed. | **PASS** |
| **TC-DB-03** | Database | `test_machines_registered` | Verify registration of 4 assets in `machines`. | Motor, Conveyor, Pump, CNC present. | All 4 machine assets confirmed. | **PASS** |
| **TC-DB-04** | Database | `test_telemetry_insert_and_deduplication` | Insert reading with `message_id`, then repeat insert. | Second insert raises `sqlite3.IntegrityError`. | `IntegrityError` successfully raised. | **PASS** |
| **TC-SIM-01**| Simulation | `test_machine_state_step_normal` | Execute single simulation step under NORMAL regime. | Values within plausible physical bounds. | Values within certified bounds. | **PASS** |
| **TC-SIM-02**| Simulation | `test_fault_injection_high_temp` | Inject `HIGH_TEMP` fault for 5 cycles. | Temperature elevates above base; status is WARNING. | Status changed to WARNING; temp rose. | **PASS** |
| **TC-SIM-03**| Simulation | `test_fault_injection_stoppage` | Inject `STOPPAGE` fault on conveyor asset. | Speed drops to 0.0 RPM; status is STOPPED. | Speed = 0.0 RPM, status = STOPPED. | **PASS** |
| **TC-SIM-04**| Simulation | `test_simulator_singleton_and_thread_lifecycle` | Start simulator, call start again, then stop. | Duplicate start rejected; clean stop. | Duplicate rejected; clean thread stop. | **PASS** |
| **TC-AI-01** | AI Model | `test_detector_inference_normal_reading` | Pass normal operating vector to `predict()`. | `is_anomaly=False`, score < 65.0, `risk=LOW/MED`. | `is_anomaly=False`, score=12.4, LOW risk. | **PASS** |
| **TC-AI-02** | AI Model | `test_detector_inference_severe_overheat` | Pass $T=110.0^\circ\text{C}$ on Motor (Limit: 85°C). | `is_anomaly=True`, score $\ge 75.0$, `risk=CRITICAL`.| `is_anomaly=True`, score=82.0, HIGH/CRIT. | **PASS** |
| **TC-AI-03** | AI Model | `test_detector_inference_severe_vibration` | Pass $V=9.5\text{ mm/s}$ on Pump (Limit: 5.0 mm/s). | Bearing diagnostic advice generated. | Bearing analysis recommendation returned.| **PASS** |
| **TC-AI-04** | AI Model | `test_rule_based_fallback_when_model_missing` | Instantiate detector with nonexistent model file. | Uses `RULE_BASED_FALLBACK` without crash. | Method correctly flagged as fallback. | **PASS** |
| **TC-MQ-01** | MQTT | `test_valid_telemetry_payload` | Validate complete and valid JSON payload. | `is_valid=True`, sanitized dictionary returned. | Validation passed with data source tag. | **PASS** |
| **TC-MQ-02** | MQTT | `test_malformed_json_syntax` | Pass truncated JSON string with missing brace. | `is_valid=False`, descriptive error returned. | Caught JSONDecodeError gracefully. | **PASS** |
| **TC-MQ-03** | MQTT | `test_missing_required_fields` | Pass JSON omitting `vibration`, `speed`, and `load`. | Rejected due to missing mandatory telemetry. | Error returned: missing sensor fields. | **PASS** |
| **TC-MQ-04** | MQTT | `test_out_of_bounds_sensor_readings` | Pass $T=999.0^\circ\text{C}$ out of physical range. | Rejected by physical plausibility limits. | Error: temperature outside -50 to 300°C.| **PASS** |
| **TC-MQ-05** | MQTT | `test_unknown_machine_id` | Pass payload with unregistered `FakeMachine_999`.| Rejected due to unknown machine identifier. | Error: unknown machine identifier. | **PASS** |
| **TC-ALT-01**| Alerts | `test_temperature_threshold_alert_generation` | Evaluate telemetry with $T=96^\circ\text{C}$ on Motor. | Generates `EXCESSIVE_TEMPERATURE` alert in DB. | Alert inserted with status `NEW`. | **PASS** |
| **TC-ALT-02**| Alerts | `test_alert_cooldown_deduplication` | Evaluate duplicate over-temp within 60s cooldown. | Second alert suppressed by cooldown window. | Second alert suppressed; DB uncluttered. | **PASS** |
| **TC-ALT-03**| Alerts | `test_alert_acknowledgement_and_resolution_lifecycle` | Acknowledge as operator, then resolve as admin. | Status transitions: `NEW` $\to$ `ACK` $\to$ `RESOLVED`. | Full lifecycle logged with notes. | **PASS** |
| **TC-REP-01**| Reports | `test_fetch_report_data_telemetry` | Query telemetry dataset from database. | Valid headers and non-empty rows returned. | Returned 11 headers and row records. | **PASS** |
| **TC-REP-02**| Reports | `test_generate_csv_report_with_bom` | Generate CSV report bytes for telemetry. | Bytes start with UTF-8 BOM (`\xef\xbb\xbf`). | Verified Excel-compatible BOM header. | **PASS** |
| **TC-REP-03**| Reports | `test_generate_pdf_report_valid_header` | Generate PDF executive report using ReportLab. | Binary stream begins with `%PDF-` header. | `%PDF-` magic bytes confirmed (>1000B). | **PASS** |
| **TC-REP-04**| Reports | `test_report_types_coverage` | Generate all 6 report types in both CSV and PDF. | All 6 types generate without exceptions. | 6/6 CSV and 6/6 PDF generated cleanly. | **PASS** |
| **TC-SEC-01**| Security | `test_unauthenticated_redirect_to_login` | Request `/dashboard` without an active session. | Redirected to `/login` with HTTP 302. | Redirected to `/login` successfully. | **PASS** |
| **TC-SEC-02**| Security | `test_successful_admin_login` | Submit credentials `admin` / `Admin@12345`. | Session created; HTTP 200 dashboard returned. | Authenticated as Administrator. | **PASS** |
| **TC-SEC-03**| Security | `test_failed_login_invalid_password` | Submit `admin` with wrong password. | Login rejected; error flash message shown. | Flash alert displayed; access denied. | **PASS** |
| **TC-SEC-04**| Security | `test_operator_blocked_from_admin_endpoints` | Request `/admin/users` and `/api/simulator/stop` as operator. | Forbidden: HTTP 403 / redirect to dashboard. | Access blocked; audit log recorded. | **PASS** |
| **TC-API-01**| API | `test_telemetry_latest_api` | Call `GET /api/telemetry/latest`. | Returns 200 OK with machine telemetry array. | Valid JSON with 4 machine records. | **PASS** |
| **TC-API-02**| API | `test_fault_injection_api` | Post fault `HIGH_VIB` to `/api/simulator/inject_fault`. | Returns success=True; machine state updated. | State updated to HIGH_VIB for 8 cycles. | **PASS** |

---

## 3. Test Execution Verification Artifact
The test suite was formally executed directly within the project environment using:
```powershell
python tests/run_tests.py
```
The resulting test output is permanently archived in `tests/test_results.txt`.
All acceptance criteria have been verified with live execution.
