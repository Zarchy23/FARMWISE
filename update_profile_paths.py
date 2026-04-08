#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import User

# Update all users to point to correct profile picture location if they have the old path
users = User.objects.all()
for user in users:
    if user.profile_picture:
        old_path = str(user.profile_picture)
        print(f"User: {user.username}, Old path: {old_path}")
        
        if not old_path.startswith('profiles/'):
            # Extract filename and create new path
            filename = old_path.split('/')[-1]
            new_path = f'profiles/{filename}'
            user.profile_picture = new_path
            user.save()
            print(f"  Updated to: {new_path}")

# Also, manually set for our test user
user = User.objects.filter(username='munashe').first()
if user:
    user.profile_picture = 'profiles/istockphoto-483451251-612x612.jpg'
    user.save()
    print(f"\nSet munashe's profile picture to: {user.profile_picture}")
    print(f"Profile picture URL would be: {user.profile_picture.url}")
