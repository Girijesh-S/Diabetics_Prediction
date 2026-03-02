#!/usr/bin/env python
"""Test script to validate model predictions."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diabetes_web.settings')
django.setup()

from prediction.ml_service import predict_diabetes
import json

print("=" * 70)
print("MODEL PREDICTION TEST")
print("=" * 70)

# Test case 1: Image 2 values (should show healthy, low risk)
print("\n[Test Case 1] Image 2 Values (Low Risk Expected):")
print("-" * 70)
data1 = {
    'Pregnancies': 0,
    'Glucose': 100.0,
    'BloodPressure': 50.0,
    'BMI': 22.2,
    'Age': 25,
}
print(f"Input: {data1}")
try:
    result1 = predict_diabetes(data1)
    print(f"Result: {result1['prediction']}")
    print(f"Probability: {result1['probability_pct']}")
    print(f"Risk Level: {result1['risk_level']}")
    print(f"✓ PASS" if float(result1['probability_pct'].rstrip('%')) < 50 else "✗ FAIL - Expected low probability")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test case 2: High risk values
print("\n[Test Case 2] High Risk Values:")
print("-" * 70)
data2 = {
    'Pregnancies': 2,
    'Glucose': 180.0,
    'BloodPressure': 90.0,
    'BMI': 32.5,
    'Age': 45,
}
print(f"Input: {data2}")
try:
    result2 = predict_diabetes(data2)
    print(f"Result: {result2['prediction']}")
    print(f"Probability: {result2['probability_pct']}")
    print(f"Risk Level: {result2['risk_level']}")
    print(f"✓ PASS - High probability detected" if float(result2['probability_pct'].rstrip('%')) > 50 else "✗ FAIL - Expected high probability")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test case 3: Very high risk values
print("\n[Test Case 3] Very High Risk Values:")
print("-" * 70)
data3 = {
    'Pregnancies': 5,
    'Glucose': 250.0,
    'BloodPressure': 140.0,
    'BMI': 40.0,
    'Age': 55,
}
print(f"Input: {data3}")
try:
    result3 = predict_diabetes(data3)
    print(f"Result: {result3['prediction']}")
    print(f"Probability: {result3['probability_pct']}")
    print(f"Risk Level: {result3['risk_level']}")
    print(f"✓ PASS - Very high probability detected" if float(result3['probability_pct'].rstrip('%')) > 75 else "? PARTIAL - Probability not as high as expected")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test case 4: Classic diabetic case
print("\n[Test Case 4] Classic Diabetic Case:")
print("-" * 70)
data4 = {
    'Pregnancies': 6,
    'Glucose': 148.0,
    'BloodPressure': 72.0,
    'BMI': 33.6,
    'Age': 50,
}
print(f"Input: {data4}")
try:
    result4 = predict_diabetes(data4)
    print(f"Result: {result4['prediction']}")
    print(f"Probability: {result4['probability_pct']}")
    print(f"Risk Level: {result4['risk_level']}")
    print(f"✓ PASS - Diabetic classification" if result4['prediction'] == 'Diabetic' else "✗ FAIL - Expected Diabetic")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
