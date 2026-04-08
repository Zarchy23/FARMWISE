# Generated migration for Phase 2-6 models

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_enhanced_validation_and_activity'),
    ]

    operations = [
        # Phase 2: Contextual Help System
        migrations.CreateModel(
            name='HelpContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('crops', 'Crops'), ('livestock', 'Livestock'), ('equipment', 'Equipment'), ('market', 'Marketplace'), ('financial', 'Financial'), ('reporting', 'Reporting'), ('general', 'General')], max_length=50)),
                ('trigger_type', models.CharField(choices=[('first_time', 'First Time User'), ('inactivity', 'Inactivity Alert'), ('error_recovery', 'Error Recovery'), ('opportunity', 'Opportunity-Based'), ('manual_request', 'Manual Request')], max_length=50)),
                ('content_type', models.CharField(choices=[('text', 'Text'), ('video', 'Video'), ('guide', 'Step-by-Step Guide'), ('faq', 'FAQ'), ('tooltip', 'Tooltip')], max_length=50)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('video_url', models.URLField(blank=True, null=True)),
                ('target_page', models.CharField(blank=True, help_text='e.g., /crops/create/', max_length=255)),
                ('target_element', models.CharField(blank=True, help_text='CSS selector for element to highlight', max_length=255)),
                ('priority', models.IntegerField(default=0, help_text='Higher number = shown first')),
                ('is_active', models.BooleanField(default=True)),
                ('view_count', models.IntegerField(default=0)),
                ('helpful_count', models.IntegerField(default=0)),
                ('not_helpful_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'help_content',
                'ordering': ['-priority', '-created_at'],
            },
        ),
        
        # Phase 3: Templates
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('category', models.CharField(choices=[('crop_plan', 'Crop Plan'), ('treatment', 'Treatment'), ('equipment_listing', 'Equipment Listing'), ('schedule', 'Schedule'), ('report', 'Report')], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('template_data', models.JSONField(help_text='Serialized template configuration')),
                ('share_level', models.CharField(choices=[('private', 'Private'), ('farm', 'Farm Only'), ('cooperative', 'Cooperative'), ('public', 'Public Marketplace')], default='private', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, default=0, help_text='Price if shared on marketplace', max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('usage_count', models.IntegerField(default=0)),
                ('average_rating', models.DecimalField(decimal_places=2, default=0, max_digits=3)),
                ('total_ratings', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('farm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='templates', to='core.farm')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='templates', to='core.user')),
            ],
            options={
                'db_table': 'templates',
                'ordering': ['-created_at'],
            },
        ),

        migrations.CreateModel(
            name='TemplateRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ('review', models.TextField(blank=True)),
                ('is_helpful', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ratings', to='core.template')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.user')),
            ],
            options={
                'db_table': 'template_ratings',
                'unique_together': {('template', 'user')},
            },
        ),

        # Phase 3: Recurring Actions
        migrations.CreateModel(
            name='RecurringAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('frequency', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('seasonal', 'Seasonal'), ('custom', 'Custom CRON')], max_length=20)),
                ('cron_expression', models.CharField(help_text='CRON expression for scheduling', max_length=255)),
                ('action_config', models.JSONField(help_text='Action-specific configuration data')),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed'), ('archived', 'Archived')], default='active', max_length=20)),
                ('next_due', models.DateTimeField(blank=True, null=True)),
                ('last_executed', models.DateTimeField(blank=True, null=True)),
                ('execution_count', models.IntegerField(default=0)),
                ('missed_count', models.IntegerField(default=0)),
                ('paused_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ManyToManyField(blank=True, related_name='assigned_recurring_actions', to='core.user')),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recurring_actions', to='core.farm')),
            ],
            options={
                'db_table': 'recurring_actions',
                'ordering': ['next_due', '-created_at'],
            },
        ),

        migrations.CreateModel(
            name='RecurringActionLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_for', models.DateTimeField()),
                ('executed_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('executed', 'Executed'), ('missed', 'Missed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('result_data', models.JSONField(blank=True, help_text='Result or error details', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('action', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='execution_logs', to='core.recurringaction')),
                ('executed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.user')),
            ],
            options={
                'db_table': 'recurring_action_logs',
                'ordering': ['-scheduled_for'],
            },
        ),

        # Phase 3: Batch Operations
        migrations.CreateModel(
            name='BatchOperation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operation_type', models.CharField(choices=[('crop_harvest', 'Bulk Crop Harvest'), ('price_update', 'Price Update'), ('status_change', 'Status Change'), ('data_export', 'Data Export'), ('field_update', 'Field Data Update')], max_length=50)),
                ('description', models.CharField(max_length=255)),
                ('record_count', models.IntegerField()),
                ('record_ids', models.JSONField(help_text='List of affected record IDs')),
                ('parameters', models.JSONField(help_text='Operation-specific parameters')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('progress_percent', models.IntegerField(default=0)),
                ('results', models.JSONField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batch_operations', to='core.farm')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='batch_operations', to='core.user')),
            ],
            options={
                'db_table': 'batch_operations',
                'ordering': ['-created_at'],
            },
        ),

        # Phase 4: Predictions
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prediction_type', models.CharField(choices=[('harvest_date', 'Harvest Date'), ('yield_estimate', 'Yield Estimate'), ('pest_risk', 'Pest Risk'), ('price_forecast', 'Price Forecast'), ('maintenance_needed', 'Maintenance Needed'), ('disease_risk', 'Disease Risk'), ('water_requirement', 'Water Requirement')], max_length=50)),
                ('object_type', models.CharField(choices=[('crop', 'Crop'), ('field', 'Field'), ('animal', 'Animal'), ('equipment', 'Equipment'), ('market', 'Market Price')], max_length=50)),
                ('object_id', models.IntegerField(help_text='ID of the related object (crop, field, animal, etc.)')),
                ('predicted_value', models.CharField(help_text='The prediction result', max_length=255)),
                ('confidence_score', models.DecimalField(decimal_places=2, max_digits=3, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('forecast_date', models.DateField(help_text='Date when prediction applies')),
                ('model_version', models.CharField(default='v1', max_length=50)),
                ('reasoning', models.TextField(blank=True, help_text='Explanation for the prediction')),
                ('factors_used', models.JSONField(default=list, help_text='List of factors used in prediction')),
                ('is_actionable', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('farm', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='predictions', to='core.farm')),
            ],
            options={
                'db_table': 'predictions',
                'ordering': ['-forecast_date', '-confidence_score'],
            },
        ),

        # Phase 5: Scheduled Exports
        migrations.CreateModel(
            name='ScheduledExport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('export_type', models.CharField(choices=[('crops', 'Crop Data'), ('livestock', 'Livestock Data'), ('financial', 'Financial Summary'), ('marketplace', 'Marketplace Activity'), ('custom', 'Custom Report')], max_length=50)),
                ('file_format', models.CharField(choices=[('csv', 'CSV'), ('json', 'JSON'), ('xlsx', 'Excel'), ('pdf', 'PDF'), ('html', 'HTML')], max_length=20)),
                ('frequency', models.CharField(choices=[('once', 'One-Time'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='once', max_length=20)),
                ('filters', models.JSONField(blank=True, default=dict, help_text='Export filters (date range, etc.)')),
                ('email_recipients', models.JSONField(default=list, help_text='List of email addresses')),
                ('include_summary', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('next_run', models.DateTimeField(blank=True, null=True)),
                ('run_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('farm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.farm')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scheduled_exports', to='core.user')),
            ],
            options={
                'db_table': 'scheduled_exports',
                'ordering': ['next_run', '-created_at'],
            },
        ),

        # Phase 6: Workspace Preferences
        migrations.CreateModel(
            name='WorkspacePreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('primary_workspace', models.CharField(choices=[('farmer', 'Farmer View'), ('agronomist', 'Agronomist View'), ('coop_manager', 'Cooperative Manager'), ('equipment_owner', 'Equipment Owner'), ('trader', 'Market Trader'), ('admin', 'Administrator')], max_length=50)),
                ('secondary_workspaces', models.JSONField(default=list, help_text='List of secondary workspace types')),
                ('last_accessed_workspace', models.CharField(choices=[('farmer', 'Farmer View'), ('agronomist', 'Agronomist View'), ('coop_manager', 'Cooperative Manager'), ('equipment_owner', 'Equipment Owner'), ('trader', 'Market Trader'), ('admin', 'Administrator')], max_length=50)),
                ('last_accessed_at', models.DateTimeField(auto_now=True)),
                ('workspace_state', models.JSONField(default=dict, help_text='Saved state for each workspace (filters, views, etc.)')),
                ('quick_stats_layout', models.JSONField(default=dict, help_text='Dashboard widget configuration')),
                ('theme_preference', models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('auto', 'Auto')], default='auto', max_length=20)),
                ('notifications_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('default_farm', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.farm')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='workspace_preference', to='core.user')),
            ],
            options={
                'db_table': 'workspace_preferences',
            },
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='helpcontent',
            index=models.Index(fields=['category', 'trigger_type'], name='help_conten_catego_0a1b2c_idx'),
        ),
        migrations.AddIndex(
            model_name='helpcontent',
            index=models.Index(fields=['is_active', 'priority'], name='help_conten_is_activ_1a2b3c_idx'),
        ),
        migrations.AddIndex(
            model_name='helpcontent',
            index=models.Index(fields=['target_page'], name='help_conten_target_2a3b4c_idx'),
        ),
        migrations.AddIndex(
            model_name='template',
            index=models.Index(fields=['user', 'category'], name='templates_user_categ_3a4b5c_idx'),
        ),
        migrations.AddIndex(
            model_name='template',
            index=models.Index(fields=['share_level', 'is_active'], name='templates_share_lev_4a5b6c_idx'),
        ),
        migrations.AddIndex(
            model_name='template',
            index=models.Index(fields=['farm'], name='templates_farm_5a6b7c_idx'),
        ),
        migrations.AddIndex(
            model_name='templaterating',
            index=models.Index(fields=['template'], name='template_rat_templat_6a7b8c_idx'),
        ),
        migrations.AddIndex(
            model_name='templaterating',
            index=models.Index(fields=['rating'], name='template_rat_rating_7a8b9c_idx'),
        ),
        migrations.AddIndex(
            model_name='recurringaction',
            index=models.Index(fields=['farm', 'status'], name='recurring_actio_farm_8a9b0c_idx'),
        ),
        migrations.AddIndex(
            model_name='recurringaction',
            index=models.Index(fields=['next_due'], name='recurring_actio_next_due_9a0b1c_idx'),
        ),
        migrations.AddIndex(
            model_name='recurringaction',
            index=models.Index(fields=['frequency'], name='recurring_actio_freq_0a1b2d_idx'),
        ),
        migrations.AddIndex(
            model_name='recurringactionlog',
            index=models.Index(fields=['action', 'scheduled_for'], name='recurring_act_log_1a2b3d_idx'),
        ),
        migrations.AddIndex(
            model_name='recurringactionlog',
            index=models.Index(fields=['status'], name='recurring_act_log_status_2a3b4d_idx'),
        ),
        migrations.AddIndex(
            model_name='batchoperation',
            index=models.Index(fields=['user', 'status'], name='batch_oper_user_stat_3a4b5d_idx'),
        ),
        migrations.AddIndex(
            model_name='batchoperation',
            index=models.Index(fields=['farm', 'created_at'], name='batch_oper_farm_crea_4a5b6d_idx'),
        ),
        migrations.AddIndex(
            model_name='prediction',
            index=models.Index(fields=['farm', 'prediction_type'], name='prediction_farm_pred_5a6b7d_idx'),
        ),
        migrations.AddIndex(
            model_name='prediction',
            index=models.Index(fields=['forecast_date'], name='prediction_forecast_6a7b8d_idx'),
        ),
        migrations.AddIndex(
            model_name='prediction',
            index=models.Index(fields=['confidence_score'], name='prediction_confid_7a8b9d_idx'),
        ),
        migrations.AddIndex(
            model_name='scheduledexport',
            index=models.Index(fields=['user', 'is_active'], name='scheduled_export_user_8a9b0d_idx'),
        ),
        migrations.AddIndex(
            model_name='scheduledexport',
            index=models.Index(fields=['farm', 'frequency'], name='scheduled_export_farm_9a0b1d_idx'),
        ),
        migrations.AddIndex(
            model_name='scheduledexport',
            index=models.Index(fields=['next_run'], name='scheduled_export_next_0a1b2e_idx'),
        ),
        migrations.AddIndex(
            model_name='workspacepreference',
            index=models.Index(fields=['primary_workspace'], name='workspace_primary_1a2b3e_idx'),
        ),
        migrations.AddIndex(
            model_name='workspacepreference',
            index=models.Index(fields=['last_accessed_at'], name='workspace_last_acc_2a3b4e_idx'),
        ),
    ]
