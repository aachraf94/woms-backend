from django.core.management.base import BaseCommand
from apps.accounts.models import Role

class Command(BaseCommand):
    help = 'Initialize the basic roles in the system'

    def handle(self, *args, **options):
        # Create Admin role
        admin_role, created = Role.objects.get_or_create(
            name=Role.ADMIN
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Admin role'))
        else:
            self.stdout.write(self.style.WARNING('Admin role already exists'))
            
        # Create Manager role
        manager_role, created = Role.objects.get_or_create(
            name=Role.MANAGER
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Manager role'))
        else:
            self.stdout.write(self.style.WARNING('Manager role already exists'))
            
        # Create Operator role
        operator_role, created = Role.objects.get_or_create(
            name=Role.OPERATOR
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created Operator role'))
        else:
            self.stdout.write(self.style.WARNING('Operator role already exists'))
