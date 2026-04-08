#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import WeatherAlert, PestReport, WeatherData

# Check pest reports with beetle image  
print("Pest reports with beetle image:")
reports = PestReport.objects.filter(image__contains='beetle')
print(f"Count: {reports.count()}")
for report in reports:
    print(f"  Report {report.id}: {report.image}")

# Check all pest reports
print("\nAll pest reports (first 5):")
for report in PestReport.objects.all()[:5]:
    print(f"  Report {report.id}: {report.image}")
