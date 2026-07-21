#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import AuditLog

print(f'Total audit logs: {AuditLog.objects.count()}')
print('\nRecent logs:')
for log in AuditLog.objects.all()[:10]:
    print(f'  {log.id}: {log.user} - {log.action} - {log.model_name} - {log.created_at}')
