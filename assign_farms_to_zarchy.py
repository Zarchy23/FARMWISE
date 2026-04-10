#!/usr/bin/env python
"""
Assign all farms with pest reports to the currently logged-in user
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.contrib.auth.models import Group
from core.models import User, Farm, PestReport

print("\n" + "=" * 80)
print("ASSIGNING FARMS TO CURRENT USER FOR PEST VERIFICATION")
print("=" * 80)

# Get or create Agronomists group
agronomists_group, created = Group.objects.get_or_create(name='Agronomists')

# Check if there's a zarchy user
zarchy = User.objects.filter(username='zarchy').first()
if zarchy:
    print(f"\n👤 Found user: {zarchy.get_full_name() or zarchy.username}")
    
    # Add to Agronomists group
    zarchy.groups.add(agronomists_group)
    print(f"✅ Added to Agronomists group")
    
    # Get all farms with pest reports
    farms_with_reports = Farm.objects.filter(pest_reports__isnull=False).distinct()
    
    print(f"\n📊 Assigning {farms_with_reports.count()} farms to zarchy:")
    for farm in farms_with_reports:
        zarchy.assigned_farms.add(farm)
        report_count = farm.pest_reports.count()
        real_reports = farm.pest_reports.filter(
            confidence__gt=0
        ).exclude(
            ai_diagnosis="Unable to analyze automatically"
        ).count()
        print(f"   ✅ {farm.name}")
        print(f"      • Total reports: {report_count}")
        print(f"      • Real AI data: {real_reports}")
    
    print(f"\n✅ All {zarchy.assigned_farms.count()} farms assigned!")
    
else:
    print("\n❌ Could not find zarchy user")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("DASHBOARD DATA READY")
print("=" * 80)

total = PestReport.objects.count()
real = PestReport.objects.filter(confidence__gt=0).exclude(ai_diagnosis="Unable to analyze automatically").count()

print(f"\n📊 Total pest reports: {total}")
print(f"✅ With real AI analysis: {real}")
print(f"⚠️  Fallback responses: {total - real}")

print(f"\n🔄 Refresh the dashboard now to see all {total} reports!")
print("=" * 80 + "\n")
