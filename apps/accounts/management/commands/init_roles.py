from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Initialiser les rôles de base dans le système'

    def handle(self, *args, **options):
        # Les rôles sont maintenant définis dans le modèle CustomUser.Role
        roles_info = [
            (User.Role.ADMIN, 'Administrateur'),
            (User.Role.MANAGER, 'Gestionnaire'), 
            (User.Role.OPERATOR, 'Opérateur'),
            (User.Role.SUPERVISOR, 'Superviseur'),
            (User.Role.ENGINEER, 'Ingénieur'),
            (User.Role.VIEWER, 'Visualiseur'),
        ]
        
        self.stdout.write(self.style.SUCCESS('Rôles disponibles dans le système:'))
        for role_value, role_display in roles_info:
            self.stdout.write(f'  - {role_value}: {role_display}')
        
        # Créer un utilisateur admin par défaut s'il n'existe pas
        admin_email = 'admin@woms.local'
        if not User.objects.filter(email=admin_email).exists():
            admin_user = User.create_admin_user(
                email=admin_email,
                password='admin123',
                first_name='Admin',
                last_name='Système'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Utilisateur admin créé: {admin_email}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Utilisateur admin existe déjà: {admin_email}')
            )
