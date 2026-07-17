"""
Management command to reset admin password
Run: python manage.py reset_admin_password
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset password for admin user'

    def handle(self, *args, **options):
        username = 'munashe'
        new_password = 'Farmwise2024!'  # Change this to desired password
        
        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully reset password for user {username}')
            )
            self.stdout.write(f'New password: {new_password}')
            self.stdout.write('Please change this password after first login.')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User {username} does not exist')
            )
