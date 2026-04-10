# Generated migration for analysis_description field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_reminder_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='pestreport',
            name='analysis_description',
            field=models.TextField(blank=True, help_text='Detailed AI analysis of the pest/disease'),
        ),
    ]
