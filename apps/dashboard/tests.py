from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from apps.wells.models import Well
from .models import (
    VisualisationPuits,
    IndicateurClePerformance,
    TableauBordExecutif,
    AlerteTableauBord,
    RapportPerformanceDetaille
)

User = get_user_model()


class VisualisationPuitsTestCase(TestCase):
    """Tests pour le modèle VisualisationPuits."""
    
    def setUp(self):
        self.well = Well.objects.create(
            nom="Puits Test",
            latitude=36.7538,
            longitude=3.0588
        )
        self.visualisation = VisualisationPuits.objects.create(
            puits=self.well,
            efficacite_globale=75.5,
            nombre_incidents_actifs=2,
            nombre_alertes_non_lues=3
        )
    
    def test_creation_visualisation(self):
        """Test la création d'une visualisation."""
        self.assertEqual(self.visualisation.puits, self.well)
        self.assertEqual(self.visualisation.efficacite_globale, 75.5)
        self.assertEqual(self.visualisation.statut_visuel, VisualisationPuits.StatutVisuel.ACTIF)
    
    def test_nom_puits_property(self):
        """Test la propriété nom_puits."""
        self.assertEqual(self.visualisation.nom_puits, "Puits Test")
    
    def test_est_critique_property(self):
        """Test la propriété est_critique."""
        self.visualisation.statut_visuel = VisualisationPuits.StatutVisuel.CRITIQUE
        self.assertTrue(self.visualisation.est_critique)
        
        self.visualisation.statut_visuel = VisualisationPuits.StatutVisuel.ACTIF
        self.assertFalse(self.visualisation.est_critique)
    
    def test_mettre_a_jour_statut(self):
        """Test la mise à jour automatique du statut."""
        # Cas avec incidents actifs
        self.visualisation.nombre_incidents_actifs = 1
        self.visualisation.mettre_a_jour_statut()
        self.assertEqual(self.visualisation.statut_visuel, VisualisationPuits.StatutVisuel.CRITIQUE)
        self.assertEqual(self.visualisation.code_couleur, VisualisationPuits.CodeCouleur.ROUGE)
        
        # Cas avec trop d'alertes
        self.visualisation.nombre_incidents_actifs = 0
        self.visualisation.nombre_alertes_non_lues = 6
        self.visualisation.mettre_a_jour_statut()
        self.assertEqual(self.visualisation.statut_visuel, VisualisationPuits.StatutVisuel.ALERTE)
        self.assertEqual(self.visualisation.code_couleur, VisualisationPuits.CodeCouleur.ORANGE)
        
        # Cas normal
        self.visualisation.nombre_alertes_non_lues = 2
        self.visualisation.efficacite_globale = 80
        self.visualisation.mettre_a_jour_statut()
        self.assertEqual(self.visualisation.statut_visuel, VisualisationPuits.StatutVisuel.ACTIF)
        self.assertEqual(self.visualisation.code_couleur, VisualisationPuits.CodeCouleur.VERT)


class IndicateurClePerformanceTestCase(TestCase):
    """Tests pour le modèle IndicateurClePerformance."""
    
    def setUp(self):
        self.well = Well.objects.create(
            nom="Puits Test KPI",
            latitude=36.7538,
            longitude=3.0588
        )
        self.indicateur = IndicateurClePerformance.objects.create(
            puits=self.well,
            nom_indicateur="Efficacité Forage",
            type_indicateur=IndicateurClePerformance.TypeIndicateur.OPERATIONNEL,
            unite_mesure="pourcentage",
            variance_cout=Decimal('1000.50'),
            variance_temps=Decimal('2.5'),
            taux_forage_moyen=Decimal('15.7'),
            efficacite_operationnelle=85.0,
            disponibilite_equipement=90.0,
            taux_reussite_operations=95.0,
            indice_securite=8.5,
            seuil_alerte=Decimal('75.0'),
            periode_debut=date.today() - timedelta(days=30),
            periode_fin=date.today()
        )
    
    def test_creation_indicateur(self):
        """Test la création d'un indicateur."""
        self.assertEqual(self.indicateur.nom_indicateur, "Efficacité Forage")
        self.assertEqual(self.indicateur.type_indicateur, "OPERATIONNEL")
        self.assertEqual(self.indicateur.variance_cout, Decimal('1000.50'))
    
    def test_performance_globale_property(self):
        """Test le calcul de la performance globale."""
        performance = self.indicateur.performance_globale
        # (85 + 90 + 95 + 85) / 4 = 88.75
        self.assertAlmostEqual(float(performance), 88.75, places=2)
    
    def test_est_dans_seuils(self):
        """Test la vérification des seuils."""
        # Performance > seuil
        self.assertTrue(self.indicateur.est_dans_seuils())
        
        # Performance < seuil
        self.indicateur.efficacite_operationnelle = 50.0
        self.indicateur.disponibilite_equipement = 50.0
        self.assertFalse(self.indicateur.est_dans_seuils())


class AlerteTableauBordTestCase(TestCase):
    """Tests pour le modèle AlerteTableauBord."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.well = Well.objects.create(
            nom="Puits Alerte",
            latitude=36.7538,
            longitude=3.0588
        )
        self.alerte = AlerteTableauBord.objects.create(
            puits=self.well,
            type_alerte=AlerteTableauBord.TypeAlerte.COUT_DEPASSE,
            niveau_alerte=AlerteTableauBord.NiveauAlerte.CRITIQUE,
            titre_alerte="Dépassement Budget",
            description_detaillee="Le coût du projet dépasse le budget alloué de 15%",
            valeur_seuil_defini=Decimal('100000.00'),
            valeur_actuelle_mesuree=Decimal('115000.00')
        )
    
    def test_creation_alerte(self):
        """Test la création d'une alerte."""
        self.assertEqual(self.alerte.titre_alerte, "Dépassement Budget")
        self.assertEqual(self.alerte.niveau_alerte, "CRITIQUE")
        self.assertTrue(self.alerte.est_active)
        self.assertFalse(self.alerte.est_accusee_reception)
    
    def test_est_critique_ou_urgente_property(self):
        """Test la propriété est_critique_ou_urgente."""
        self.assertTrue(self.alerte.est_critique_ou_urgente)
        
        self.alerte.niveau_alerte = AlerteTableauBord.NiveauAlerte.INFO
        self.assertFalse(self.alerte.est_critique_ou_urgente)
    
    def test_accuser_reception(self):
        """Test l'accusé de réception d'une alerte."""
        self.alerte.accuser_reception(self.user)
        
        self.assertTrue(self.alerte.est_accusee_reception)
        self.assertEqual(self.alerte.accusee_par, self.user)
        self.assertEqual(self.alerte.statut_alerte, AlerteTableauBord.StatutAlerte.ACCUSEE)
        self.assertIsNotNone(self.alerte.date_accusation)
    
    def test_commencer_traitement(self):
        """Test le début de traitement d'une alerte."""
        self.alerte.commencer_traitement(self.user)
        
        self.assertEqual(self.alerte.traitee_par, self.user)
        self.assertEqual(self.alerte.statut_alerte, AlerteTableauBord.StatutAlerte.EN_COURS)
        self.assertIsNotNone(self.alerte.date_debut_traitement)
    
    def test_resoudre_alerte(self):
        """Test la résolution d'une alerte."""
        self.alerte.resoudre_alerte()
        
        self.assertFalse(self.alerte.est_active)
        self.assertEqual(self.alerte.statut_alerte, AlerteTableauBord.StatutAlerte.RESOLUE)
        self.assertIsNotNone(self.alerte.date_resolution)


class TableauBordExecutifTestCase(TestCase):
    """Tests pour le modèle TableauBordExecutif."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpass123"
        )
        self.tableau = TableauBordExecutif.objects.create(
            nom_tableau="Dashboard Q1 2024",
            type_tableau=TableauBordExecutif.TypeTableau.OPERATIONNEL,
            total_puits=50,
            puits_actifs=35,
            puits_termines=10,
            budget_total_alloue=Decimal('5000000.00'),
            cout_realise_cumule=Decimal('4500000.00'),
            variance_budgetaire=Decimal('500000.00'),
            periode_debut=date(2024, 1, 1),
            periode_fin=date(2024, 3, 31),
            cree_par=self.user
        )
    
    def test_creation_tableau_bord(self):
        """Test la création d'un tableau de bord."""
        self.assertEqual(self.tableau.nom_tableau, "Dashboard Q1 2024")
        self.assertEqual(self.tableau.total_puits, 50)
        self.assertEqual(self.tableau.cree_par, self.user)
        self.assertTrue(self.tableau.est_actif)
    
    def test_taux_completion_projets_property(self):
        """Test le calcul du taux de complétion."""
        taux = self.tableau.taux_completion_projets
        # 10 terminés / 50 total = 20%
        self.assertEqual(taux, 20.0)
    
    def test_performance_budgetaire_property(self):
        """Test le calcul de la performance budgétaire."""
        performance = self.tableau.performance_budgetaire
        # (5000000 - 500000) / 5000000 * 100 = 90%
        self.assertEqual(performance, 90.0)


class RapportPerformanceDetailleTestCase(TestCase):
    """Tests pour le modèle RapportPerformanceDetaille."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="reporter",
            email="reporter@example.com",
            password="reportpass123"
        )
        self.validateur = User.objects.create_user(
            username="validator",
            email="validator@example.com",
            password="validpass123"
        )
        self.rapport = RapportPerformanceDetaille.objects.create(
            nom_rapport="Rapport Mensuel Mars 2024",
            type_rapport=RapportPerformanceDetaille.TypeRapport.MENSUEL,
            periode_debut=date(2024, 3, 1),
            periode_fin=date(2024, 3, 31),
            donnees_rapport={"total_puits": 25, "cout_moyen": 150000},
            resume_executif="Analyse des performances du mois de mars",
            analyse_performance="Les performances sont en hausse de 5%",
            genere_par=self.user
        )
    
    def test_creation_rapport(self):
        """Test la création d'un rapport."""
        self.assertEqual(self.rapport.nom_rapport, "Rapport Mensuel Mars 2024")
        self.assertEqual(self.rapport.type_rapport, "MENSUEL")
        self.assertEqual(self.rapport.statut_rapport, "EN_PREPARATION")
        self.assertEqual(self.rapport.genere_par, self.user)
    
    def test_duree_periode_property(self):
        """Test le calcul de la durée de période."""
        duree = self.rapport.duree_periode
        # Mars 2024 a 31 jours, donc du 1er au 31 = 30 jours
        self.assertEqual(duree, 30)
    
    def test_est_recent_property(self):
        """Test la propriété est_recent."""
        # Le rapport vient d'être créé, il devrait être récent
        self.assertTrue(self.rapport.est_recent)
    
    def test_valider_rapport(self):
        """Test la validation d'un rapport."""
        # D'abord changer le statut à GENERE
        self.rapport.statut_rapport = RapportPerformanceDetaille.StatutRapport.GENERE
        self.rapport.save()
        
        self.rapport.valider_rapport(self.validateur)
        
        self.assertEqual(self.rapport.valide_par, self.validateur)
        self.assertEqual(self.rapport.statut_rapport, RapportPerformanceDetaille.StatutRapport.VALIDE)
        self.assertIsNotNone(self.rapport.date_validation)
    
    def test_publier_rapport(self):
        """Test la publication d'un rapport."""
        # Préparer le rapport pour publication
        self.rapport.statut_rapport = RapportPerformanceDetaille.StatutRapport.VALIDE
        self.rapport.save()
        
        self.rapport.publier_rapport()
        
        self.assertEqual(self.rapport.statut_rapport, RapportPerformanceDetaille.StatutRapport.PUBLIE)
        self.assertIsNotNone(self.rapport.date_publication)
