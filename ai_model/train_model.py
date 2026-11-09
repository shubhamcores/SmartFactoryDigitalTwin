"""
Isolation Forest Model Training and Evaluation 
Trains an unsupervised Isolation Forest on normal industrial telemetry.
Evaluates detection performance on a separate labeled synthetic evaluation set.
Saves model, scaler, and formal metrics report.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, confusion_matrix,
    classification_report
)
from config import Config
from ai_model.generate_dataset import generate_datasets

FEATURE_COLUMNS = ["temperature", "vibration", "speed", "load"]

def train_and_evaluate(force_regenerate_data=False):
    """
    Train Isolation Forest strictly on normal operating data, evaluate on labeled test set.
    """
    Config.ensure_directories()
    train_file = Config.DATA_DIR / "normal_training_data.csv"
    eval_file = Config.DATA_DIR / "anomaly_evaluation_data.csv"

    if force_regenerate_data or not train_file.exists() or not eval_file.exists():
        print("[INFO] Telemetry datasets not found. Generating fresh synthetic datasets...")
        generate_datasets()

    print("=" * 75)
    print("FactoryTwin  - Isolation Forest Training & Rigorous Evaluation")
    print("=" * 75)

    # 1. Load Data
    df_train = pd.read_csv(train_file)
    df_eval = pd.read_csv(eval_file)

    print(f"Loaded Training Data:   {len(df_train):,} rows (Strictly normal operation)")
    print(f"Loaded Evaluation Data: {len(df_eval):,} rows (Ground truth labeled anomalies)")

    # 2. Extract Features
    X_train = df_train[FEATURE_COLUMNS].values
    X_eval = df_eval[FEATURE_COLUMNS].values
    y_eval_true = df_eval["is_anomaly"].values  # 0 = Normal, 1 = Anomaly

    # 3. Fit Scaler (Fit only on training data to prevent data leakage)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_eval_scaled = scaler.transform(X_eval)

    # 4. Train Isolation Forest
    print(f"\n[1/3] Training Isolation Forest (n_estimators=150, contamination={Config.ANOMALY_CONTAMINATION})...")
    model = IsolationForest(
        n_estimators=150,
        contamination=Config.ANOMALY_CONTAMINATION,
        max_samples="auto",
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled)
    print("      -> Model convergence achieved.")

    # 5. Evaluate on Evaluation Dataset
    print("\n[2/3] Evaluating unsupervised detector against test set with ground truth anomalies...")
    # In scikit-learn IsolationForest:
    # predict() returns 1 for inlier (normal), -1 for outlier (anomaly).
    raw_preds = model.predict(X_eval_scaled)
    y_eval_pred = np.where(raw_preds == -1, 1, 0)

    # Decision function returns negative scores for outliers, positive for inliers
    decision_scores = model.decision_function(X_eval_scaled)

    # Metrics Computation
    cm = confusion_matrix(y_eval_true, y_eval_pred)
    tn, fp, fn, tp = cm.ravel()

    precision = float(precision_score(y_eval_true, y_eval_pred, zero_division=0))
    recall = float(recall_score(y_eval_true, y_eval_pred, zero_division=0))
    f1 = float(f1_score(y_eval_true, y_eval_pred, zero_division=0))
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    print("\n" + "-" * 50)
    print("EVALUATION METRICS SUMMARY")
    print("-" * 50)
    print(f"  Precision:           {precision:.4f}  (True Anomaly / Predicted Anomaly)")
    print(f"  Recall (Sensitivity):{recall:.4f}  (Detected Anomalies / Actual Anomalies)")
    print(f"  F1-Score:            {f1:.4f}  (Harmonic Mean of Precision and Recall)")
    print(f"  False Positive Rate: {fpr:.4f}  (Normal samples misclassified as anomaly)")
    print(f"  Confusion Matrix:")
    print(f"     True Negatives  (Normal detected as Normal):   {tn:,}")
    print(f"     False Positives (Normal flagged as Anomaly):   {fp:,}")
    print(f"     False Negatives (Anomaly missed by Detector):  {fn:,}")
    print(f"     True Positives  (Anomaly successfully Caught): {tp:,}")
    print("-" * 50)

    # 6. Save Artifacts
    print("\n[3/3] Saving fitted model, standardizer, and evaluation metrics...")
    joblib.dump(model, Config.MODEL_PATH)
    joblib.dump(scaler, Config.SCALER_PATH)

    metrics_report = {
        "model_type": "IsolationForest",
        "features": FEATURE_COLUMNS,
        "n_estimators": 150,
        "contamination": Config.ANOMALY_CONTAMINATION,
        "training_samples": int(len(df_train)),
        "evaluation_samples": int(len(df_eval)),
        "metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "limitations_and_disclaimer": (
            "1. Synthetic Anomaly Bias: Evaluation anomalies were generated algorithmically "
            "based on known physics regimes (e.g., thermal spikes, bearing noise). Real factory "
            "faults exhibit non-linear micro-wear patterns that may yield different performance.\n"
            "2. Score Meaning: Isolation Forest decision scores indicate mathematical isolation depth "
            "(rareness of observation), NOT a calibrated probability of machine breakdown. A high score "
            "signifies an unusual state warranting inspection, not immediate failure.\n"
            "3. Environmental Shifts: Ambient temperature changes (summer vs. winter) or raw material "
            "density shifts may shift normal distributions and necessitate periodic retraining."
        )
    }

    with open(Config.METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_report, f, indent=4)

    print(f"[OK] Model saved to:   {Config.MODEL_PATH}")
    print(f"[OK] Scaler saved to:  {Config.SCALER_PATH}")
    print(f"[OK] Metrics saved to: {Config.METRICS_PATH}")
    print("=" * 75)
    return metrics_report

if __name__ == "__main__":
    train_and_evaluate(force_regenerate_data=True)
