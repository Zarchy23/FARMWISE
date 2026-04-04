#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmwise.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='munashe')
user.set_password('Admin@123456')
user.save()

print("✓ Superuser password set successfully!")
print(f"\nLogin Credentials:")
print(f"  Username: munashe")
print(f"  Email: tungwararamunashe@gmail.com")
print(f"  Password: Admin@123456")
print(f"\nAccess admin at: http://localhost:8000/admin/")
