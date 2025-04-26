from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates an admin user with admin role'

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Email address')
        parser.add_argument('--password', required=True, help='Password')
        parser.add_argument('--first_name', default='', help='First name')
        parser.add_argument('--last_name', default='', help='Last name')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        
        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'User with email {email} already exists'))
            return
            
        user = User.create_admin_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'Admin user created: {user.email}'))
