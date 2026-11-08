"""
Unit Tests for Machine Simulation Engine (P_307)
"""

import unittest
import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import Config
from simulation.simulator import MachineState, SimulationEngine, get_simulator

class TestSimulation(unittest.TestCase):
    """Test suite for machine physics simulator and background execution controls."""

    def test_machine_state_step_normal(self):
        """Verify normal simulation step produces plausible values within operating bounds."""
        cfg = Config.MACHINES["Motor"]
        state = MachineState("Motor", cfg)

        reading = state.step()
        self.assertEqual(reading["machine_id"], "Motor")
        self.assertEqual(reading["status"], "RUNNING")
        self.assertEqual(reading["data_source"], "SIMULATED")
        # Check values are within physical bounds
        self.assertGreater(reading["temperature"], 40.0)
        self.assertLess(reading["temperature"], 100.0)
        self.assertGreater(reading["vibration"], 0.5)
        self.assertLess(reading["vibration"], 4.0)
        self.assertGreater(reading["speed"], 1500.0)
        self.assertLess(reading["speed"], 2000.0)

    def test_fault_injection_high_temp(self):
        """Verify fault injection for HIGH_TEMP shifts temperature upward and updates status."""
        cfg = Config.MACHINES["Motor"]
        state = MachineState("Motor", cfg)
        state.set_condition("HIGH_TEMP", duration_cycles=5)

        for _ in range(3):
            reading = state.step()

        self.assertIn(reading["status"], ["WARNING", "CRITICAL"])
        self.assertGreater(reading["temperature"], cfg["base_temp"])

    def test_fault_injection_stoppage(self):
        """Verify STOPPAGE fault drives speed to 0 and stops production increment."""
        cfg = Config.MACHINES["Conveyor"]
        state = MachineState("Conveyor", cfg)
        state.set_condition("STOPPAGE", duration_cycles=3)

        reading = state.step()
        self.assertEqual(reading["status"], "STOPPED")
        self.assertEqual(reading["speed"], 0.0)

    def test_simulator_singleton_and_thread_lifecycle(self):
        """Verify simulator starts, stops, and rejects duplicate start attempts."""
        sim = get_simulator()
        # Ensure stopped first
        sim.stop()
        time.sleep(0.5)
        self.assertFalse(sim.is_running())

        # Start
        started = sim.start()
        self.assertTrue(started)
        self.assertTrue(sim.is_running())

        # Duplicate start should return False and not create new thread
        duplicate = sim.start()
        self.assertFalse(duplicate)

        # Stop
        stopped = sim.stop()
        self.assertTrue(stopped)
        time.sleep(0.5)
        self.assertFalse(sim.is_running())

if __name__ == "__main__":
    unittest.main()
