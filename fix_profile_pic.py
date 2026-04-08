#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import User

# Get users with profile pictures
users_with_pics = User.objects.filter(profile_picture__isnull=False).exclude(profile_picture='')

if users_with_pics.exists():
    for user in users_with_pics:
        old_path = str(user.profile_picture)
        print(f"User: {user.username}")
        print(f"Old profile_picture path: {old_path}")
        
        # Get just the filename
        filename = old_path.split('/')[-1]
        new_path = f'profiles/{filename}'
        
        # Only update if not already correct
        if not old_path.startswith('profiles/'):
            user.profile_picture = new_path
            user.save()
            print(f"Updated to: {new_path}")
        else:
            print(f"Already correct: {old_path}")
        print()
else:
    print("No users with profile pictures found")
