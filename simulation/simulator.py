"""
Industrial Machine Digital Twin Simulator (P_307)
Simulates continuous factory operations for 4 machines:
  - Motor (Induction Motor)
  - Conveyor (Material Conveyor)
  - Pump (Coolant Centrifugal Pump)
  - CNC (5-Axis Milling Center)

Supports 7 Operational Regimes:
  1. NORMAL: Within nominal engineering tolerances
  2. HIGH_TEMP: Thermal runaway / cooling failure
  3. HIGH_VIB: Bearing raceway wear / mechanical unbalance
  4. EXCESSIVE_LOAD: Mechanical jam / overload
  5. REDUCED_PRODUCTION: Starvation / sub-optimal speed
  6. STOPPAGE: Emergency stop / power trip
  7. ABNORMAL_SENSOR: Transient electrical glitch / sensor failure

Thread-safe lifecycle controls with duplicate-worker prevention.
"""

import time
import random
import logging
import threading
from datetime import datetime
from database import get_db_connection
from config import Config
from ai_model.predict import get_anomaly_detector
from services.alert_service import evaluate_telemetry_for_alerts

logger = logging.getLogger(__name__)

class MachineState:
    """Represents the real-time physical simulation state of a single machine."""

    def __init__(self, machine_id: str, cfg: dict):
        self.machine_id = machine_id
        self.cfg = cfg
        self.base_temp = cfg["base_temp"]
        self.base_vib = cfg["base_vibration"]
        self.base_rpm = cfg["base_rpm"]
        self.base_load = cfg["base_load"]
        self.max_temp = cfg["max_temp"]
        self.max_vib = cfg["max_vibration"]
        self.max_rpm = cfg["max_rpm"]
        self.max_load = cfg["max_load"]
        self.nominal_rate = cfg.get("production_rate", 5)

        # Dynamic physics state
        self.temp = self.base_temp
        self.vib = self.base_vib
        self.rpm = self.base_rpm
        self.load = self.base_load
        self.production_count = 0
        self.status = "RUNNING"
        self.condition = "NORMAL"
        self.fault_cycles_remaining = 0

    def set_condition(self, condition: str, duration_cycles: int = 15):
        """Inject an operating condition or fault for a set number of simulation cycles."""
        self.condition = condition.upper()
        self.fault_cycles_remaining = duration_cycles
        logger.info(f"Machine {self.machine_id} entered condition: {self.condition} ({duration_cycles} cycles)")

    def step(self):
        """Simulate one continuous physics update step."""
        if self.fault_cycles_remaining > 0:
            self.fault_cycles_remaining -= 1
            if self.fault_cycles_remaining == 0:
                self.condition = "NORMAL"
                logger.info(f"Machine {self.machine_id} returned to NORMAL condition")

        cond = self.condition

        if cond == "NORMAL":
            target_temp = self.base_temp + random.uniform(-1.5, 1.5)
            target_vib = self.base_vib + random.uniform(-0.15, 0.15)
            target_rpm = self.base_rpm + random.uniform(-15.0, 15.0)
            target_load = self.base_load + random.uniform(-3.0, 3.0)
            self.status = "RUNNING"
            self.production_count += self.nominal_rate

        elif cond == "HIGH_TEMP":
            # Progressive thermal rise above max threshold
            target_temp = self.max_temp + random.uniform(5.0, 20.0)
            target_vib = self.base_vib + random.uniform(0.1, 0.5)
            target_rpm = self.base_rpm * 0.95
            target_load = self.base_load + 10.0
            self.status = "WARNING"
            self.production_count += int(self.nominal_rate * 0.8)

        elif cond == "HIGH_VIB":
            # Significant vibration jump (bearing defect)
            target_temp = self.base_temp + random.uniform(3.0, 8.0)
            target_vib = self.max_vib + random.uniform(1.5, 4.5)
            target_rpm = self.base_rpm + random.uniform(-40.0, 40.0)
            target_load = self.base_load + random.uniform(5.0, 12.0)
            self.status = "WARNING"
            self.production_count += int(self.nominal_rate * 0.6)

        elif cond == "EXCESSIVE_LOAD":
            # Severe mechanical drag / jam
            target_temp = self.max_temp + random.uniform(2.0, 10.0)
            target_vib = self.max_vib * 0.9
            target_rpm = max(100.0, self.base_rpm * 0.4)
            target_load = min(100.0, self.max_load + random.uniform(5.0, 9.0))
            self.status = "CRITICAL"
            self.production_count += 1

        elif cond == "REDUCED_PRODUCTION":
            # Throttled line / starvation
            target_temp = self.base_temp - 5.0
            target_vib = self.base_vib * 0.7
            target_rpm = self.base_rpm * 0.5
            target_load = self.base_load * 0.4
            self.status = "IDLE"
            self.production_count += 1

        elif cond == "STOPPAGE":
            # Emergency stop or trip - immediate deceleration to 0
            self.temp = max(25.0, self.temp - 1.5)
            self.vib = 0.05
            self.rpm = 0.0
            self.load = 0.0
            self.status = "STOPPED"
            return {
                "machine_id": self.machine_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "temperature": round(float(self.temp), 2),
                "vibration": round(float(self.vib), 3),
                "speed": 0.0,
                "load": 0.0,
                "status": self.status,
                "production_count": int(self.production_count),
                "data_source": "SIMULATED",
                "active_condition": self.condition
            }

        elif cond == "ABNORMAL_SENSOR":
            # Erratic sensor spike
            target_temp = random.choice([125.0, -10.0, 140.0])
            target_vib = random.uniform(12.0, 28.0)
            target_rpm = random.choice([0.0, 4500.0])
            target_load = 100.0
            self.status = "CRITICAL"
            self.production_count += 0

        else:
            target_temp = self.base_temp
            target_vib = self.base_vib
            target_rpm = self.base_rpm
            target_load = self.base_load
            self.status = "RUNNING"

        # Apply smooth thermal and inertia transitions (exponential moving approach)
        self.temp += 0.25 * (target_temp - self.temp) + random.uniform(-0.3, 0.3)
        self.vib += 0.4 * (target_vib - self.vib) + random.uniform(-0.05, 0.05)
        self.rpm += 0.5 * (target_rpm - self.rpm) + random.uniform(-5.0, 5.0)
        self.load += 0.35 * (target_load - self.load) + random.uniform(-1.0, 1.0)

        # Clamp physical bounds
        self.temp = max(-20.0, min(200.0, self.temp))
        self.vib = max(0.01, min(50.0, self.vib))
        self.rpm = max(0.0, min(8000.0, self.rpm))
        self.load = max(0.0, min(100.0, self.load))

        return {
            "machine_id": self.machine_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperature": round(float(self.temp), 2),
            "vibration": round(float(self.vib), 3),
            "speed": round(float(self.rpm), 1),
            "load": round(float(self.load), 1),
            "status": self.status,
            "production_count": int(self.production_count),
            "data_source": "SIMULATED",
            "active_condition": self.condition
        }


class SimulationEngine:
    """Thread-safe simulator coordinator controlling all machine digital twins."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SimulationEngine, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.machines = {
            m_id: MachineState(m_id, cfg)
            for m_id, cfg in Config.MACHINES.items()
        }
        self.source_modes = {
            m_id: Config.DEFAULT_DATA_SOURCE_MODE
            for m_id in Config.MACHINES
        }
        self.interval = Config.SIMULATION_INTERVAL
        self._thread = None
        self._stop_event = threading.Event()
        self._is_running = False
        self._mqtt_publisher = None  # Optional MQTT hook
        self._initialized = True

    def set_source_mode(self, machine_id: str, mode: str) -> bool:
        """
        Set data source mode to 'SYNTHETIC' or 'ESP32'.
        If machine_id is 'ALL', sets mode across all machines.
        """
        mode = mode.upper()
        if mode not in ("SYNTHETIC", "ESP32"):
            return False

        with self._lock:
            if machine_id == "ALL":
                for m_id in self.source_modes:
                    self.source_modes[m_id] = mode
                logger.info(f"Data source mode set to '{mode}' for ALL machines.")
            elif machine_id in self.source_modes:
                self.source_modes[machine_id] = mode
                logger.info(f"Data source mode for {machine_id} set to '{mode}'.")
            else:
                return False
            return True

    def get_source_modes(self) -> dict:
        """Retrieve current data source modes per machine."""
        with self._lock:
            return dict(self.source_modes)

    def set_mqtt_publisher(self, publisher):
        """Attach an optional MQTT publisher to forward simulated telemetry over MQTT."""
        self._mqtt_publisher = publisher

    def is_running(self) -> bool:
        """Check if the simulation background thread is actively executing."""
        return self._is_running and self._thread is not None and self._thread.is_alive()

    def start(self):
        """Start the background simulation thread safely, preventing duplicates."""
        with self._lock:
            if self.is_running():
                logger.warning("Simulation is already running. Duplicate start ignored.")
                return False

            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="FactoryTwin-SimulatorWorker",
                daemon=True
            )
            self._is_running = True
            self._thread.start()
            logger.info("Machine digital twin simulator thread started.")
            return True

    def stop(self):
        """Stop the background simulation worker gracefully."""
        with self._lock:
            if not self.is_running():
                return False

            self._stop_event.set()
            self._is_running = False
            logger.info("Signal sent to stop machine simulator.")
            return True

    def inject_fault(self, machine_id: str, condition: str, duration_cycles: int = 15) -> bool:
        """Inject an anomaly or failure condition into a specific machine."""
        if machine_id not in self.machines:
            return False
        self.machines[machine_id].set_condition(condition, duration_cycles)
        return True

    def get_status(self) -> dict:
        """Get high-level status of the simulation engine."""
        return {
            "running": self.is_running(),
            "interval_seconds": self.interval,
            "machine_count": len(self.machines),
            "source_modes": self.get_source_modes(),
            "machines": {
                m_id: {
                    "condition": m.condition,
                    "status": m.status,
                    "cycles_left": m.fault_cycles_remaining,
                    "source_mode": self.source_modes.get(m_id, "SYNTHETIC")
                }
                for m_id, m in self.machines.items()
            }
        }

    def _run_loop(self):
        """Main simulation execution loop executing in background daemon thread."""
        logger.info("Simulation loop active.")
        detector = get_anomaly_detector()

        while not self._stop_event.is_set():
            loop_start = time.time()

            for machine_id, machine in self.machines.items():
                if self._stop_event.is_set():
                    break

                # If this machine is set to ESP32 mode, skip synthetic generation
                if self.source_modes.get(machine_id) == "ESP32":
                    continue

                try:
                    # 1. Physical Simulation Step
                    telemetry_reading = machine.step()
                    message_id = f"SIM-{machine_id}-{int(time.time() * 1000)}"
                    telemetry_reading["message_id"] = message_id

                    # 2. AI Anomaly Inference
                    anomaly_res = detector.predict(
                        machine_id=machine_id,
                        temperature=telemetry_reading["temperature"],
                        vibration=telemetry_reading["vibration"],
                        speed=telemetry_reading["speed"],
                        load=telemetry_reading["load"]
                    )

                    # 3. Database Persistence
                    self._persist_reading(telemetry_reading, anomaly_res)

                    # 4. Alert & Health Monitoring Evaluation
                    evaluate_telemetry_for_alerts(telemetry_reading, anomaly_res)

                    # 5. Optional MQTT Publish
                    if self._mqtt_publisher and getattr(self._mqtt_publisher, "is_connected", False):
                        self._mqtt_publisher.publish_telemetry(machine_id, telemetry_reading)

                except Exception as e:
                    logger.error(f"Error in simulation cycle for {machine_id}: {e}", exc_info=True)

            # Sleep remaining time to maintain constant cycle frequency
            elapsed = time.time() - loop_start
            sleep_time = max(0.2, self.interval - elapsed)
            self._stop_event.wait(timeout=sleep_time)

        self._is_running = False
        logger.info("Simulation worker thread exited cleanly.")

    def _persist_reading(self, reading: dict, anomaly_res: dict):
        """Persist telemetry record and anomaly prediction into SQLite."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert Telemetry Record
            cursor.execute("""
                INSERT INTO telemetry (
                    message_id, machine_id, timestamp, temperature, vibration, speed, load, status, production_count, data_source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reading["message_id"],
                reading["machine_id"],
                reading["timestamp"],
                reading["temperature"],
                reading["vibration"],
                reading["speed"],
                reading["load"],
                reading["status"],
                reading["production_count"],
                reading["data_source"]
            ))
            telemetry_id = cursor.lastrowid

            # Insert Anomaly Prediction
            if anomaly_res:
                cursor.execute("""
                    INSERT INTO anomaly_predictions (
                        telemetry_id, machine_id, timestamp, anomaly_score, is_anomaly, risk_category, detection_method, suggested_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    telemetry_id,
                    reading["machine_id"],
                    reading["timestamp"],
                    anomaly_res["anomaly_score"],
                    1 if anomaly_res["is_anomaly"] else 0,
                    anomaly_res["risk_category"],
                    anomaly_res["detection_method"],
                    anomaly_res["suggested_action"]
                ))

            # Update Machine Current Status & Check Transition
            cursor.execute("SELECT current_status FROM machines WHERE machine_id = ?", (reading["machine_id"],))
            row = cursor.fetchone()
            old_status = row["current_status"] if row else "RUNNING"
            new_status = reading["status"]

            if old_status != new_status:
                cursor.execute("""
                    UPDATE machines SET current_status = ? WHERE machine_id = ?
                """, (new_status, reading["machine_id"]))
                cursor.execute("""
                    INSERT INTO machine_status_history (machine_id, old_status, new_status, reason)
                    VALUES (?, ?, ?, ?)
                """, (reading["machine_id"], old_status, new_status, f"State change to {new_status} under condition {reading.get('active_condition', 'NORMAL')}"))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to persist simulated telemetry: {e}")

# Global simulation singleton
_simulator = None

def get_simulator() -> SimulationEngine:
    global _simulator
    if _simulator is None:
        _simulator = SimulationEngine()
    return _simulator
