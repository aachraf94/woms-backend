from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import FournisseurService, ProfilUtilisateur, JournalConnexion, TokenJWT

User = get_user_model()

class CustomUserModelTest(TestCase):
    """Tests pour le modèle CustomUser."""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'entreprise': 'Test Company',
            'fonction': 'Developer'
        }
    
    def test_create_user(self):
        """Test de création d'un utilisateur."""
        user = User.objects.create_user(
            password='testpass123',
            **self.user_data
        )
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.entreprise, self.user_data['entreprise'])
        self.assertEqual(user.fonction, self.user_data['fonction'])
        self.assertTrue(user.check_password('testpass123'))
        self.assertEqual(user.role, User.Role.VIEWER)  # Rôle par défaut
    
    def test_create_admin_user(self):
        """Test de création d'un utilisateur admin."""
        admin = User.create_admin_user(
            email='admin@example.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User'
        )
        self.assertEqual(admin.role, User.Role.ADMIN)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_compatibility_properties(self):
        """Test des propriétés de compatibilité."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            entreprise='Test Corp',
            fonction='Manager'
        )
        # Test des getters
        self.assertEqual(user.company, 'Test Corp')
        self.assertEqual(user.function, 'Manager')
        self.assertTrue(user.is_active)
        
        # Test des setters
        user.company = 'New Corp'
        user.function = 'Director'
        user.is_active = False
        
        self.assertEqual(user.entreprise, 'New Corp')
        self.assertEqual(user.fonction, 'Director')
        self.assertFalse(user.est_actif)


class AuthenticationAPITest(APITestCase):
    """Tests pour les APIs d'authentification."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.login_url = reverse('accounts:token_obtain_pair')
        self.refresh_url = reverse('accounts:token_refresh')
        self.logout_url = reverse('accounts:logout')
    
    def test_login_success(self):
        """Test de connexion réussie."""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Vérifier que le journal de connexion est créé
        self.assertTrue(
            JournalConnexion.objects.filter(
                utilisateur=self.user,
                succes_connexion=True
            ).exists()
        )
    
    def test_login_invalid_credentials(self):
        """Test de connexion avec des identifiants invalides."""
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_success(self):
        """Test de déconnexion réussie."""
        # D'abord se connecter
        refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)
        
        data = {
            'refresh': str(refresh)
        }
        response = self.client.post(self.logout_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UserManagementAPITest(APITestCase):
    """Tests pour les APIs de gestion des utilisateurs."""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            role=User.Role.ADMIN
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='userpass123',
            role=User.Role.VIEWER
        )
        self.client = APIClient()
    
    def test_admin_can_list_all_users(self):
        """Test qu'un admin peut lister tous les utilisateurs."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('accounts:user-management-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # admin + regular user
    
    def test_regular_user_can_only_see_self(self):
        """Test qu'un utilisateur régulier ne peut voir que lui-même."""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('accounts:user-management-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['email'], self.regular_user.email)
    
    def test_admin_can_change_user_role(self):
        """Test qu'un admin peut changer le rôle d'un utilisateur."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('accounts:user-management-change-role', kwargs={'pk': self.regular_user.pk})
        data = {'role': User.Role.MANAGER}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.regular_user.refresh_from_db()
        self.assertEqual(self.regular_user.role, User.Role.MANAGER)


class FournisseurServiceTest(TestCase):
    """Tests pour le modèle FournisseurService."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='provider@example.com',
            username='provider',
            password='providerpass123'
        )
    
    def test_create_fournisseur_service(self):
        """Test de création d'un fournisseur de service."""
        from datetime import date, timedelta
        
        fournisseur = FournisseurService.objects.create(
            utilisateur=self.user,
            type_service='Maintenance',
            numero_contrat='CONT-001',
            date_validite=date.today() + timedelta(days=365),
            entreprise='Service Corp',
            specialites='Électricité, Plomberie'
        )
        
        self.assertEqual(fournisseur.utilisateur, self.user)
        self.assertEqual(fournisseur.type_service, 'Maintenance')
        self.assertTrue(fournisseur.est_valide)
    
    def test_fournisseur_service_expired(self):
        """Test qu'un contrat expiré est détecté."""
        from datetime import date, timedelta
        
        fournisseur = FournisseurService.objects.create(
            utilisateur=self.user,
            type_service='Maintenance',
            numero_contrat='CONT-002',
            date_validite=date.today() - timedelta(days=1),  # Expiré hier
            entreprise='Service Corp'
        )
        
        self.assertFalse(fournisseur.est_valide)


class ProfilUtilisateurTest(TestCase):
    """Tests pour le modèle ProfilUtilisateur."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            username='profile',
            password='profilepass123'
        )
    
    def test_create_profil_utilisateur(self):
        """Test de création d'un profil utilisateur."""
        profil = ProfilUtilisateur.objects.create(
            utilisateur=self.user,
            biographie='Développeur expérimenté',
            experience_annees=5,
            ville='Paris',
            pays='France',
            langue_preferee='fr'
        )
        
        self.assertEqual(profil.utilisateur, self.user)
        self.assertEqual(profil.experience_annees, 5)
        self.assertEqual(profil.langue_preferee, 'fr')


class JWTTokenTrackingTest(TestCase):
    """Tests pour le suivi des tokens JWT."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='token@example.com',
            username='token',
            password='tokenpass123'
        )
    
    def test_create_token_jwt(self):
        """Test de création d'un token JWT."""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        token = TokenJWT.objects.create(
            utilisateur=self.user,
            jti='unique-jti-123',
            type_token='ACCESS',
            date_expiration=timezone.now() + timedelta(hours=1),
            adresse_ip='192.168.1.1'
        )
        
        self.assertEqual(token.utilisateur, self.user)
        self.assertEqual(token.type_token, 'ACCESS')
        self.assertFalse(token.est_sur_liste_noire)
        self.assertFalse(token.est_expire)
    
    def test_token_blacklist(self):
        """Test de mise sur liste noire d'un token."""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        token = TokenJWT.objects.create(
            utilisateur=self.user,
            jti='blacklist-jti-123',
            type_token='REFRESH',
            date_expiration=timezone.now() + timedelta(days=7),
            adresse_ip='192.168.1.1'
        )
        
        token.mettre_sur_liste_noire()
        
        self.assertTrue(token.est_sur_liste_noire)
        self.assertIsNotNone(token.date_mise_liste_noire)
