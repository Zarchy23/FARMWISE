#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from core.models import User

# Get all users
all_users = User.objects.all().values('id', 'username', 'profile_picture')

print("All users and their profile_picture values:")
for user in all_users:
    print(f"ID: {user['id']}, Username: {user['username']}, profile_picture: '{user['profile_picture']}'")
