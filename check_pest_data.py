#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import PestReport

count = PestReport.objects.count()
print(f'\nTotal PestReports in database: {count}\n')

if count > 0:
    print("=" * 80)
    print("Recent Pest Reports:")
    print("=" * 80)
    for r in PestReport.objects.all().order_by('-created_at')[:5]:
        print(f"\n📋 Farm: {r.farm.name}")
        print(f"   Farmer: {r.farmer.get_full_name()}")
        print(f"   Diagnosis: {r.ai_diagnosis}")
        print(f"   Confidence: {r.confidence}%")
        print(f"   Severity: {r.severity}")
        print(f"   Status: {r.status}")
        print(f"   Analysis: {(r.analysis_description or 'NO DESCRIPTION')[:80]}...")
        print(f"   Created: {r.created_at}")
else:
    print("⚠️  No pest reports in database yet. Upload an image to create one!")
