"""
Synthetic Dataset Generator for Industrial Machine Telemetry (P_307)
Generates:
1. Normal operating telemetry (Unsupervised Training Set - no labels, strictly normal behavior)
2. Evaluation telemetry (Test Set containing controlled synthetic anomalies with ground truth labels)

Strictly ensures NO DATA LEAKAGE: training set contains only normal behavior.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import Config

def generate_normal_record(machine_id, base_cfg, rng):
    """Generate a single sensor reading within normal operating statistical envelopes."""
    temp_noise = rng.normal(0, 1.8)
    vib_noise = rng.normal(0, 0.15)
    rpm_noise = rng.normal(0, 15.0)
    load_noise = rng.normal(0, 2.5)

    temp = max(20.0, base_cfg["base_temp"] + temp_noise)
    vib = max(0.1, base_cfg["base_vibration"] + vib_noise)
    rpm = max(100.0, base_cfg["base_rpm"] + rpm_noise)
    load = min(100.0, max(5.0, base_cfg["base_load"] + load_noise))

    return {
        "machine_id": machine_id,
        "temperature": round(float(temp), 2),
        "vibration": round(float(vib), 3),
        "speed": round(float(rpm), 1),
        "load": round(float(load), 1),
        "status": "RUNNING"
    }

def generate_anomaly_record(machine_id, base_cfg, rng, anomaly_type):
    """Generate a single sensor reading with an engineered industrial anomaly."""
    rec = generate_normal_record(machine_id, base_cfg, rng)

    if anomaly_type == "overheat":
        # Thermal runaway / cooling failure
        rec["temperature"] = round(float(base_cfg["max_temp"] + rng.uniform(5.0, 25.0)), 2)
        rec["status"] = "WARNING"
    elif anomaly_type == "bearing_fault":
        # Severe bearing race spalling / unbalance
        rec["vibration"] = round(float(base_cfg["max_vibration"] + rng.uniform(2.0, 8.0)), 3)
        rec["status"] = "WARNING"
    elif anomaly_type == "mechanical_jam":
        # Sudden torque overload and speed drop
        rec["load"] = round(float(min(100.0, base_cfg["max_load"] + rng.uniform(5.0, 15.0))), 1)
        rec["speed"] = round(float(max(50.0, base_cfg["base_rpm"] * rng.uniform(0.15, 0.45))), 1)
        rec["status"] = "CRITICAL"
    elif anomaly_type == "sensor_spike":
        # Electrical sensor failure / erratic transient glitch
        rec["temperature"] = round(float(rng.uniform(115.0, 150.0)), 2)
        rec["vibration"] = round(float(rng.uniform(12.0, 25.0)), 3)
        rec["status"] = "CRITICAL"
    elif anomaly_type == "compound_failure":
        # High vibration inducing thermal heating
        rec["temperature"] = round(float(base_cfg["max_temp"] + rng.uniform(8.0, 20.0)), 2)
        rec["vibration"] = round(float(base_cfg["max_vibration"] + rng.uniform(3.0, 7.0)), 3)
        rec["load"] = round(float(min(100.0, base_cfg["base_load"] + 20.0)), 1)
        rec["status"] = "CRITICAL"

    return rec

def generate_datasets(n_train_per_machine=3000, n_eval_per_machine=750, random_seed=42):
    """
    Generate independent training and evaluation datasets.
    
    Training Set: Strictly normal telemetry (12,000 samples).
    Evaluation Set: 85% normal, 15% synthetic anomalies with ground truth labels (3,000 samples).
    """
    Config.ensure_directories()
    rng = np.random.default_rng(random_seed)

    print("=" * 70)
    print("FactoryTwin (P_307) - Synthetic Industrial Telemetry Generation")
    print("=" * 70)

    # 1. Generate Normal Training Dataset (Unsupervised)
    train_records = []
    base_time = datetime.now() - timedelta(days=14)
    time_cursor = base_time

    for machine_id, cfg in Config.MACHINES.items():
        print(f"Generating {n_train_per_machine} normal records for {machine_id}...")
        for _ in range(n_train_per_machine):
            time_cursor += timedelta(seconds=int(rng.integers(2, 6)))
            rec = generate_normal_record(machine_id, cfg, rng)
            rec["timestamp"] = time_cursor.strftime("%Y-%m-%d %H:%M:%S")
            train_records.append(rec)

    df_train = pd.DataFrame(train_records)
    train_path = Config.DATA_DIR / "normal_training_data.csv"
    df_train.to_csv(train_path, index=False)
    print(f"[OK] Training dataset saved to: {train_path} ({len(df_train)} rows)")

    # 2. Generate Evaluation Dataset (Normal + Labeled Anomalies)
    eval_records = []
    anomaly_types = ["overheat", "bearing_fault", "mechanical_jam", "sensor_spike", "compound_failure"]
    eval_time = datetime.now() - timedelta(days=2)

    for machine_id, cfg in Config.MACHINES.items():
        print(f"Generating {n_eval_per_machine} evaluation records for {machine_id} (15% anomalies)...")
        n_anomalies = int(n_eval_per_machine * 0.15)
        n_normals = n_eval_per_machine - n_anomalies

        # Generate normal subset
        for _ in range(n_normals):
            eval_time += timedelta(seconds=int(rng.integers(2, 6)))
            rec = generate_normal_record(machine_id, cfg, rng)
            rec["timestamp"] = eval_time.strftime("%Y-%m-%d %H:%M:%S")
            rec["is_anomaly"] = 0
            rec["anomaly_reason"] = "Normal Operation"
            eval_records.append(rec)

        # Generate anomaly subset
        for _ in range(n_anomalies):
            eval_time += timedelta(seconds=int(rng.integers(2, 6)))
            atype = str(rng.choice(anomaly_types))
            rec = generate_anomaly_record(machine_id, cfg, rng, atype)
            rec["timestamp"] = eval_time.strftime("%Y-%m-%d %H:%M:%S")
            rec["is_anomaly"] = 1
            rec["anomaly_reason"] = atype
            eval_records.append(rec)

    df_eval = pd.DataFrame(eval_records)
    # Shuffle evaluation set
    df_eval = df_eval.sample(frac=1.0, random_state=random_seed).reset_index(drop=True)
    eval_path = Config.DATA_DIR / "anomaly_evaluation_data.csv"
    df_eval.to_csv(eval_path, index=False)

    total_eval = len(df_eval)
    actual_anomalies = int(df_eval["is_anomaly"].sum())
    print(f"[OK] Evaluation dataset saved to: {eval_path} ({total_eval} rows, {actual_anomalies} anomalies = {actual_anomalies/total_eval*100:.1f}%)")
    print("=" * 70)

if __name__ == "__main__":
    generate_datasets()
