#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import User, PestReport
from django.contrib.auth.models import Group

print("\n" + "=" * 80)
print("AGRONOMIST FARM ASSIGNMENT STATUS")
print("=" * 80)

# Check for agronomists in the system
agronomists_group = Group.objects.filter(name='Agronomists').first()
if agronomists_group:
    agronomists = agronomists_group.user_set.all()
    print(f"\n📊 Found {agronomists.count()} agronomists in system:")
    for agronomist in agronomists[:5]:
        assigned_farms = agronomist.assigned_farms.all()
        print(f"\n  👤 {agronomist.get_full_name() or agronomist.username}")
        print(f"     - Assigned farms: {assigned_farms.count()}")
        if assigned_farms.count() > 0:
            for farm in assigned_farms:
                farm_reports = PestReport.objects.filter(farm=farm).count()
                print(f"       • {farm.name} ({farm_reports} reports)")
else:
    print("\n⚠️  No 'Agronomists' group found")

print("\n" + "=" * 80)
print("ALL PEST REPORTS BY FARM")
print("=" * 80)

from core.models import Farm
from collections import defaultdict

reports_by_farm = defaultdict(list)
for report in PestReport.objects.all():
    reports_by_farm[report.farm.name].append(report)

for farm_name, reports in sorted(reports_by_farm.items()):
    print(f"\n🌾 {farm_name} ({len(reports)} reports)")
    for r in reports[:2]:  # Show first 2 per farm
        real_data = r.confidence > 0 and r.ai_diagnosis != "Unable to analyze automatically"
        badge = "✅ REAL AI" if real_data else "⚠️  FALLBACK"
        print(f"   {badge} - {r.ai_diagnosis} ({r.confidence}%) - {r.created_at.strftime('%Y-%m-%d %H:%M')}")

print("\n" + "=" * 80)
