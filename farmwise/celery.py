# farmwise/celery.py
# Celery configuration for FarmWise

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')

app = Celery('farmwise')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for automatic ML tasks
app.conf.beat_schedule = {
    # Check model freshness and retrain if needed - Daily at 2 AM
    'check-model-freshness': {
        'task': 'core.tasks.auto_retrain_if_needed',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Generate AI recommendations for all farms - Daily at 6 AM
    'generate-ai-recommendations': {
        'task': 'core.tasks.generate_ai_recommendations_for_all_farms',
        'schedule': crontab(hour=6, minute=0),
    },
    
    # Monitor model performance - Weekly on Sunday at 3 AM
    'monitor-model-performance': {
        'task': 'core.tasks.monitor_model_performance',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },
    
    # Train all models with fresh data - Weekly on Monday at 1 AM
    'train-all-models': {
        'task': 'core.tasks.auto_train_all_models',
        'schedule': crontab(hour=1, minute=0, day_of_week=1),
    },
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
