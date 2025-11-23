# Generated migration for fixing duplicate language field

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        # Remove the old language field with wrong choices
        migrations.RemoveField(
            model_name='userprofile',
            name='language',
        ),
        # Re-add with correct choices
        migrations.AddField(
            model_name='userprofile',
            name='language',
            field=models.CharField(
                choices=[('en', 'English'), ('bn', 'Bengali')],
                default='en',
                max_length=2
            ),
        ),
    ]
