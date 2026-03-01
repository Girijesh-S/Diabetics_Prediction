"""
Migration to:
1. Rename Prediction.created_at → predicted_at and update ordering
2. Remove SurveyResponse.created_at
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prediction', '0002_surveyresponse'),
    ]

    operations = [
        # 1. Rename created_at → predicted_at on Prediction
        migrations.RenameField(
            model_name='prediction',
            old_name='created_at',
            new_name='predicted_at',
        ),
        # 2. Update Prediction ordering
        migrations.AlterModelOptions(
            name='prediction',
            options={'ordering': ['-predicted_at']},
        ),
        # 3. Remove created_at from SurveyResponse
        migrations.RemoveField(
            model_name='surveyresponse',
            name='created_at',
        ),
    ]
