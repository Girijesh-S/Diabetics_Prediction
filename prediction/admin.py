"""
Admin configuration for prediction app.
"""
from django.contrib import admin
from .models import Prediction, SurveyResponse


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ['user_display', 'prediction_result', 'risk_level', 'probability', 'age', 'glucose', 'blood_pressure', 'predicted_at']
    list_filter = ['risk_level', 'prediction_result', 'predicted_at']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'predicted_at'
    
    def user_display(self, obj):
        """Display 'Anonymous' for predictions without user, otherwise show username."""
        if obj.user is None:
            return "[ANONYMOUS]"
        return obj.user.username
    user_display.short_description = "User"


@admin.register(SurveyResponse)
class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ['name', 'age', 'pregnancies', 'glucose', 'blood_pressure', 'outcome_display', 'date_recorded', 'user']
    list_filter = ['outcome']
    search_fields = ['name', 'user__username']
    
    def outcome_display(self, obj):
        return "Diabetes" if obj.outcome == 1 else "No Diabetes"
    outcome_display.short_description = "Outcome"
