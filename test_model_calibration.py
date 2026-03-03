#!/usr/bin/env python
"""Test medical calibration of model probabilities."""

from prediction.ml_service import predict_diabetes

print("\n" + "="*60)
print("MODEL MEDICAL CALIBRATION TEST")
print("="*60 + "\n")

# Test 1: Glucose 100 (should now be ~30-40% not 7%)
result = predict_diabetes({
    'Pregnancies': 0,
    'Glucose': 100,
    'BloodPressure': 70,
    'BMI': 23,
    'Age': 30
})
print("Test 1 - Glucose 100, Normal BMI (Prediabetic range):")
print(f"  Probability: {result['probability_pct']}")
print(f"  Risk Level: {result['risk_level']}")
print(f"  Status: {'✓ PASS' if float(result['probability_pct'].rstrip('%')) >= 30 else '✗ FAIL - Too low'}")
print()

# Test 2: Glucose 130, BMI 28 (prediabetic + overweight)
result = predict_diabetes({
    'Pregnancies': 1,
    'Glucose': 130,
    'BloodPressure': 75,
    'BMI': 28,
    'Age': 35
})
print("Test 2 - Glucose 130, BMI 28 (Prediabetic + Overweight):")
print(f"  Probability: {result['probability_pct']}")
print(f"  Risk Level: {result['risk_level']}")
print(f"  Status: {'✓ PASS' if float(result['probability_pct'].rstrip('%')) >= 40 else '✗ FAIL - Too low'}")
print()

# Test 3: Glucose 150, BMI 25
result = predict_diabetes({
    'Pregnancies': 0,
    'Glucose': 150,
    'BloodPressure': 80,
    'BMI': 25,
    'Age': 45
})
print("Test 3 - Glucose 150, BMI 25 (High glucose):")
print(f"  Probability: {result['probability_pct']}")
print(f"  Risk Level: {result['risk_level']}")
print(f"  Status: {'✓ PASS' if float(result['probability_pct'].rstrip('%')) >= 50 else '✗ FAIL - Too low'}")
print()

# Test 4: Glucose 200+ (severe)
result = predict_diabetes({
    'Pregnancies': 2,
    'Glucose': 250,
    'BloodPressure': 85,
    'BMI': 32,
    'Age': 50
})
print("Test 4 - Glucose 250 (Severe Hyperglycemia):")
print(f"  Probability: {result['probability_pct']}")
print(f"  Risk Level: {result['risk_level']}")
print(f"  Status: {'✓ PASS' if float(result['probability_pct'].rstrip('%')) >= 80 else '✗ FAIL - Too low'}")
print()

# Test 5: Low glucose, normal BMI (low risk)
result = predict_diabetes({
    'Pregnancies': 0,
    'Glucose': 80,
    'BloodPressure': 70,
    'BMI': 22,
    'Age': 25
})
print("Test 5 - Glucose 80, Normal BMI (Low risk):")
print(f"  Probability: {result['probability_pct']}")
print(f"  Risk Level: {result['risk_level']}")
print(f"  Status: {'✓ Can be low' if float(result['probability_pct'].rstrip('%')) < 20 else '✓ Acceptable'}")
print()

print("="*60)
print("CALIBRATION COMPLETE")
print("="*60 + "\n")
