#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import User, Animal

# Check user profile pictures
print("User profile pictures:")
for user in User.objects.all():
    picture_value = user.profile_picture
    print(f"  {user.username}: {repr(picture_value)} (bool: {bool(picture_value)})")
    if picture_value:
        print(f"    Path: {str(picture_value)}")

print("\nLooking for beetle image...")
users_with_beetle = User.objects.filter(profile_picture__contains='beetle')
print(f"Users with 'beetle' in profile_picture: {users_with_beetle.count()}")
for u in users_with_beetle:
    print(f"  {u.username}: {u.profile_picture}")
