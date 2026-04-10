#!/usr/bin/env python
"""
Setup script to create agronomist user and assign farms for testing
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.contrib.auth.models import Group
from core.models import User, Farm

print("\n" + "=" * 80)
print("SETTING UP AGRONOMIST FOR PEST VERIFICATION DASHBOARD")
print("=" * 80)

# 1. Create Agronomists group if it doesn't exist
agronomists_group, created = Group.objects.get_or_create(name='Agronomists')
if created:
    print("\n✅ Created 'Agronomists' group")
else:
    print("\nℹ️  'Agronomists' group already exists")

# 2. Create or get agronomist user
agronomist_user, created = User.objects.get_or_create(
    username='agronomist_demo',
    defaults={
        'first_name': 'Demo',
        'last_name': 'Agronomist',
        'email': 'agronomist@farmwise.local',
        'phone_number': '+1-555-AGRONOMIST',
        'is_active': True,
    }
)

if created:
    agronomist_user.set_password('agronomist123')
    agronomist_user.save()
    print(f"\n✅ Created agronomist user: agronomist_demo")
    print(f"   Password: agronomist123")
else:
    print(f"\nℹ️  Agronomist user already exists: agronomist_demo")

# 3. Add user to Agronomists group
agronomist_user.groups.add(agronomists_group)
print(f"✅ Assigned user to Agronomists group")

# 4. Assign all farms with pest reports to this agronomist
farms_with_reports = Farm.objects.filter(pest_reports__isnull=False).distinct()
print(f"\n📊 Assigning {farms_with_reports.count()} farms to agronomist:")

for farm in farms_with_reports:
    agronomist_user.assigned_farms.add(farm)
    report_count = farm.pest_reports.count()
    real_reports = farm.pest_reports.filter(confidence__gt=0).exclude(ai_diagnosis="Unable to analyze automatically").count()
    print(f"   • {farm.name} ({report_count} reports, {real_reports} with real AI data)")

print(f"\n✅ {agronomist_user.assigned_farms.count()} farms assigned to agronomist")

# 5. Show summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n🔐 LOGIN CREDENTIALS:")
print(f"   Username: agronomist_demo")
print(f"   Password: agronomist123")
print(f"\n📍 DASHBOARD URL:")
print(f"   http://127.0.0.1:8000/pest-verification/dashboard/")
print(f"\n📊 DATA AVAILABLE:")

from core.models import PestReport
all_reports = PestReport.objects.count()
real_reports = PestReport.objects.filter(confidence__gt=0).exclude(ai_diagnosis="Unable to analyze automatically").count()
fallback_reports = all_reports - real_reports

print(f"   Total reports: {all_reports}")
print(f"   With real AI data: {real_reports} ✅")
print(f"   Fallback responses: {fallback_reports} ⚠️")

print(f"\n✨ Dashboard is ready! Login and visit /pest-verification/dashboard/")
print("=" * 80 + "\n")
