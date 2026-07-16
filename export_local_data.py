#!/usr/bin/env python
"""
Export local database data to JSON fixtures for production migration.
This script exports all data from your local database to JSON files that can be loaded in production.
"""

import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import Farm, CropSeason, Animal, Equipment, Worker, Payroll
import sys

def export_data():
    """Export all local database data to JSON fixtures."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"Starting data export at {timestamp}...")
    
    # Export user accounts separately
    print("Exporting user accounts...")
    try:
        with open(f'users_data_{timestamp}.json', 'w') as f:
            call_command('dumpdata', 'auth.User', indent=2, stdout=f)
        print(f"✓ User accounts exported to users_data_{timestamp}.json")
    except Exception as e:
        print(f"✗ Error exporting user accounts: {e}")
    
    # Export core app data (excluding auth users)
    print("Exporting core application data...")
    try:
        with open(f'production_data_{timestamp}.json', 'w') as f:
            # Export all core models except User (handled separately)
            call_command('dumpdata', 'core', indent=2, stdout=f)
        print(f"✓ Core data exported to production_data_{timestamp}.json")
    except Exception as e:
        print(f"✗ Error exporting core data: {e}")
    
    # Export other apps if they exist
    apps_to_export = [
        'analytics',
        'chatbot', 
        'disease',
        'location',
        'market',
        'offline',
        'voice'
    ]
    
    for app in apps_to_export:
        try:
            print(f"Exporting {app} data...")
            with open(f'{app}_data_{timestamp}.json', 'w') as f:
                call_command('dumpdata', app, indent=2, stdout=f)
            print(f"✓ {app} data exported to {app}_data_{timestamp}.json")
        except Exception as e:
            print(f"✗ Error exporting {app} data: {e}")
    
    # Create combined production fixture
    print("Creating combined production fixture...")
    combined_data = []
    
    # Load user accounts
    try:
        with open(f'users_data_{timestamp}.json', 'r') as f:
            user_data = json.load(f)
            combined_data.extend(user_data)
    except FileNotFoundError:
        print("User data file not found, skipping...")
    
    # Load core data
    try:
        with open(f'production_data_{timestamp}.json', 'r') as f:
            core_data = json.load(f)
            combined_data.extend(core_data)
    except FileNotFoundError:
        print("Core data file not found, skipping...")
    
    # Load other app data
    for app in apps_to_export:
        try:
            with open(f'{app}_data_{timestamp}.json', 'r') as f:
                app_data = json.load(f)
                combined_data.extend(app_data)
        except FileNotFoundError:
            print(f"{app} data file not found, skipping...")
    
    # Write combined fixture
    if combined_data:
        with open(f'production_data_{timestamp}.json', 'w') as f:
            json.dump(combined_data, f, indent=2)
        print(f"✓ Combined production data exported to production_data_{timestamp}.json")
    
    print(f"\nExport completed successfully!")
    print(f"Files created:")
    print(f"  - users_data_{timestamp}.json (user accounts)")
    print(f"  - production_data_{timestamp}.json (combined production data)")
    
    print(f"\nNext steps:")
    print(f"1. Review the exported JSON files")
    print(f"2. Upload users_data_{timestamp}.json to your server as users_data.json")
    print(f"3. Upload production_data_{timestamp}.json to your server as production_data.json")
    print(f"4. Deploy to Render - the start.sh script will automatically load these files")

if __name__ == '__main__':
    try:
        export_data()
    except KeyboardInterrupt:
        print("\nExport cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during export: {e}")
        sys.exit(1)
