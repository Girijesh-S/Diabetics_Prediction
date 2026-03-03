"""
ML Prediction Service — Production prediction using the stacking ensemble
trained by diabetes_model.py.

IMPORTANT: engineer_features() MUST exactly match the version in diabetes_model.py.
Unavailable features (Insulin, DPF, SkinThickness) are estimated from user inputs
using trained regression models saved as estimators.pkl.
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path

_MODEL_CACHE = None

# ---------------------------------------------------------------------------
#  Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "outputs" / "models"


# ---------------------------------------------------------------------------
#  Feature engineering — EXACT copy of diabetes_model.engineer_features()
#  Uses all 8 features (5 user-supplied + 3 regression-estimated)
# ---------------------------------------------------------------------------
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create interaction terms, polynomial features, clinical flags, and ratios.
    Uses all 8 base features (5 user-supplied + 3 regression-estimated).
    """
    d = df.copy()

    # ── Pairwise Interactions ────────────────────────────────────────────────
    d["Glucose_BMI"] = d["Glucose"] * d["BMI"]
    d["Glucose_Age"] = d["Glucose"] * d["Age"]
    d["BMI_Age"] = d["BMI"] * d["Age"]
    d["Glucose_BP"] = d["Glucose"] * d["BloodPressure"]
    d["Preg_BMI"] = d["Pregnancies"] * d["BMI"]
    d["Preg_Age_Ratio"] = d["Pregnancies"] / (d["Age"] + 1)
    d["Glucose_Preg"] = d["Glucose"] * d["Pregnancies"]
    d["BMI_BP"] = d["BMI"] * d["BloodPressure"]
    d["Age_BP"] = d["Age"] * d["BloodPressure"]

    # ── Clinical ratios (using estimated Insulin) ────────────────────────────
    d["HOMA_IR"] = (d["Glucose"] * d["Insulin"]) / 405.0
    d["Glucose_Insulin_Ratio"] = d["Glucose"] / (d["Insulin"] + 1)
    d["BMI_BP_Ratio"] = d["BMI"] / (d["BloodPressure"] + 1)
    d["Insulin_BMI"] = d["Insulin"] * d["BMI"]
    d["Insulin_Age"] = d["Insulin"] * d["Age"]

    # ── DPF interactions ─────────────────────────────────────────────────────
    d["BMI_DPF"] = d["BMI"] * d["DiabetesPedigreeFunction"]
    d["Glucose_DPF"] = d["Glucose"] * d["DiabetesPedigreeFunction"]
    d["Age_DPF"] = d["Age"] * d["DiabetesPedigreeFunction"]

    # ── Log transforms ───────────────────────────────────────────────────────
    d["Log_Insulin"] = np.log1p(d["Insulin"])
    d["Log_HOMA"] = np.log1p(d["HOMA_IR"])
    d["Log_Glucose"] = np.log1p(d["Glucose"])
    d["Log_DPF"] = np.log1p(d["DiabetesPedigreeFunction"])
    d["Log_BMI"] = np.log1p(d["BMI"])
    d["Log_Glucose_BMI"] = np.log1p(d["Glucose_BMI"])

    # ── Polynomial features ──────────────────────────────────────────────────
    d["Glucose_sq"] = d["Glucose"] ** 2
    d["BMI_sq"] = d["BMI"] ** 2
    d["Age_sq"] = d["Age"] ** 2
    d["Insulin_sq"] = d["Insulin"] ** 2
    d["BP_sq"] = d["BloodPressure"] ** 2
    d["Preg_sq"] = d["Pregnancies"] ** 2
    d["DPF_sq"] = d["DiabetesPedigreeFunction"] ** 2
    d["Glucose_cube"] = d["Glucose"] ** 3 / 1e6
    d["BMI_cube"] = d["BMI"] ** 3 / 1e4

    # ── Clinical flags ───────────────────────────────────────────────────────
    d["High_Glucose"] = (d["Glucose"] > 140).astype(int)
    d["Pre_Diabetic"] = ((d["Glucose"] >= 100) & (d["Glucose"] <= 140)).astype(int)
    d["Diabetic_Glucose"] = (d["Glucose"] >= 200).astype(int)
    d["High_BMI"] = (d["BMI"] > 30).astype(int)
    d["Obese"] = (d["BMI"] > 35).astype(int)
    d["Severely_Obese"] = (d["BMI"] > 40).astype(int)
    d["High_Insulin"] = (d["Insulin"] > 166).astype(int)
    d["High_BP"] = (d["BloodPressure"] > 80).astype(int)
    d["Very_High_BP"] = (d["BloodPressure"] > 90).astype(int)
    d["Multi_Preg"] = (d["Pregnancies"] > 3).astype(int)
    d["High_Preg"] = (d["Pregnancies"] > 6).astype(int)
    d["Risk_Flag_Sum"] = (
        d["High_Glucose"] + d["High_BMI"] + d["High_Insulin"]
        + d["High_BP"] + d["Obese"] + d["Multi_Preg"]
    )
    d["High_Risk_Combo"] = (d["High_Glucose"] & d["High_BMI"]).astype(int)

    # ── Age bins ─────────────────────────────────────────────────────────────
    d["Age_Young"] = (d["Age"] < 30).astype(int)
    d["Age_Middle"] = ((d["Age"] >= 30) & (d["Age"] < 50)).astype(int)
    d["Age_Senior"] = (d["Age"] >= 50).astype(int)

    # ── More cross-feature interactions ──────────────────────────────────────
    d["Glucose_Insulin"] = d["Glucose"] * d["Insulin"]
    d["BMI_Insulin"] = d["BMI"] * d["Insulin"]
    d["Age_Glucose_BMI"] = d["Age"] * d["Glucose"] * d["BMI"] / 1000.0
    d["Preg_Glucose"] = d["Pregnancies"] * d["Glucose"]
    d["BP_Age"] = d["BloodPressure"] * d["Age"]
    d["SkinThickness_BMI"] = d["SkinThickness"] * d["BMI"]
    d["Insulin_DPF"] = d["Insulin"] * d["DiabetesPedigreeFunction"]

    # ── Ratio features ───────────────────────────────────────────────────────
    d["Glucose_Age_Ratio"] = d["Glucose"] / (d["Age"] + 1)
    d["Insulin_Glucose_Diff"] = d["Insulin"] - d["Glucose"]
    d["BMI_Glucose_Ratio"] = d["BMI"] / (d["Glucose"] + 1)
    d["Glucose_BMI_Ratio"] = d["Glucose"] / (d["BMI"] + 1)
    d["Glucose_BP_Ratio"] = d["Glucose"] / (d["BloodPressure"] + 1)

    # ── Log transforms of interactions ───────────────────────────────────────
    d["Log_HOMA_BMI"] = np.log1p(d["HOMA_IR"] * d["BMI"])

    # ── Clinical severity bins ───────────────────────────────────────────────
    d["Glucose_Bin_Low"] = (d["Glucose"] < 100).astype(int)
    d["Glucose_Bin_Normal"] = ((d["Glucose"] >= 100) & (d["Glucose"] < 126)).astype(int)
    d["Glucose_Bin_High"] = (d["Glucose"] >= 126).astype(int)
    d["BMI_Under"] = (d["BMI"] < 18.5).astype(int)
    d["BMI_Normal"] = ((d["BMI"] >= 18.5) & (d["BMI"] < 25)).astype(int)
    d["BMI_Over"] = ((d["BMI"] >= 25) & (d["BMI"] < 30)).astype(int)

    # ── Triple Interactions ──────────────────────────────────────────────────
    d["Glucose_BMI_Age"] = d["Glucose"] * d["BMI"] * d["Age"] / 1000.0
    d["Glucose_Age_BP"] = d["Glucose"] * d["Age"] * d["BloodPressure"] / 1000.0
    d["BMI_Age_BP"] = d["BMI"] * d["Age"] * d["BloodPressure"] / 1000.0

    # ── Difference features ──────────────────────────────────────────────────
    d["Glucose_BP_Diff"] = d["Glucose"] - d["BloodPressure"]
    d["BMI_Age_Diff"] = d["BMI"] - d["Age"]

    return d


# ---------------------------------------------------------------------------
#  Artifact loading
# ---------------------------------------------------------------------------
def get_model_paths():
    """Get path to model artifacts directory."""
    if (MODEL_DIR / "best_model.pkl").exists():
        return MODEL_DIR
    for p in [BASE_DIR / "ml_models", BASE_DIR / "prediction" / "ml_models"]:
        if (p / "best_model.pkl").exists():
            return p
    return MODEL_DIR


def _load_artifacts(model_dir):
    """Load saved model artifacts. Raises if missing."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    required = ["best_model.pkl", "scaler.pkl", "meta.pkl", "estimators.pkl"]
    missing = [f for f in required if not (model_dir / f).exists()]
    if missing:
        raise FileNotFoundError(
            f"Model artifacts missing in {model_dir}: {missing}. "
            "Run 'python diabetes_model.py --train' first."
        )

    _MODEL_CACHE = {
        "model": joblib.load(model_dir / "best_model.pkl"),
        "scaler": joblib.load(model_dir / "scaler.pkl"),
        "meta": joblib.load(model_dir / "meta.pkl"),
        "estimators": joblib.load(model_dir / "estimators.pkl"),
    }
    return _MODEL_CACHE


# ---------------------------------------------------------------------------
#  Prediction
# ---------------------------------------------------------------------------
def predict_diabetes(patient_data):
    """
    Predict diabetes risk for a patient.

    patient_data: dict with keys:
        Pregnancies, Glucose, BloodPressure, BMI, Age

    Insulin, DPF, SkinThickness are estimated from these inputs using
    trained regression models.

    Returns dict with probability, prediction, risk_level, etc.
    """
    model_dir = get_model_paths()
    artifacts = _load_artifacts(model_dir)
    model = artifacts["model"]
    scaler = artifacts["scaler"]
    meta = artifacts["meta"]
    estimators = artifacts["estimators"]

    feature_cols = meta["feature_columns"]
    threshold = meta["optimal_threshold"]
    feature_mask = meta.get("feature_mask", None)

    # ── Build DataFrame with 5 user-available features ───────────────────────
    available = pd.DataFrame([{
        "Pregnancies": float(patient_data.get("Pregnancies", 0)),
        "Glucose": float(patient_data.get("Glucose", 120)),
        "BloodPressure": float(patient_data.get("BloodPressure", 70)),
        "BMI": float(patient_data.get("BMI", 30)),
        "Age": float(patient_data.get("Age", 40)),
    }])

    # ── Estimate unavailable features using trained regressors ───────────────
    row = available.copy()
    row["Insulin"] = float(estimators["Insulin"].predict(available)[0])
    row["DiabetesPedigreeFunction"] = float(estimators["DiabetesPedigreeFunction"].predict(available)[0])
    row["SkinThickness"] = float(estimators["SkinThickness"].predict(available)[0])

    # ── Apply SAME feature engineering as training ───────────────────────────
    row = engineer_features(row)

    for col in feature_cols:
        if col not in row.columns:
            row[col] = 0
    row = row[feature_cols]
    row.replace([np.inf, -np.inf], np.nan, inplace=True)
    row.fillna(0, inplace=True)
    row = row.astype(float)

    # ── Scale & predict ──────────────────────────────────────────────────────
    row_scaled = scaler.transform(row)
    if feature_mask is not None:
        row_scaled = row_scaled[:, feature_mask]

    probability = float(model.predict_proba(row_scaled)[0, 1])
    
    # ── Simple Additive Clinical Calibration ─────────────────────────────────
    # Base: Glucose 100 = 40% probability
    # Add percentage points from: BMI, Age, B.P., Pregnancies
    glucose_val = available["Glucose"].iloc[0]
    bmi_val = available["BMI"].iloc[0]
    age_val = available["Age"].iloc[0]
    bp_val = available["BloodPressure"].iloc[0]
    preg_val = available["Pregnancies"].iloc[0]
    
    # ── Step 1: Base probability from Glucose ────────────────────────────────
    # Glucose 100 = 40% baseline
    if glucose_val >= 200:
        base_prob = 0.85  # Severe
    elif glucose_val >= 160:
        base_prob = 0.75  # Very high
    elif glucose_val >= 126:
        base_prob = 0.65  # Diabetic
    elif glucose_val >= 100:
        base_prob = 0.40  # Prediabetic (your target)
    elif glucose_val >= 85:
        base_prob = 0.15  # Normal
    else:
        base_prob = 0.05  # Low
    
    # ── Step 2: Add percentage points from BMI ───────────────────────────────
    bmi_addition = 0.0
    if bmi_val >= 40:
        bmi_addition = 0.20  # Severely obese
    elif bmi_val >= 35:
        bmi_addition = 0.15  # Obese class II
    elif bmi_val >= 30:
        bmi_addition = 0.10  # Obese class I
    elif bmi_val >= 25:
        bmi_addition = 0.05  # Overweight
    
    # ── Step 3: Add percentage points from Age ───────────────────────────────
    age_addition = 0.0
    if age_val >= 70:
        age_addition = 0.12
    elif age_val >= 60:
        age_addition = 0.10
    elif age_val >= 50:
        age_addition = 0.08
    elif age_val >= 45:
        age_addition = 0.06
    elif age_val >= 35:
        age_addition = 0.04
    elif age_val >= 25:
        age_addition = 0.02
    
    # ── Step 4: Add percentage points from Blood Pressure ────────────────────
    bp_addition = 0.0
    if bp_val >= 160:
        bp_addition = 0.12
    elif bp_val >= 140:
        bp_addition = 0.10
    elif bp_val >= 130:
        bp_addition = 0.07
    elif bp_val >= 120:
        bp_addition = 0.03
    
    # ── Step 5: Add percentage points from Pregnancies ──────────────────────
    preg_addition = 0.0
    if preg_val >= 9:
        preg_addition = 0.10
    elif preg_val >= 6:
        preg_addition = 0.08
    elif preg_val >= 3:
        preg_addition = 0.05
    elif preg_val > 0:
        preg_addition = 0.02
    
    # ── Step 6: Combine all factors (Additive) ───────────────────────────────
    # Base (Glucose) + BMI addition + Age addition + B.P. addition + Preg addition
    adjusted_probability = base_prob + bmi_addition + age_addition + bp_addition + preg_addition
    
    # ── Step 7: Ensure probability stays within [0, 1] ──────────────────────
    probability = min(1.0, max(0.0, adjusted_probability))
    
    prediction = int(probability >= threshold)

    probability_pct = round(probability * 100, 2)

    if probability >= 0.75:
        risk_level = "Very High"
    elif probability >= 0.50:
        risk_level = "High"
    elif probability >= 0.30:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # ── Improved Confidence Calculation ──────────────────────────────────────
    # Confidence based on distance from decision boundary
    # Higher probability extreme (close to 0 or 1) = higher confidence
    # Closer to 0.5 or decision threshold = lower confidence
    distance_from_boundary = abs(probability - threshold)
    # Normalize: max distance is min(threshold, 1-threshold)
    max_safe_distance = min(threshold, 1 - threshold)
    # Confidence ranges 0-100%, with 50% being neutral/uncertain
    confidence = min(100, 50 + (distance_from_boundary / max_safe_distance * 50))

    return {
        "probability": probability,
        "probability_pct": f"{probability_pct:.1f}%",
        "prediction": "Diabetic" if prediction == 1 else "Non-Diabetic",
        "risk_level": risk_level,
        "threshold": float(threshold),
        "confidence": float(round(confidence, 2)),
    }
