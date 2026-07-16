#!/usr/bin/env python
"""
Export local database data to JSON fixtures for production migration.
This script exports all data from your local database to JSON files that can be loaded in production.
"""

import os
import django
import json
from datetime import datetime
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings
from io import StringIO

def export_data():
    """Export all local database data to JSON fixtures."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Starting data export at {timestamp}...")
    
    # Get installed apps
    installed_apps = [app.split('.')[-1] for app in settings.INSTALLED_APPS]
    print(f"Installed apps: {installed_apps}")
    
    # Export user accounts separately
    print("Exporting user accounts...")
    try:
        output = StringIO()
        call_command('dumpdata', 'auth.User', indent=2, stdout=output)
        user_data = json.loads(output.getvalue())
        
        with open(f'users_data_{timestamp}.json', 'w') as f:
            json.dump(user_data, f, indent=2)
        print(f"✓ User accounts exported to users_data_{timestamp}.json ({len(user_data)} records)")
    except Exception as e:
        print(f"✗ Error exporting user accounts: {e}")
        user_data = []
    
    # Export core app data (excluding auth users)
    print("Exporting core application data...")
    try:
        output = StringIO()
        call_command('dumpdata', 'core', indent=2, stdout=output)
        core_data = json.loads(output.getvalue())
        
        with open(f'core_data_{timestamp}.json', 'w') as f:
            json.dump(core_data, f, indent=2)
        print(f"✓ Core data exported to core_data_{timestamp}.json ({len(core_data)} records)")
    except Exception as e:
        print(f"✗ Error exporting core data: {e}")
        core_data = []
    
    # Export analytics data if it exists
    if 'analytics' in installed_apps:
        print("Exporting analytics data...")
        try:
            output = StringIO()
            call_command('dumpdata', 'analytics', indent=2, stdout=output)
            analytics_data = json.loads(output.getvalue())
            
            with open(f'analytics_data_{timestamp}.json', 'w') as f:
                json.dump(analytics_data, f, indent=2)
            print(f"✓ Analytics data exported to analytics_data_{timestamp}.json ({len(analytics_data)} records)")
        except Exception as e:
            print(f"✗ Error exporting analytics data: {e}")
            analytics_data = []
    else:
        print("Analytics app not installed, skipping...")
        analytics_data = []
    
    # Create combined production fixture
    print("Creating combined production fixture...")
    combined_data = []
    
    # Add user accounts
    if user_data:
        combined_data.extend(user_data)
        print(f"  - Added {len(user_data)} user records")
    
    # Add core data
    if core_data:
        combined_data.extend(core_data)
        print(f"  - Added {len(core_data)} core records")
    
    # Add analytics data
    if analytics_data:
        combined_data.extend(analytics_data)
        print(f"  - Added {len(analytics_data)} analytics records")
    
    # Write combined fixture
    if combined_data:
        with open(f'production_data_{timestamp}.json', 'w') as f:
            json.dump(combined_data, f, indent=2)
        print(f"✓ Combined production data exported to production_data_{timestamp}.json ({len(combined_data)} total records)")
    else:
        print("✗ No data to export in combined fixture")
    
    print(f"\nExport completed successfully!")
    print(f"Files created:")
    if user_data:
        print(f"  - users_data_{timestamp}.json ({len(user_data)} user accounts)")
    if core_data:
        print(f"  - core_data_{timestamp}.json ({len(core_data)} core records)")
    if analytics_data:
        print(f"  - analytics_data_{timestamp}.json ({len(analytics_data)} analytics records)")
    if combined_data:
        print(f"  - production_data_{timestamp}.json ({len(combined_data)} total records)")
    
    print(f"\nNext steps:")
    print(f"1. Review the exported JSON files")
    if user_data:
        print(f"2. Rename users_data_{timestamp}.json to users_data.json and commit to repository")
    if combined_data:
        print(f"3. Rename production_data_{timestamp}.json to production_data.json and commit to repository")
    print(f"4. Deploy to Render - the start.sh script will automatically load these files")

if __name__ == '__main__':
    try:
        export_data()
    except KeyboardInterrupt:
        print("\nExport cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
