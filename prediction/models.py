"""
Models for Diabetes Prediction application.
"""
from django.db import models
from django.contrib.auth.models import User


class Prediction(models.Model):
    """Stores user prediction history."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions', null=True, blank=True)
    
    # Input features
    pregnancies = models.PositiveIntegerField(default=0)
    glucose = models.FloatField()
    blood_pressure = models.FloatField()
    skin_thickness = models.FloatField()
    insulin = models.FloatField()
    bmi = models.FloatField()
    diabetes_pedigree_function = models.FloatField()
    age = models.PositiveIntegerField()
    
    # Results
    probability = models.FloatField()
    risk_level = models.CharField(max_length=20)  # Low, Medium, High
    prediction_result = models.CharField(max_length=20)  # Diabetic, Non-Diabetic
    predicted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-predicted_at']
    
    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.prediction_result}"


class SurveyResponse(models.Model):
    """Stores survey contributions from users."""
    OUTCOME_CHOICES = [
        (0, 'No Diabetes'),
        (1, 'Diabetes'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='survey_responses', null=True, blank=True)
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    pregnancies = models.PositiveIntegerField(default=0)
    height = models.FloatField(help_text="Height in cm")
    weight = models.FloatField(help_text="Weight in kg")
    glucose = models.FloatField(help_text="Glucose level mg/dL")
    blood_pressure = models.FloatField(help_text="Blood Pressure mmHg")
    outcome = models.IntegerField(choices=OUTCOME_CHOICES, help_text="0 = No Diabetes, 1 = Diabetes")
    date_recorded = models.DateTimeField()
    
    class Meta:
        ordering = ['-date_recorded']
    
    def __str__(self):
        return f"{self.name} - {'Diabetes' if self.outcome == 1 else 'No Diabetes'} ({self.date_recorded.strftime('%Y-%m-%d')})"
