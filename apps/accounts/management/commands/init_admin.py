from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialize admin user with Super Admin role and permissions'

    def handle(self, *args, **options):
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin')
        admin_first_name = os.environ.get('ADMIN_FIRST_NAME', 'Admin')
        admin_last_name = os.environ.get('ADMIN_LAST_NAME', 'User')

        try:
            if User.objects.filter(email=admin_email).exists():
                self.stdout.write(self.style.SUCCESS(f'Admin user already exists: {admin_email}'))
            else:
                # Use the specialized method that creates a user with Super Admin role
                user = User.create_superAdmin_with_role(
                    email=admin_email,
                    password=admin_password,
                    first_name=admin_first_name,
                    last_name=admin_last_name
                )
                self.stdout.write(self.style.SUCCESS(
                    f'Super Admin created: {user.email} with full permissions'
                ))
        except IntegrityError as e:
            self.stderr.write(self.style.ERROR(f'Error creating admin user: {str(e)}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Unexpected error: {str(e)}'))