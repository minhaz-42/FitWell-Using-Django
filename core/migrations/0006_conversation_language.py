# Generated migration to add language field to Conversation model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_userstats_usagetracking'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('es', 'Spanish'), ('fr', 'French'), ('de', 'German'), ('zh', 'Chinese'), ('ja', 'Japanese'), ('ar', 'Arabic'), ('pt', 'Portuguese'), ('hi', 'Hindi'), ('ko', 'Korean')], default='en', max_length=2),
        ),
    ]
