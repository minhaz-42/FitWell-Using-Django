# Generated migration for adding database indexes

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_fix_duplicate_language_field'),
    ]

    operations = [
        # Add indexes for UserProfile
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['user'], name='core_userpr_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['activity_level'], name='core_userpr_activity_idx'),
        ),
        
        # Add indexes for HealthAssessment
        migrations.AddIndex(
            model_name='healthassessment',
            index=models.Index(fields=['user', '-assessment_date'], name='core_health_user_date_idx'),
        ),
        migrations.AddIndex(
            model_name='healthassessment',
            index=models.Index(fields=['bmi_category'], name='core_health_bmi_cat_idx'),
        ),
        
        # Add indexes for ProgressTracking
        migrations.AddIndex(
            model_name='progresstracking',
            index=models.Index(fields=['user', '-date'], name='core_progress_user_date_idx'),
        ),
    ]
