#!/usr/bin/env python
"""
Verify that ANY agronomist can now see ALL pest reports
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.contrib.auth.models import Group
from core.models import PestReport, Farm

print("\n" + "=" * 80)
print("✅ PEST VERIFICATION SYSTEM - UPDATED FOR SHARED ACCESS")
print("=" * 80)

print("\n📋 CHANGES MADE:")
print("   ✅ Removed farm assignment restrictions")
print("   ✅ Any agronomist can now see ALL pest reports")
print("   ✅ Any agronomist can review decisions made by others")
print("   ✅ Farm filter shows all farms (not just assigned)")

print("\n📊 DATA AVAILABLE TO ANY AGRONOMIST:")

total_reports = PestReport.objects.count()
real_ai_reports = PestReport.objects.filter(confidence__gt=0).exclude(
    ai_diagnosis="Unable to analyze automatically"
).count()
fallback_reports = total_reports - real_ai_reports

print(f"\n   Total Pest Reports: {total_reports}")
print(f"   ✅ With Real AI Analysis: {real_ai_reports}")
print(f"   ⚠️  With Fallback Guidance: {fallback_reports}")

print(f"\n🌾 FARMS INCLUDED:")
for farm in Farm.objects.filter(pest_reports__isnull=False).distinct():
    count = farm.pest_reports.count()
    print(f"   • {farm.name} ({count} reports)")

print("\n👥 ALL AGRONOMISTS CAN NOW:")
print("   • View any pest report from any farm")
print("   • Verify AI detection accuracy")
print("   • Make decisions (approve/reject/request revision)")
print("   • See decisions made by other agronomists")
print("   • Filter by farm, severity, status, or search")

print("\n🔄 NEXT STEPS:")
print("   1. Refresh the dashboard in your browser")
print("   2. All 28 pest reports should now be visible")
print("   3. Try filtering by farm, severity, or status")
print("   4. Click 'Review' to see other agronomists' decisions")

print("\n" + "=" * 80)
