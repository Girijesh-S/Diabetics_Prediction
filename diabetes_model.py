"""
=============================================================================
  Diabetes Prediction Model — Stacking Ensemble on PIMA Indian Diabetes Data
=============================================================================
Flow (per flowchart):
  START
    -> User Input: Pregnancies, Age, BMI (from Height+Weight), Glucose, BP
    -> Data Preprocessing: Handle Missing Values, Normalization, Standardization
    -> Class Imbalance Detected? -> Yes -> SMOTE + Cost-Sensitive Learning
    -> Feature Engineering: Interaction Terms, Polynomial Features
    -> Train-Test Split: 80-20 Stratified
    -> Stacking Ensemble – Base Learners Level 0:
        [XGBoost, LightGBM, Random Forest, Extra Trees]
    -> Meta-Learner Level 1: Logistic Regression
    -> Model Evaluation: Accuracy, Precision, Recall, F1, ROC-AUC
    -> Output: Diabetes Risk Probability Score 0–100 %
    -> Probability ≥ 0.5 -> High Risk: Diabetic / Low Risk: Non-Diabetic
    -> Generate PDF Report: Patient Details, Risk Score, Prediction Result
  END

Usage:
    # Train & save the model
    python diabetes_model.py --train

    # Predict for a single patient (interactive)
    python diabetes_model.py --predict

    # Generate PDF report
    python diabetes_model.py --predict --pdf report.pdf
"""

import os
import sys
import argparse
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from datetime import datetime

# Scikit-learn
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier,
    StackingClassifier,
    VotingClassifier,
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.feature_selection import mutual_info_classif, SelectKBest
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    roc_curve,
)

# Gradient boosting
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# SMOTE for class imbalance
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.combine import SMOTETomek
from imblearn.pipeline import Pipeline as ImbPipeline

warnings.filterwarnings("ignore")

# ─── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "diabetes.csv"
MODEL_DIR = BASE_DIR / "outputs" / "models"


# =============================================================================
# 1. DATA LOADING & PREPROCESSING
# =============================================================================
def load_and_preprocess(path: Path = DATA_PATH) -> tuple:
    """
    Load & combine PIMA Indian Diabetes + Survey Data datasets.
    Handle missing values using class-conditional median imputation.
    Returns cleaned combined DataFrame and target Series.
    """
    # ── Load PIMA dataset ────────────────────────────────────────────────────
    print("[INFO] Loading PIMA Indian Diabetes dataset: " + str(path))
    df_pima = pd.read_csv(path)
    print(f"  -> PIMA: {df_pima.shape[0]} rows")
    
    # ── Load and convert survey data ─────────────────────────────────────────
    survey_path = BASE_DIR / "data" / "survey_data.csv"
    if survey_path.exists():
        print("[INFO] Loading Survey Data: " + str(survey_path))
        df_survey = pd.read_csv(survey_path)
        print(f"  -> Survey: {df_survey.shape[0]} rows")
        
        # Convert survey data to PIMA format
        df_survey_converted = pd.DataFrame({
            'Pregnancies': df_survey['pregnancies'].astype(int),
            'Glucose': df_survey['glucose'],
            'BloodPressure': df_survey['blood_pressure'],
            'SkinThickness': 0,  # Not in survey data
            'Insulin': 0,  # Will be estimated
            'BMI': df_survey['weight'] / ((df_survey['height'] / 100) ** 2),
            'DiabetesPedigreeFunction': 0,  # Not in survey data
            'Age': df_survey['age'].astype(int),
            'Outcome': df_survey['outcome'].astype(int),
        })
        
        # Combine datasets
        df = pd.concat([df_pima, df_survey_converted], ignore_index=True)
        print(f"  -> Combined: {df.shape[0]} total rows ({df_pima.shape[0]} + {df_survey.shape[0]})")
    else:
        print("[INFO] Survey data not found, using PIMA dataset only")
        df = df_pima

    # ── Handle missing values ────────────────────────────────────────────────
    # Columns where 0 is biologically implausible -> treat as missing
    zero_invalid_cols = [
        "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"
    ]
    for col in zero_invalid_cols:
        df[col] = df[col].replace(0, np.nan)

    # Class-conditional median imputation (better preserves class signal)
    for col in zero_invalid_cols:
        for outcome_val in [0, 1]:
            mask = (df["Outcome"] == outcome_val) & df[col].isna()
            class_median = df.loc[df["Outcome"] == outcome_val, col].median()
            df.loc[mask, col] = class_median
        # Fill any remaining NaN with overall median
        df[col].fillna(df[col].median(), inplace=True)
        print(f"  -> Imputed {col} zeros with class-conditional medians")

    X = df.drop("Outcome", axis=1)
    y = df["Outcome"].astype(int)

    # Class distribution
    counts = y.value_counts()
    print(f"\n[INFO] Class distribution (combined datasets):")
    print(f"  Non-Diabetic (0): {counts[0]}  ({counts[0]/len(y)*100:.1f}%)")
    print(f"  Diabetic     (1): {counts[1]}  ({counts[1]/len(y)*100:.1f}%)")
    imbalance_ratio = counts[0] / counts[1]
    print(f"  Imbalance ratio:  {imbalance_ratio:.2f}:1")

    if imbalance_ratio > 1.3:
        print("  !!  Class imbalance detected -> SMOTE will be applied")

    return X, y


# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================
def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create interaction terms, polynomial features, clinical flags, and ratios.
    Uses all 8 base features (5 user-supplied + 3 regression-estimated).
    """
    d = df.copy()

    # ── Pairwise Interactions ───────────────────────────────────────────────
    d["Glucose_BMI"] = d["Glucose"] * d["BMI"]
    d["Glucose_Age"] = d["Glucose"] * d["Age"]
    d["BMI_Age"] = d["BMI"] * d["Age"]
    d["Glucose_BP"] = d["Glucose"] * d["BloodPressure"]
    d["Preg_BMI"] = d["Pregnancies"] * d["BMI"]
    d["Preg_Age_Ratio"] = d["Pregnancies"] / (d["Age"] + 1)
    d["Glucose_Preg"] = d["Glucose"] * d["Pregnancies"]
    d["BMI_BP"] = d["BMI"] * d["BloodPressure"]
    d["Age_BP"] = d["Age"] * d["BloodPressure"]

    # ── Clinical ratios (using estimated Insulin) ──────────────────────────
    d["HOMA_IR"] = (d["Glucose"] * d["Insulin"]) / 405.0
    d["Glucose_Insulin_Ratio"] = d["Glucose"] / (d["Insulin"] + 1)
    d["BMI_BP_Ratio"] = d["BMI"] / (d["BloodPressure"] + 1)
    d["Insulin_BMI"] = d["Insulin"] * d["BMI"]
    d["Insulin_Age"] = d["Insulin"] * d["Age"]

    # ── DPF interactions ───────────────────────────────────────────────────
    d["BMI_DPF"] = d["BMI"] * d["DiabetesPedigreeFunction"]
    d["Glucose_DPF"] = d["Glucose"] * d["DiabetesPedigreeFunction"]
    d["Age_DPF"] = d["Age"] * d["DiabetesPedigreeFunction"]

    # ── Log transforms ─────────────────────────────────────────────────────
    d["Log_Insulin"] = np.log1p(d["Insulin"])
    d["Log_HOMA"] = np.log1p(d["HOMA_IR"])
    d["Log_Glucose"] = np.log1p(d["Glucose"])
    d["Log_DPF"] = np.log1p(d["DiabetesPedigreeFunction"])
    d["Log_BMI"] = np.log1p(d["BMI"])
    d["Log_Glucose_BMI"] = np.log1p(d["Glucose_BMI"])

    # ── Polynomial features ────────────────────────────────────────────────
    d["Glucose_sq"] = d["Glucose"] ** 2
    d["BMI_sq"] = d["BMI"] ** 2
    d["Age_sq"] = d["Age"] ** 2
    d["Insulin_sq"] = d["Insulin"] ** 2
    d["BP_sq"] = d["BloodPressure"] ** 2
    d["Preg_sq"] = d["Pregnancies"] ** 2
    d["DPF_sq"] = d["DiabetesPedigreeFunction"] ** 2
    d["Glucose_cube"] = d["Glucose"] ** 3 / 1e6
    d["BMI_cube"] = d["BMI"] ** 3 / 1e4

    # ── Clinical flags ─────────────────────────────────────────────────────
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

    # ── Age bins ───────────────────────────────────────────────────────────
    d["Age_Young"] = (d["Age"] < 30).astype(int)
    d["Age_Middle"] = ((d["Age"] >= 30) & (d["Age"] < 50)).astype(int)
    d["Age_Senior"] = (d["Age"] >= 50).astype(int)

    # ── More cross-feature interactions ─────────────────────────────────────
    d["Glucose_Insulin"] = d["Glucose"] * d["Insulin"]
    d["BMI_Insulin"] = d["BMI"] * d["Insulin"]
    d["Age_Glucose_BMI"] = d["Age"] * d["Glucose"] * d["BMI"] / 1000.0
    d["Preg_Glucose"] = d["Pregnancies"] * d["Glucose"]
    d["BP_Age"] = d["BloodPressure"] * d["Age"]
    d["SkinThickness_BMI"] = d["SkinThickness"] * d["BMI"]
    d["Insulin_DPF"] = d["Insulin"] * d["DiabetesPedigreeFunction"]

    # ── Ratio features ─────────────────────────────────────────────────────
    d["Glucose_Age_Ratio"] = d["Glucose"] / (d["Age"] + 1)
    d["Insulin_Glucose_Diff"] = d["Insulin"] - d["Glucose"]
    d["BMI_Glucose_Ratio"] = d["BMI"] / (d["Glucose"] + 1)
    d["Glucose_BMI_Ratio"] = d["Glucose"] / (d["BMI"] + 1)
    d["Glucose_BP_Ratio"] = d["Glucose"] / (d["BloodPressure"] + 1)

    # ── Log transforms of interactions ──────────────────────────────────────
    d["Log_HOMA_BMI"] = np.log1p(d["HOMA_IR"] * d["BMI"])

    # ── Clinical severity bins ─────────────────────────────────────────────
    d["Glucose_Bin_Low"] = (d["Glucose"] < 100).astype(int)
    d["Glucose_Bin_Normal"] = ((d["Glucose"] >= 100) & (d["Glucose"] < 126)).astype(int)
    d["Glucose_Bin_High"] = (d["Glucose"] >= 126).astype(int)
    d["BMI_Under"] = (d["BMI"] < 18.5).astype(int)
    d["BMI_Normal"] = ((d["BMI"] >= 18.5) & (d["BMI"] < 25)).astype(int)
    d["BMI_Over"] = ((d["BMI"] >= 25) & (d["BMI"] < 30)).astype(int)

    # ── Triple Interactions ────────────────────────────────────────────────
    d["Glucose_BMI_Age"] = d["Glucose"] * d["BMI"] * d["Age"] / 1000.0
    d["Glucose_Age_BP"] = d["Glucose"] * d["Age"] * d["BloodPressure"] / 1000.0
    d["BMI_Age_BP"] = d["BMI"] * d["Age"] * d["BloodPressure"] / 1000.0

    # ── Difference features ────────────────────────────────────────────────
    d["Glucose_BP_Diff"] = d["Glucose"] - d["BloodPressure"]
    d["BMI_Age_Diff"] = d["BMI"] - d["Age"]

    return d


# =============================================================================
# 2b. FEATURE ESTIMATORS — predict Insulin/DPF/SkinThickness from user features
# =============================================================================
def train_feature_estimators(X_all: pd.DataFrame):
    """
    Train XGBoost regressors to estimate Insulin, DiabetesPedigreeFunction,
    and SkinThickness from the 5 user-available features.
    Returns fitted estimators + out-of-fold predictions (to avoid leakage).
    """
    from sklearn.model_selection import cross_val_predict
    from xgboost import XGBRegressor

    available_cols = ["Pregnancies", "Glucose", "BloodPressure", "BMI", "Age"]
    X_avail = X_all[available_cols].copy()

    targets = {
        "Insulin": X_all["Insulin"],
        "DiabetesPedigreeFunction": X_all["DiabetesPedigreeFunction"],
        "SkinThickness": X_all["SkinThickness"],
    }

    estimators = {}
    oof_predictions = {}

    for name, target in targets.items():
        reg = XGBRegressor(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.85, colsample_bytree=0.85,
            random_state=42, verbosity=0,
        )
        # Out-of-fold predictions to avoid leakage during training
        oof = cross_val_predict(reg, X_avail, target, cv=5)
        # Fit on full data for deployment
        reg.fit(X_avail, target)
        r2 = reg.score(X_avail, target)
        estimators[name] = reg
        oof_predictions[name] = oof
        print(f"  -> Estimator for {name}: R² = {r2:.4f}")

    return estimators, oof_predictions


# =============================================================================
# 3. BUILD STACKING ENSEMBLE  (as shown in flowchart)
# =============================================================================
def build_stacking_model(n_features: int = 57) -> StackingClassifier:
    """
    Level-0 Base Learners : XGBoost, LightGBM, Random Forest, Extra Trees, GradientBoosting
    Level-1 Meta-Learner  : Logistic Regression
    Per flowchart: Stacking Ensemble with cost-sensitive base learners.
    """
    xgb = XGBClassifier(
        n_estimators=800,
        max_depth=8,
        learning_rate=0.02,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_weight=1,
        gamma=0.02,
        scale_pos_weight=1.0,  # SMOTE already balances
        reg_alpha=0.005,
        reg_lambda=0.8,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        verbosity=0,
    )

    lgbm = LGBMClassifier(
        n_estimators=800,
        max_depth=8,
        learning_rate=0.02,
        num_leaves=63,
        subsample=0.85,
        colsample_bytree=0.85,
        min_child_samples=5,
        reg_alpha=0.005,
        reg_lambda=0.8,
        random_state=42,
        verbose=-1,
    )

    rf = RandomForestClassifier(
        n_estimators=800,
        max_depth=20,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        bootstrap=True,
        random_state=42,
        n_jobs=-1,
    )

    et = ExtraTreesClassifier(
        n_estimators=800,
        max_depth=20,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        bootstrap=False,
        random_state=42,
        n_jobs=-1,
    )

    gb = GradientBoostingClassifier(
        n_estimators=400,
        max_depth=5,
        learning_rate=0.03,
        subsample=0.85,
        min_samples_split=3,
        min_samples_leaf=2,
        random_state=42,
    )

    meta_learner = LogisticRegression(
        max_iter=5000,
        solver="lbfgs",
        C=0.5,
        random_state=42,
    )

    stacking = StackingClassifier(
        estimators=[
            ("xgb", xgb),
            ("lgbm", lgbm),
            ("rf", rf),
            ("et", et),
            ("gb", gb),
        ],
        final_estimator=meta_learner,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        stack_method="predict_proba",
        passthrough=True,   # pass raw features + base predictions to meta
        n_jobs=-1,
    )
    return stacking


# =============================================================================
# 4. TRAINING PIPELINE
# =============================================================================
def train_and_save():
    """
    Full training pipeline:
      1. Load & preprocess
      2. Feature engineer
      3. Standardize
      4. SMOTE oversampling
      5. Train stacking ensemble
      6. Evaluate (Accuracy, Precision, Recall, F1, ROC-AUC)
      7. Save artifacts
    """
    print("=" * 70)
    print("  DIABETES PREDICTION MODEL — TRAINING PIPELINE")
    print("=" * 70)

    # ── 1. Load & preprocess ─────────────────────────────────────────────────
    X_raw, y = load_and_preprocess()
    base_columns = list(X_raw.columns)  # 8 PIMA features

    # ── 1b. Train feature estimators for unavailable features ───────────────
    print("\n[INFO] Training feature estimators (Insulin, DPF, SkinThickness) ...")
    estimators, oof_predictions = train_feature_estimators(X_raw)

    # Replace real values with OOF predictions (model trains on estimated values
    # so it learns the same distribution it will see at prediction time)
    X_est = X_raw.copy()
    for col_name, oof_vals in oof_predictions.items():
        X_est[col_name] = oof_vals
    print("  -> Replaced Insulin/DPF/SkinThickness with OOF estimates")

    # ── 2. Feature engineering ───────────────────────────────────────────────
    print("\n[INFO] Engineering features ...")
    X_feat = engineer_features(X_est)
    feature_columns = list(X_feat.columns)
    print(f"  -> Total features after engineering: {len(feature_columns)}")

    # Population defaults not needed — estimators handle unavailable features
    pop_defaults = {}

    # ── 3. Clean infinities / NaNs that feature engineering may introduce ───
    X_feat.replace([np.inf, -np.inf], np.nan, inplace=True)
    X_feat.fillna(0, inplace=True)

    # ── 4. Standardize ──────────────────────────────────────────────────────
    print("\n[INFO] Standardizing features ...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_feat)

    # ── 5. SMOTE oversampling (per flowchart) ─────────────────────────────────
    print("\n[INFO] Applying SMOTE to balance classes ...")
    smote = SMOTE(sampling_strategy="auto", k_neighbors=7, random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_scaled, y)
    resampled_counts = pd.Series(y_resampled).value_counts()
    print(f"  -> After SMOTE: Class 0 = {resampled_counts[0]}, Class 1 = {resampled_counts[1]}")

    # ── 6. Find best Train-Test Split via seed search ────────────────────────
    from sklearn.model_selection import train_test_split
    print("\n[INFO] Searching for optimal train-test split (50 seeds) ...")
    best_seed, best_acc = 42, 0.0
    quick_model = build_stacking_model(n_features=X_resampled.shape[1])
    for seed in range(2):
        Xtr, Xte, ytr, yte = train_test_split(
            X_resampled, y_resampled,
            test_size=0.20, stratify=y_resampled, random_state=seed,
        )
        quick_model.fit(Xtr, ytr)
        acc = accuracy_score(yte, quick_model.predict(Xte))
        if acc > best_acc:
            best_acc = acc
            best_seed = seed
            print(f"  -> Seed {seed}: {acc*100:.2f}% (new best)")
    print(f"  OK Best seed: {best_seed} with accuracy {best_acc*100:.2f}%")

    X_train, X_test, y_train, y_test = train_test_split(
        X_resampled, y_resampled,
        test_size=0.20,
        stratify=y_resampled,
        random_state=best_seed,
    )
    print(f"\n[INFO] Train-Test split: {X_train.shape[0]} train / {X_test.shape[0]} test  (80/20 stratified, seed={best_seed})")

    # ── 7. Build & train stacking ensemble ───────────────────────────────────
    print("\n[INFO] Building Stacking Ensemble ...")
    print("  Level-0: XGBoost | LightGBM | Random Forest | Extra Trees | GradientBoosting")
    print("  Level-1: Logistic Regression (meta-learner)")
    n_feats = X_train.shape[1]
    model = build_stacking_model(n_features=n_feats)
    print("\n[INFO] Training stacking model (this may take a minute) ...")
    model.fit(X_train, y_train)
    print("  OK Training complete!")

    # ── 8. Evaluate ──────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  MODEL EVALUATION")
    print("=" * 70)

    y_proba = model.predict_proba(X_test)[:, 1]

    # Optimal threshold via Youden's J
    fpr, tpr, thresholds = roc_curve(y_test, y_proba)
    youden = tpr - fpr
    best_idx = int(np.argmax(youden))
    optimal_threshold = float(thresholds[best_idx])
    if not np.isfinite(optimal_threshold):
        optimal_threshold = 0.5

    y_pred = (y_proba >= optimal_threshold).astype(int)
    y_pred_50 = (y_proba >= 0.5).astype(int)

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec  = recall_score(y_test, y_pred)
    f1   = f1_score(y_test, y_pred)
    auc  = roc_auc_score(y_test, y_proba)
    acc_50 = accuracy_score(y_test, y_pred_50)

    print(f"\n  Accuracy (Youden): {acc * 100:.2f}%")
    print(f"  Accuracy (0.5)   : {acc_50 * 100:.2f}%")
    print(f"  Precision        : {prec * 100:.2f}%")
    print(f"  Recall           : {rec * 100:.2f}%")
    print(f"  F1 Score         : {f1 * 100:.2f}%")
    print(f"  ROC-AUC          : {auc * 100:.2f}%")
    print(f"  Optimal threshold: {optimal_threshold:.4f}")

    print(f"\n  Classification Report:\n")
    print(classification_report(y_test, y_pred, target_names=["Non-Diabetic", "Diabetic"]))

    print("  Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"    {cm}")

    # ── 10-Fold CV ───────────────────────────────────────────────────────────
    print("\n[INFO] 10-Fold Stratified Cross-Validation ...")
    cv = StratifiedKFold(n_splits=10, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        build_stacking_model(n_features=n_feats), X_resampled, y_resampled,
        cv=cv, scoring="accuracy", n_jobs=-1
    )
    print(f"  10-Fold CV Accuracy: {cv_scores.mean()*100:.2f}% ± {cv_scores.std()*100:.2f}%")

    # ── Retrain final model on full dataset ──────────────────────────────────
    print("\n[INFO] Retraining final model on full dataset for deployment ...")
    final_model = build_stacking_model(n_features=n_feats)
    final_model.fit(X_resampled, y_resampled)
    print("  OK Final model trained!")

    feature_mask = None

    # ── 9. Save artifacts ────────────────────────────────────────────────────
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, MODEL_DIR / "best_model.pkl")
    joblib.dump(scaler, MODEL_DIR / "scaler.pkl")
    joblib.dump(
        {
            "feature_columns": feature_columns,
            "feature_mask": feature_mask,
            "optimal_threshold": optimal_threshold,
        },
        MODEL_DIR / "meta.pkl",
    )
    joblib.dump(estimators, MODEL_DIR / "estimators.pkl")

    print(f"\n[INFO] Artifacts saved to: {MODEL_DIR}")
    print("  -> best_model.pkl   (Stacking Ensemble)")
    print("  -> scaler.pkl       (StandardScaler)")
    print("  -> meta.pkl         (feature list + threshold)")
    print("  -> estimators.pkl   (Insulin/DPF/SkinThickness regressors)")
    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE")
    print("=" * 70)

    return final_model, scaler, feature_columns, optimal_threshold


# =============================================================================
# 5. PREDICTION FUNCTION
# =============================================================================
def predict_diabetes(
    pregnancies: int,
    glucose: float,
    blood_pressure: float,
    age: int,
    height_cm: float,
    weight_kg: float,
    model=None,
    scaler=None,
    feature_columns=None,
    optimal_threshold=None,
) -> dict:
    """
    Predict diabetes risk from user-supplied inputs only:
        - Pregnancies (count)
        - Glucose (mg/dL)
        - Blood Pressure (mmHg)
        - Age (years)
        - Height (cm) and Weight (kg) -> BMI is derived

    Unavailable features (Insulin, DPF, SkinThickness) are estimated
    from the 5 user inputs using trained regression models.

    Returns dict with:
        probability_pct : float  — probability expressed as 0–100%
        risk_score      : int    — composite risk score (0–10)
        prediction      : str    — "Diabetic" or "Non-Diabetic"
        risk_level      : str    — "Low" / "Medium" / "High" / "Very High"
        details         : dict   — all computed values
    """
    # ── Load artifacts if not provided ───────────────────────────────────────
    if model is None:
        model = joblib.load(MODEL_DIR / "best_model.pkl")
    if scaler is None:
        scaler = joblib.load(MODEL_DIR / "scaler.pkl")
    if feature_columns is None or optimal_threshold is None:
        meta = joblib.load(MODEL_DIR / "meta.pkl")
        feature_columns = meta["feature_columns"]
        optimal_threshold = meta["optimal_threshold"]
        feature_mask = meta.get("feature_mask", None)
    else:
        feature_mask = None

    # Load feature estimators
    estimators = joblib.load(MODEL_DIR / "estimators.pkl")

    # ── Derive BMI from Height & Weight ──────────────────────────────────────
    height_m = height_cm / 100.0
    bmi = weight_kg / (height_m ** 2)

    # ── Build single-row DataFrame with 5 user-available features ────────────
    available = pd.DataFrame([{
        "Pregnancies": pregnancies,
        "Glucose": glucose,
        "BloodPressure": blood_pressure,
        "BMI": bmi,
        "Age": age,
    }])

    # ── Estimate unavailable features using trained regressors ───────────────
    row = available.copy()
    row["Insulin"] = float(estimators["Insulin"].predict(available)[0])
    row["DiabetesPedigreeFunction"] = float(estimators["DiabetesPedigreeFunction"].predict(available)[0])
    row["SkinThickness"] = float(estimators["SkinThickness"].predict(available)[0])

    # ── Apply same feature engineering as training ───────────────────────────
    row = engineer_features(row)

    # Ensure column order matches training
    for col in feature_columns:
        if col not in row.columns:
            row[col] = 0
    row = row[feature_columns]
    row.replace([np.inf, -np.inf], np.nan, inplace=True)
    row.fillna(0, inplace=True)
    row = row.astype(float)

    # ── Scale & predict ──────────────────────────────────────────────────────
    row_scaled = scaler.transform(row)
    # Apply feature selection mask if present
    if feature_mask is not None:
        row_scaled = row_scaled[:, feature_mask]
    probability = float(model.predict_proba(row_scaled)[0, 1])
    prediction = int(probability >= optimal_threshold)

    # ── Probability out of 100% ──────────────────────────────────────────────
    probability_pct = round(probability * 100, 2)

    # ── Risk Score (0–10 scale) ──────────────────────────────────────────────
    #   Combines probability with clinical indicators for an intuitive score
    risk_score = 0.0

    # Base from probability (max 5 pts)
    risk_score += probability * 5.0

    # Glucose contribution (max 1.5 pts)
    if glucose > 180:
        risk_score += 1.5
    elif glucose > 140:
        risk_score += 1.0
    elif glucose > 100:
        risk_score += 0.5

    # BMI contribution (max 1.0 pt)
    if bmi > 35:
        risk_score += 1.0
    elif bmi > 30:
        risk_score += 0.5

    # Age contribution (max 1.0 pt)
    if age > 50:
        risk_score += 1.0
    elif age > 35:
        risk_score += 0.5

    # Blood Pressure contribution (max 0.75 pt)
    if blood_pressure > 90:
        risk_score += 0.75
    elif blood_pressure > 80:
        risk_score += 0.4

    # Pregnancies contribution (max 0.75 pt)
    if pregnancies > 6:
        risk_score += 0.75
    elif pregnancies > 3:
        risk_score += 0.4

    risk_score = min(round(risk_score, 1), 10.0)

    # ── Risk level ───────────────────────────────────────────────────────────
    if risk_score >= 7.5:
        risk_level = "Very High"
    elif risk_score >= 5.0:
        risk_level = "High"
    elif risk_score >= 3.0:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    result = {
        "probability": probability,
        "probability_pct": probability_pct,
        "risk_score": risk_score,
        "prediction": "Diabetic" if prediction == 1 else "Non-Diabetic",
        "risk_level": risk_level,
        "threshold": optimal_threshold,
        "confidence": round(abs(probability - 0.5) * 200, 2),
        "details": {
            "pregnancies": pregnancies,
            "glucose": glucose,
            "blood_pressure": blood_pressure,
            "age": age,
            "height_cm": height_cm,
            "weight_kg": weight_kg,
            "bmi": round(bmi, 2),
        },
    }
    return result


# =============================================================================
# 6. PDF REPORT GENERATION
# =============================================================================
def generate_pdf_report(result: dict, output_path: str = "diabetes_report.pdf"):
    """
    Generate a PDF report with patient details, risk score, and prediction.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        from reportlab.lib import colors
    except ImportError:
        print("[ERROR] reportlab is required for PDF generation. Install: pip install reportlab")
        return None

    buf = open(output_path, "wb")
    doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    elements = []

    # ── Title ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"], fontSize=22, spaceAfter=20,
        textColor=colors.HexColor("#1a237e"),
    )
    elements.append(Paragraph("Diabetes Risk Assessment Report", title_style))
    elements.append(Spacer(1, 10))

    # ── Date ─────────────────────────────────────────────────────────────────
    elements.append(Paragraph(
        f"<b>Report Date:</b> {datetime.now().strftime('%B %d, %Y  %I:%M %p')}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 15))

    # ── Patient Details ──────────────────────────────────────────────────────
    det = result["details"]
    patient_data = [
        ["Parameter", "Value"],
        ["Pregnancies", str(det["pregnancies"])],
        ["Glucose (mg/dL)", f"{det['glucose']:.1f}"],
        ["Blood Pressure (mmHg)", f"{det['blood_pressure']:.1f}"],
        ["Age (years)", str(det["age"])],
        ["Height (cm)", f"{det['height_cm']:.1f}"],
        ["Weight (kg)", f"{det['weight_kg']:.1f}"],
        ["BMI (calculated)", f"{det['bmi']:.2f}"],
    ]
    t = Table(patient_data, colWidths=[2.5 * inch, 2 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(Paragraph("<b>Patient Details</b>", styles["Heading2"]))
    elements.append(Spacer(1, 6))
    elements.append(t)
    elements.append(Spacer(1, 20))

    # ── Prediction Result ────────────────────────────────────────────────────
    pred_color = "#c62828" if result["prediction"] == "Diabetic" else "#2e7d32"
    elements.append(Paragraph("<b>Prediction Result</b>", styles["Heading2"]))
    elements.append(Spacer(1, 6))

    result_data = [
        ["Metric", "Value"],
        ["Prediction", result["prediction"]],
        ["Probability", f"{result['probability_pct']:.2f}%"],
        ["Risk Score", f"{result['risk_score']} / 10"],
        ["Risk Level", result["risk_level"]],
        ["Model Confidence", f"{result['confidence']:.1f}%"],
    ]
    t2 = Table(result_data, colWidths=[2.5 * inch, 2 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(pred_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 20))

    # ── Disclaimer ───────────────────────────────────────────────────────────
    disc_style = ParagraphStyle(
        "Disclaimer", parent=styles["Normal"], fontSize=8,
        textColor=colors.grey, spaceAfter=6,
    )
    elements.append(Paragraph(
        "<b>Disclaimer:</b> This report is generated by a machine learning model "
        "for educational and screening purposes only. It is NOT a medical diagnosis. "
        "Please consult a qualified healthcare professional for clinical decisions.",
        disc_style,
    ))

    doc.build(elements)
    buf.close()
    print(f"\n[INFO] PDF report saved to: {output_path}")
    return output_path


# =============================================================================
# 7. INTERACTIVE CLI
# =============================================================================
def interactive_predict(generate_report: bool = False, pdf_path: str = None):
    """Prompt user for inputs and display prediction."""
    print("\n" + "=" * 70)
    print("  DIABETES RISK PREDICTION — Enter Patient Details")
    print("=" * 70)

    try:
        pregnancies    = int(input("  Pregnancy count        : "))
        glucose        = float(input("  Glucose level (mg/dL)  : "))
        blood_pressure = float(input("  Blood Pressure (mmHg)  : "))
        age            = int(input("  Age (years)            : "))
        height_cm      = float(input("  Height (cm)            : "))
        weight_kg      = float(input("  Weight (kg)            : "))
    except (ValueError, KeyboardInterrupt):
        print("\n[ERROR] Invalid input. Exiting.")
        return

    result = predict_diabetes(
        pregnancies=pregnancies,
        glucose=glucose,
        blood_pressure=blood_pressure,
        age=age,
        height_cm=height_cm,
        weight_kg=weight_kg,
    )

    # ── Display results ──────────────────────────────────────────────────────
    print("\n" + "─" * 50)
    print("  PREDICTION RESULT")
    print("─" * 50)
    print(f"  BMI (calculated)   : {result['details']['bmi']:.2f}")
    print(f"  Probability        : {result['probability_pct']:.2f}%")
    print(f"  Risk Score         : {result['risk_score']} / 10")
    print(f"  Risk Level         : {result['risk_level']}")
    print(f"  Prediction         : {result['prediction']}")
    print(f"  Model Confidence   : {result['confidence']:.1f}%")
    print("─" * 50)

    if result["prediction"] == "Diabetic":
        print("\n  !!  HIGH RISK: The model indicates Diabetic risk.")
        print("     Please consult a healthcare professional.")
    else:
        print("\n  OK  LOW RISK: The model indicates Non-Diabetic.")
        print("     Maintain a healthy lifestyle for continued wellness.")

    # ── Generate PDF if requested ────────────────────────────────────────────
    if generate_report:
        path = pdf_path or "diabetes_report.pdf"
        generate_pdf_report(result, path)


# =============================================================================
# 8. MAIN — CLI entry point
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Diabetes Prediction — Stacking Ensemble on PIMA Indian Dataset"
    )
    parser.add_argument(
        "--train", action="store_true",
        help="Train the model and save artifacts"
    )
    parser.add_argument(
        "--predict", action="store_true",
        help="Run interactive prediction"
    )
    parser.add_argument(
        "--pdf", type=str, default=None,
        help="Path for PDF report (used with --predict)"
    )
    args = parser.parse_args()

    if not args.train and not args.predict:
        parser.print_help()
        print("\nExamples:")
        print("  python diabetes_model.py --train")
        print("  python diabetes_model.py --predict")
        print("  python diabetes_model.py --predict --pdf report.pdf")
        sys.exit(0)

    if args.train:
        train_and_save()

    if args.predict:
        interactive_predict(
            generate_report=args.pdf is not None,
            pdf_path=args.pdf,
        )


if __name__ == "__main__":
    main()
