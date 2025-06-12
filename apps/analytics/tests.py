from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.utils import timezone

from apps.wells.models import Well, Phase, Operation
from .models import (
    JeuDonneesAnalytiques, AnalyseEcart, InteractionAssistantIA,
    IndicateurPerformance, AnalyseReservoir, TableauBordKPI,
    AnalysePredictive, AlerteAnalytique
)

User = get_user_model()


class JeuDonneesAnalytiquesTestCase(TestCase):
    """Tests pour le modèle JeuDonneesAnalytiques."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='analyste_test',
            email='analyste@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits Test Analytics',
            latitude=36.7539,
            longitude=3.0588
        )
    
    def test_creation_jeu_donnees_analytiques(self):
        """Test de création d'un jeu de données analytiques."""
        jeu_donnees = JeuDonneesAnalytiques.objects.create(
            puits=self.puits,
            type_donnees='PRODUCTION',
            nom_jeu_donnees='Données de production Q1 2024',
            donnees={'production_journaliere': [100, 120, 110, 95]},
            source_donnees='Système SCADA',
            cree_par=self.user
        )
        
        self.assertEqual(jeu_donnees.puits, self.puits)
        self.assertEqual(jeu_donnees.type_donnees, 'PRODUCTION')
        self.assertIn('production_journaliere', jeu_donnees.donnees)
        self.assertTrue(jeu_donnees.date_creation)
        self.assertTrue(jeu_donnees.date_modification)
    
    def test_str_representation(self):
        """Test de la représentation string du modèle."""
        jeu_donnees = JeuDonneesAnalytiques.objects.create(
            puits=self.puits,
            type_donnees='FORAGE',
            nom_jeu_donnees='Logs de forage',
            donnees={'profondeur': [0, 1000, 2000]},
            cree_par=self.user
        )
        
        expected_str = f"Logs de forage - {self.puits.nom}"
        self.assertEqual(str(jeu_donnees), expected_str)


class AnalyseEcartTestCase(TestCase):
    """Tests pour le modèle AnalyseEcart."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='analyste_ecart',
            email='ecart@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits Écart Test',
            latitude=36.7539,
            longitude=3.0588
        )
        self.phase = Phase.objects.create(
            puits=self.puits,
            numero_phase=1,
            nom='Phase Test Écart'
        )
    
    def test_calcul_automatique_ecart(self):
        """Test du calcul automatique de l'écart."""
        analyse = AnalyseEcart.objects.create(
            phase=self.phase,
            valeur_planifiee=Decimal('100.00'),
            valeur_reelle=Decimal('120.00'),
            type_indicateur='PRODUCTION',
            analyseur=self.user
        )
        
        self.assertEqual(analyse.ecart_absolu, Decimal('20.00'))
        self.assertEqual(analyse.pourcentage_ecart, Decimal('20.0000'))
        self.assertEqual(analyse.niveau_criticite, 'MOYEN')
    
    def test_niveau_criticite_automatique(self):
        """Test de la détermination automatique du niveau de criticité."""
        # Écart critique (>= 50%)
        analyse_critique = AnalyseEcart.objects.create(
            phase=self.phase,
            valeur_planifiee=Decimal('100.00'),
            valeur_reelle=Decimal('50.00'),
            type_indicateur='COUT',
            analyseur=self.user
        )
        self.assertEqual(analyse_critique.niveau_criticite, 'CRITIQUE')
        
        # Écart élevé (>= 25%)
        analyse_elevee = AnalyseEcart.objects.create(
            phase=self.phase,
            valeur_planifiee=Decimal('100.00'),
            valeur_reelle=Decimal('75.00'),
            type_indicateur='TEMPS',
            analyseur=self.user
        )
        self.assertEqual(analyse_elevee.niveau_criticite, 'ELEVE')
        
        # Écart faible (< 10%)
        analyse_faible = AnalyseEcart.objects.create(
            phase=self.phase,
            valeur_planifiee=Decimal('100.00'),
            valeur_reelle=Decimal('95.00'),
            type_indicateur='QUALITE',
            analyseur=self.user
        )
        self.assertEqual(analyse_faible.niveau_criticite, 'FAIBLE')


class InteractionAssistantIATestCase(TestCase):
    """Tests pour le modèle InteractionAssistantIA."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='utilisateur_ia',
            email='ia@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits IA Test',
            latitude=36.7539,
            longitude=3.0588
        )
    
    def test_creation_interaction_ia(self):
        """Test de création d'une interaction avec l'IA."""
        interaction = InteractionAssistantIA.objects.create(
            utilisateur=self.user,
            requete="Analysez la production du puits pour les 30 derniers jours",
            type_requete='ANALYSE',
            puits_associe=self.puits,
            score_pertinence=Decimal('0.95')
        )
        
        self.assertEqual(interaction.utilisateur, self.user)
        self.assertEqual(interaction.type_requete, 'ANALYSE')
        self.assertEqual(interaction.statut, 'EN_ATTENTE')
        self.assertTrue(interaction.horodatage_creation)
    
    def test_validation_score_pertinence(self):
        """Test de validation du score de pertinence."""
        # Score valide
        interaction_valide = InteractionAssistantIA(
            utilisateur=self.user,
            requete="Test requête",
            type_requete='ANALYSE',
            score_pertinence=Decimal('0.85')
        )
        interaction_valide.full_clean()  # Ne doit pas lever d'exception
        
        # Score invalide (> 1)
        interaction_invalide = InteractionAssistantIA(
            utilisateur=self.user,
            requete="Test requête",
            type_requete='ANALYSE',
            score_pertinence=Decimal('1.5')
        )
        with self.assertRaises(ValidationError):
            interaction_invalide.full_clean()


class IndicateurPerformanceTestCase(TestCase):
    """Tests pour le modèle IndicateurPerformance."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='mesureur_perf',
            email='perf@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits Performance Test',
            latitude=36.7539,
            longitude=3.0588
        )
        self.operation = Operation.objects.create(
            puits=self.puits,
            nom='Opération Test Performance'
        )
        # Create a dummy TypeIndicateur - adjust based on your wells app structure
        from apps.wells.models import TypeIndicateur
        self.type_indicateur = TypeIndicateur.objects.create(
            nom='Production',
            unite='m³/j'
        )
    
    def test_calcul_automatique_performance(self):
        """Test du calcul automatique des métriques de performance."""
        indicateur = IndicateurPerformance.objects.create(
            operation=self.operation,
            type_indicateur=self.type_indicateur,
            valeur_prevue=Decimal('1000.00'),
            valeur_reelle=Decimal('1200.00'),
            date_mesure=timezone.now(),
            mesure_par=self.user
        )
        
        self.assertEqual(indicateur.ecart_performance, Decimal('200.00'))
        self.assertEqual(indicateur.pourcentage_realisation, Decimal('120.00'))


class TableauBordKPITestCase(TestCase):
    """Tests pour le modèle TableauBordKPI."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='gestionnaire_kpi',
            email='kpi@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits KPI Test',
            latitude=36.7539,
            longitude=3.0588
        )
    
    def test_calcul_automatique_kpi(self):
        """Test du calcul automatique des KPIs."""
        kpi = TableauBordKPI.objects.create(
            puits=self.puits,
            nom_kpi='Production journalière',
            categorie_kpi='PRODUCTION',
            valeur_actuelle=Decimal('950.00'),
            valeur_precedente=Decimal('900.00'),
            unite_mesure='m³/j',
            objectif_cible=Decimal('1000.00'),
            periode_reference='Janvier 2024',
            calcule_par=self.user
        )
        
        self.assertEqual(kpi.pourcentage_atteinte, Decimal('95.00'))
        self.assertAlmostEqual(kpi.evolution_pourcentage, Decimal('5.56'), places=2)
        self.assertEqual(kpi.statut_kpi, 'SATISFAISANT')
    
    def test_determination_statut_automatique(self):
        """Test de la détermination automatique du statut KPI."""
        # KPI Excellent (>= 120%)
        kpi_excellent = TableauBordKPI.objects.create(
            puits=self.puits,
            nom_kpi='Test Excellent',
            categorie_kpi='PRODUCTION',
            valeur_actuelle=Decimal('1250.00'),
            unite_mesure='unité',
            objectif_cible=Decimal('1000.00'),
            periode_reference='Test',
            calcule_par=self.user
        )
        self.assertEqual(kpi_excellent.statut_kpi, 'EXCELLENT')
        
        # KPI Critique (< 50%)
        kpi_critique = TableauBordKPI.objects.create(
            puits=self.puits,
            nom_kpi='Test Critique',
            categorie_kpi='SECURITE',
            valeur_actuelle=Decimal('400.00'),
            unite_mesure='unité',
            objectif_cible=Decimal('1000.00'),
            periode_reference='Test',
            calcule_par=self.user
        )
        self.assertEqual(kpi_critique.statut_kpi, 'CRITIQUE')


class AnalysePredictiveTestCase(TestCase):
    """Tests pour le modèle AnalysePredictive."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='predicteur',
            email='prediction@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits Prédiction Test',
            latitude=36.7539,
            longitude=3.0588
        )
    
    def test_creation_analyse_predictive(self):
        """Test de création d'une analyse prédictive."""
        analyse = AnalysePredictive.objects.create(
            puits=self.puits,
            nom_analyse='Prédiction production Q2 2024',
            type_prediction='PRODUCTION',
            valeur_predite=Decimal('1500.00'),
            valeur_min_predite=Decimal('1300.00'),
            valeur_max_predite=Decimal('1700.00'),
            intervalle_confiance=Decimal('95.00'),
            date_prediction_pour=date(2024, 6, 30),
            horizon_prediction_jours=90,
            modele_utilise='Random Forest',
            parametres_modele={'n_estimators': 100, 'max_depth': 10},
            donnees_entree={'historique_production': [100, 120, 110]},
            cree_par=self.user
        )
        
        self.assertEqual(analyse.statut_prediction, 'EN_COURS')
        self.assertTrue(analyse.date_creation)
        self.assertEqual(analyse.type_prediction, 'PRODUCTION')
    
    def test_validation_intervalle_confiance(self):
        """Test de validation de l'intervalle de confiance."""
        # Intervalle valide
        analyse_valide = AnalysePredictive(
            puits=self.puits,
            nom_analyse='Test valide',
            type_prediction='PRODUCTION',
            valeur_predite=Decimal('1000.00'),
            intervalle_confiance=Decimal('95.00'),
            date_prediction_pour=date.today(),
            horizon_prediction_jours=30,
            modele_utilise='Test',
            parametres_modele={},
            donnees_entree={}
        )
        analyse_valide.full_clean()  # Ne doit pas lever d'exception
        
        # Intervalle invalide (> 100)
        analyse_invalide = AnalysePredictive(
            puits=self.puits,
            nom_analyse='Test invalide',
            type_prediction='PRODUCTION',
            valeur_predite=Decimal('1000.00'),
            intervalle_confiance=Decimal('150.00'),
            date_prediction_pour=date.today(),
            horizon_prediction_jours=30,
            modele_utilise='Test',
            parametres_modele={},
            donnees_entree={}
        )
        with self.assertRaises(ValidationError):
            analyse_invalide.full_clean()


class AlerteAnalytiqueTestCase(TestCase):
    """Tests pour le modèle AlerteAnalytique."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='gestionnaire_alerte',
            email='alerte@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits Alerte Test',
            latitude=36.7539,
            longitude=3.0588
        )
    
    def test_creation_alerte_analytique(self):
        """Test de création d'une alerte analytique."""
        alerte = AlerteAnalytique.objects.create(
            puits=self.puits,
            type_alerte='SEUIL_DEPASSE',
            niveau_urgence='URGENT',
            titre_alerte='Production en baisse critique',
            description='La production a chuté de 30% en 24h',
            valeur_declenchante=Decimal('700.00'),
            seuil_reference=Decimal('1000.00'),
            source_donnees='Capteurs production',
            assigne_a=self.user
        )
        
        self.assertEqual(alerte.statut_alerte, 'NOUVELLE')
        self.assertEqual(alerte.niveau_urgence, 'URGENT')
        self.assertTrue(alerte.date_declenchement)
        self.assertIsNone(alerte.date_resolution)
    
    def test_str_representation_alerte(self):
        """Test de la représentation string de l'alerte."""
        alerte = AlerteAnalytique.objects.create(
            puits=self.puits,
            type_alerte='ANOMALIE_DETECTEE',
            niveau_urgence='INFO',
            titre_alerte='Anomalie détectée',
            description='Test description',
            source_donnees='Test'
        )
        
        expected_str = f"Alerte Anomalie détectée - {self.puits.nom}"
        self.assertEqual(str(alerte), expected_str)


class AnalyticsIntegrationTestCase(TransactionTestCase):
    """Tests d'intégration pour l'app analytics."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integration_test',
            email='integration@test.com',
            password='motdepasse123'
        )
        self.puits = Well.objects.create(
            nom='Puits Intégration Test',
            latitude=36.7539,
            longitude=3.0588
        )
    
    def test_workflow_analyse_complete(self):
        """Test d'un workflow complet d'analyse."""
        # 1. Créer un jeu de données
        jeu_donnees = JeuDonneesAnalytiques.objects.create(
            puits=self.puits,
            type_donnees='PRODUCTION',
            nom_jeu_donnees='Données test workflow',
            donnees={'production': [100, 90, 80, 85]},
            cree_par=self.user
        )
        
        # 2. Créer une interaction IA
        interaction = InteractionAssistantIA.objects.create(
            utilisateur=self.user,
            requete="Analysez la tendance de production",
            type_requete='ANALYSE',
            puits_associe=self.puits
        )
        
        # 3. Créer une prédiction
        prediction = AnalysePredictive.objects.create(
            puits=self.puits,
            nom_analyse='Prédiction workflow',
            type_prediction='PRODUCTION',
            valeur_predite=Decimal('75.00'),
            intervalle_confiance=Decimal('90.00'),
            date_prediction_pour=date.today() + timedelta(days=30),
            horizon_prediction_jours=30,
            modele_utilise='Régression linéaire',
            parametres_modele={'slope': -2.5},
            donnees_entree=jeu_donnees.donnees,
            cree_par=self.user
        )
        
        # 4. Créer une alerte basée sur la prédiction
        alerte = AlerteAnalytique.objects.create(
            puits=self.puits,
            type_alerte='PREDICTION_CRITIQUE',
            niveau_urgence='ATTENTION',
            titre_alerte='Baisse de production prédite',
            description=f'Prédiction de production à {prediction.valeur_predite}',
            valeur_declenchante=prediction.valeur_predite,
            seuil_reference=Decimal('100.00'),
            source_donnees='Modèle prédictif'
        )
        
        # Vérifications
        self.assertTrue(JeuDonneesAnalytiques.objects.filter(puits=self.puits).exists())
        self.assertTrue(InteractionAssistantIA.objects.filter(utilisateur=self.user).exists())
        self.assertTrue(AnalysePredictive.objects.filter(puits=self.puits).exists())
        self.assertTrue(AlerteAnalytique.objects.filter(puits=self.puits).exists())
        
        # Vérifier les relations
        self.assertEqual(alerte.puits, jeu_donnees.puits)
        self.assertEqual(interaction.puits_associe, prediction.puits)
