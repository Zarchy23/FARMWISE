# core/migrations/0008_enhanced_validation_and_activity.py

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_user_profile_picture'),
    ]

    operations = [
        # New model: ValidationRule for managing validation rules
        migrations.CreateModel(
            name='ValidationRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('format', 'Format'), ('range', 'Range'), ('business_logic', 'Business Logic'), ('relationship', 'Relationship'), ('duplicate', 'Duplicate')], max_length=50)),
                ('rule_code', models.CharField(max_length=100, unique=True)),
                ('message', models.TextField()),
                ('rule_config', models.JSONField(default=dict, help_text='Configuration for the rule')),
                ('is_active', models.BooleanField(default=True)),
                ('applies_to_models', models.JSONField(default=list, help_text='List of model names this rule applies to')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'validation_rules',
            },
        ),
        
        # New model: ValidationLog for tracking validation failures
        migrations.CreateModel(
            name='ValidationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='validation_logs', to='core.user')),
                ('field_name', models.CharField(max_length=255)),
                ('rule_code', models.CharField(max_length=100)),
                ('provided_value', models.TextField(blank=True)),
                ('expected_format', models.CharField(blank=True, max_length=255)),
                ('form_or_api', models.CharField(choices=[('form', 'Web Form'), ('api', 'API'), ('import', 'Bulk Import'), ('mobile', 'Mobile')], max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'validation_logs',
                'indexes': [
                    models.Index(fields=['user', 'created_at'], name='core_validlog_user_cdate_idx'),
                    models.Index(fields=['rule_code'], name='core_validlog_rulecode_idx'),
                ],
            },
        ),
        
        # New model: UserHistory for auto-completion learning
        migrations.CreateModel(
            name='UserHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='field_history', to='core.user')),
                ('field_name', models.CharField(max_length=255)),
                ('field_value', models.TextField()),
                ('usage_count', models.IntegerField(default=1)),
                ('success_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('last_used', models.DateTimeField(auto_now=True)),
                ('first_used', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'user_history',
                'indexes': [
                    models.Index(fields=['user', 'field_name'], name='core_usrhist_user_fname_idx'),
                    models.Index(fields=['user', 'last_used'], name='core_usrhist_user_lastused_idx'),
                ],
            },
        ),
        
        # New model: FarmHistory for farm-level auto-completion
        migrations.CreateModel(
            name='FarmHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='field_history', to='core.farm')),
                ('field_name', models.CharField(max_length=255)),
                ('field_value', models.TextField()),
                ('usage_count', models.IntegerField(default=1)),
                ('success_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('last_used', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'farm_history',
                'indexes': [
                    models.Index(fields=['farm', 'field_name'], name='core_farmhist_farm_fname_idx'),
                ],
            },
        ),
        
        # Enhance AuditLog model with activity-specific fields
        migrations.AddField(
            model_name='auditlog',
            name='is_activity',
            field=models.BooleanField(default=False, help_text='Whether this is a timeline activity'),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='severity',
            field=models.CharField(choices=[('critical', 'Critical'), ('high', 'High'), ('normal', 'Normal'), ('low', 'Low')], default='normal', max_length=20),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='farm',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='activities', to='core.farm'),
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['farm', 'created_at'], name='core_audilt_farm_cdate_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['severity', 'created_at'], name='core_audilt_sever_cdate_idx'),
        ),
    ]
