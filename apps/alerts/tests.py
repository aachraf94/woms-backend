from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    Notification, Incident, RegleAlerte, JournalAction,
    TypeNotification, StatutIncident, TypeIncident
)

User = get_user_model()


class NotificationModelTest(TestCase):
    """Tests pour le modèle Notification"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_notification(self):
        """Test de création d'une notification"""
        notification = Notification.objects.create(
            type_notification=TypeNotification.ALERTE,
            titre='Test Alerte',
            message='Message de test',
            destinataire=self.user
        )
        self.assertEqual(notification.titre, 'Test Alerte')
        self.assertEqual(notification.destinataire, self.user)
        self.assertFalse(notification.lu)
        self.assertIsNone(notification.date_lecture)
    
    def test_notification_str(self):
        """Test de la représentation string d'une notification"""
        notification = Notification.objects.create(
            titre='Test',
            message='Message',
            destinataire=self.user
        )
        expected = f"Test - {self.user.username}"
        self.assertEqual(str(notification), expected)


class IncidentModelTest(TestCase):
    """Tests pour le modèle Incident"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='reporter',
            email='reporter@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='assignee',
            email='assignee@example.com',
            password='pass123'
        )
    
    def test_create_incident(self):
        """Test de création d'un incident"""
        incident = Incident.objects.create(
            titre='Panne serveur',
            type_incident=TypeIncident.PANNE_EQUIPEMENT,
            description='Le serveur principal ne répond plus',
            rapporte_par=self.user1,
            priorite=3
        )
        self.assertEqual(incident.titre, 'Panne serveur')
        self.assertEqual(incident.statut, StatutIncident.NOUVEAU)
        self.assertEqual(incident.priorite, 3)
        self.assertEqual(incident.rapporte_par, self.user1)
    
    def test_incident_assignment(self):
        """Test d'assignation d'un incident"""
        incident = Incident.objects.create(
            titre='Bug critique',
            type_incident=TypeIncident.AUTRE,
            description='Bug dans l\'application',
            rapporte_par=self.user1,
            assigne_a=self.user2
        )
        self.assertEqual(incident.assigne_a, self.user2)
    
    def test_incident_str(self):
        """Test de la représentation string d'un incident"""
        incident = Incident.objects.create(
            titre='Test Incident',
            type_incident=TypeIncident.AUTRE,
            description='Description test',
            rapporte_par=self.user1
        )
        expected = f"Test Incident - {incident.get_statut_display()}"
        self.assertEqual(str(incident), expected)


class RegleAlerteModelTest(TestCase):
    """Tests pour le modèle RegleAlerte"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
    
    def test_create_regle_alerte(self):
        """Test de création d'une règle d'alerte"""
        regle = RegleAlerte.objects.create(
            nom='Alerte température',
            description='Alerte si température > 40°C',
            condition='temperature > 40',
            action='send_notification',
            seuil_declenchement=40.0,
            type_capteur='temperature',
            creee_par=self.user
        )
        self.assertEqual(regle.nom, 'Alerte température')
        self.assertTrue(regle.active)
        self.assertEqual(regle.seuil_declenchement, 40.0)
        self.assertEqual(regle.creee_par, self.user)
    
    def test_regle_alerte_str(self):
        """Test de la représentation string d'une règle d'alerte"""
        regle = RegleAlerte.objects.create(
            nom='Test Règle',
            condition='test condition',
            action='test action',
            creee_par=self.user
        )
        self.assertEqual(str(regle), 'Test Règle')


class JournalActionModelTest(TestCase):
    """Tests pour le modèle JournalAction"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='actionuser',
            email='action@example.com',
            password='actionpass123'
        )
        self.incident = Incident.objects.create(
            titre='Incident test',
            type_incident=TypeIncident.AUTRE,
            description='Description incident test',
            rapporte_par=self.user
        )
    
    def test_create_journal_action(self):
        """Test de création d'une entrée de journal d'action"""
        action = JournalAction.objects.create(
            action='Création incident',
            details='Incident créé via interface web',
            adresse_ip='192.168.1.100',
            user_agent='Mozilla/5.0...',
            utilisateur=self.user,
            incident_lie=self.incident
        )
        self.assertEqual(action.action, 'Création incident')
        self.assertEqual(action.utilisateur, self.user)
        self.assertEqual(action.incident_lie, self.incident)
        self.assertEqual(action.adresse_ip, '192.168.1.100')
    
    def test_journal_action_without_incident(self):
        """Test de création d'une action sans incident lié"""
        action = JournalAction.objects.create(
            action='Connexion utilisateur',
            utilisateur=self.user
        )
        self.assertEqual(action.action, 'Connexion utilisateur')
        self.assertIsNone(action.incident_lie)
    
    def test_journal_action_str(self):
        """Test de la représentation string d'une action"""
        action = JournalAction.objects.create(
            action='Test Action',
            utilisateur=self.user
        )
        expected = f"Test Action - {self.user.username} - {action.horodatage}"
        self.assertEqual(str(action), expected)


class ModelChoicesTest(TestCase):
    """Tests pour les choix des modèles"""
    
    def test_type_notification_choices(self):
        """Test des choix de type de notification"""
        choices = [choice[0] for choice in TypeNotification.choices]
        expected = ['info', 'alerte', 'urgence', 'maintenance']
        self.assertEqual(choices, expected)
    
    def test_statut_incident_choices(self):
        """Test des choix de statut d'incident"""
        choices = [choice[0] for choice in StatutIncident.choices]
        expected = ['nouveau', 'en_cours', 'resolu', 'ferme']
        self.assertEqual(choices, expected)
    
    def test_type_incident_choices(self):
        """Test des choix de type d'incident"""
        choices = [choice[0] for choice in TypeIncident.choices]
        expected = [
            'panne_equipement', 'probleme_reseau', 
            'defaillance_capteur', 'maintenance_urgente', 'autre'
        ]
        self.assertEqual(choices, expected)


class ModelRelationshipTest(TestCase):
    """Tests pour les relations entre modèles"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
    
    def test_user_notifications_relationship(self):
        """Test de la relation utilisateur-notifications"""
        notification = Notification.objects.create(
            titre='Test',
            message='Message test',
            destinataire=self.user1
        )
        self.assertIn(notification, self.user1.notifications_recues.all())
    
    def test_user_incidents_relationship(self):
        """Test de la relation utilisateur-incidents"""
        incident = Incident.objects.create(
            titre='Test Incident',
            type_incident=TypeIncident.AUTRE,
            description='Description',
            rapporte_par=self.user1,
            assigne_a=self.user2
        )
        self.assertIn(incident, self.user1.incidents_rapportes.all())
        self.assertIn(incident, self.user2.incidents_assignes.all())
    
    def test_cascade_deletion(self):
        """Test de suppression en cascade"""
        incident = Incident.objects.create(
            titre='Test',
            type_incident=TypeIncident.AUTRE,
            description='Description',
            rapporte_par=self.user1
        )
        action = JournalAction.objects.create(
            action='Test action',
            utilisateur=self.user1,
            incident_lie=incident
        )
        
        # Supprimer l'incident, l'action doit être mise à jour
        incident.delete()
        action.refresh_from_db()
        self.assertIsNone(action.incident_lie)
