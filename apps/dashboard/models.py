from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from apps.wells.models import Well


class VisualisationPuits(models.Model):
    """Modèle pour la visualisation des puits avec indicateurs visuels."""
    
    class StatutVisuel(models.TextChoices):
        ACTIF = 'ACTIF', _('Actif')
        INACTIF = 'INACTIF', _('Inactif') 
        EN_COURS = 'EN_COURS', _('En cours')
        ALERTE = 'ALERTE', _('Alerte')
        CRITIQUE = 'CRITIQUE', _('Critique')
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
    
    class CodeCouleur(models.TextChoices):
        VERT = 'VERT', _('Vert - Normal')
        ORANGE = 'ORANGE', _('Orange - Attention')
        ROUGE = 'ROUGE', _('Rouge - Critique')
        BLEU = 'BLEU', _('Bleu - Information')
        GRIS = 'GRIS', _('Gris - Inactif')
    
    # Relations
    puits = models.OneToOneField(
        Well, 
        on_delete=models.CASCADE, 
        verbose_name=_('Puits'),
        related_name='visualisation'
    )
    
    # Indicateurs visuels
    code_couleur = models.CharField(
        max_length=20, 
        choices=CodeCouleur.choices,
        default=CodeCouleur.VERT,
        verbose_name=_('Code couleur')
    )
    statut_visuel = models.CharField(
        max_length=20, 
        choices=StatutVisuel.choices, 
        default=StatutVisuel.ACTIF, 
        verbose_name=_('Statut visuel')
    )
    icone_statut = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name=_('Icône de statut')
    )
    
    # Métriques de base
    taux_progression = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Taux de progression (%)')
    )
    efficacite_globale = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Efficacité globale (%)')
    )
    cout_total_realise = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0,
        verbose_name=_('Coût total réalisé (DZD)')
    )
    
    # Compteurs pour le tableau de bord
    nombre_incidents_actifs = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Nombre d\'incidents actifs')
    )
    nombre_alertes_non_lues = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre d\'alertes non lues')
    )
    jours_depuis_derniere_activite = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Jours depuis dernière activité')
    )
    
    # Audit
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, 
        verbose_name=_('Dernière mise à jour')
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    @property
    def nom_puits(self):
        """Retourne le nom du puits."""
        return getattr(self.puits, 'nom', None) or getattr(self.puits, 'name', 'Puits sans nom')
    
    @property
    def est_critique(self):
        """Vérifie si le puits est en état critique."""
        return self.statut_visuel in [self.StatutVisuel.CRITIQUE, self.StatutVisuel.ALERTE]
    
    def mettre_a_jour_statut(self):
        """Met à jour le statut visuel basé sur les métriques."""
        if self.nombre_incidents_actifs > 0:
            self.statut_visuel = self.StatutVisuel.CRITIQUE
            self.code_couleur = self.CodeCouleur.ROUGE
        elif self.nombre_alertes_non_lues > 5:
            self.statut_visuel = self.StatutVisuel.ALERTE
            self.code_couleur = self.CodeCouleur.ORANGE
        elif self.efficacite_globale < 50:
            self.statut_visuel = self.StatutVisuel.ALERTE
            self.code_couleur = self.CodeCouleur.ORANGE
        else:
            self.statut_visuel = self.StatutVisuel.ACTIF
            self.code_couleur = self.CodeCouleur.VERT
        self.save()
    
    def __str__(self):
        return f"Visualisation - {self.nom_puits}"
    
    class Meta:
        verbose_name = _('Visualisation de puits')
        verbose_name_plural = _('Visualisations de puits')
        ordering = ['-derniere_mise_a_jour']


class IndicateurClePerformance(models.Model):
    """Modèle pour les indicateurs clés de performance (KPI)."""
    
    class TypeIndicateur(models.TextChoices):
        FINANCIER = 'FINANCIER', _('Financier')
        OPERATIONNEL = 'OPERATIONNEL', _('Opérationnel')
        SECURITE = 'SECURITE', _('Sécurité')
        QUALITE = 'QUALITE', _('Qualité')
        ENVIRONNEMENT = 'ENVIRONNEMENT', _('Environnement')
        TEMPS = 'TEMPS', _('Temps')
    
    # Relations
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE, 
        verbose_name=_('Puits'),
        related_name='indicateurs_performance'
    )
    
    # Identification
    nom_indicateur = models.CharField(
        max_length=100, 
        verbose_name=_('Nom de l\'indicateur')
    )
    type_indicateur = models.CharField(
        max_length=20,
        choices=TypeIndicateur.choices,
        verbose_name=_('Type d\'indicateur')
    )
    unite_mesure = models.CharField(
        max_length=20,
        verbose_name=_('Unité de mesure')
    )
    
    # Variances principales
    variance_cout = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name=_('Variance de coût (DZD)')
    )
    variance_temps = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_('Variance de temps (jours)')
    )
    taux_forage_moyen = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name=_('Taux de forage moyen (m/h)')
    )
    
    # Métriques de performance avancées
    efficacite_operationnelle = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Efficacité opérationnelle (%)')
    )
    disponibilite_equipement = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Disponibilité équipement (%)')
    )
    taux_reussite_operations = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Taux de réussite des opérations (%)')
    )
    indice_securite = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_('Indice de sécurité (/10)')
    )
    
    # Seuils et cibles
    valeur_cible = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Valeur cible')
    )
    seuil_alerte = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Seuil d\'alerte')
    )
    
    # Audit et dates
    date_calcul = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de calcul')
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, 
        verbose_name=_('Dernière mise à jour')
    )
    periode_debut = models.DateField(
        verbose_name=_('Début de période')
    )
    periode_fin = models.DateField(
        verbose_name=_('Fin de période')
    )
    
    @property
    def nom_puits(self):
        """Retourne le nom du puits."""
        return getattr(self.puits, 'nom', None) or getattr(self.puits, 'name', 'Puits sans nom')
    
    @property
    def performance_globale(self):
        """Calcule un score de performance global."""
        scores = [
            self.efficacite_operationnelle,
            self.disponibilite_equipement,
            self.taux_reussite_operations,
            self.indice_securite * 10  # Normaliser sur 100
        ]
        return sum(scores) / len(scores) if scores else 0
    
    def est_dans_seuils(self):
        """Vérifie si l'indicateur respecte les seuils."""
        if self.seuil_alerte is None:
            return True
        return self.performance_globale >= self.seuil_alerte
    
    def __str__(self):
        return f"{self.nom_indicateur} - {self.nom_puits}"
    
    class Meta:
        verbose_name = _('Indicateur clé de performance')
        verbose_name_plural = _('Indicateurs clés de performance')
        ordering = ['-date_calcul']
        unique_together = ['puits', 'nom_indicateur', 'periode_debut']


class TableauBordExecutif(models.Model):
    """Modèle pour le tableau de bord exécutif avec métriques de synthèse."""
    
    class TypeTableau(models.TextChoices):
        OPERATIONNEL = 'OPERATIONNEL', _('Opérationnel')
        FINANCIER = 'FINANCIER', _('Financier')
        STRATEGIQUE = 'STRATEGIQUE', _('Stratégique')
        SECURITE = 'SECURITE', _('Sécurité')
        QUALITE = 'QUALITE', _('Qualité')
    
    # Identification
    nom_tableau = models.CharField(
        max_length=100, 
        verbose_name=_('Nom du tableau de bord')
    )
    type_tableau = models.CharField(
        max_length=20,
        choices=TypeTableau.choices,
        default=TypeTableau.OPERATIONNEL,
        verbose_name=_('Type de tableau')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    
    # Métriques globales des puits
    total_puits = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Total des puits')
    )
    puits_actifs = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Puits actifs')
    )
    puits_termines = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Puits terminés')
    )
    puits_en_cours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Puits en cours')
    )
    puits_en_maintenance = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Puits en maintenance')
    )
    
    # Métriques financières détaillées
    budget_total_alloue = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name=_('Budget total alloué (DZD)')
    )
    cout_realise_cumule = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name=_('Coût réalisé cumulé (DZD)')
    )
    variance_budgetaire = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name=_('Variance budgétaire (DZD)')
    )
    taux_consommation_budget = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Taux de consommation budget (%)')
    )
    
    # Métriques temporelles
    delai_moyen_completion = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0, 
        verbose_name=_('Délai moyen de complétion (jours)')
    )
    projets_en_retard = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Projets en retard')
    )
    projets_en_avance = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Projets en avance')
    )
    taux_respect_delais = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Taux de respect des délais (%)')
    )
    
    # Métriques de qualité et sécurité
    nombre_incidents_total = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Nombre total d\'incidents')
    )
    taux_incidents = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_('Taux d\'incidents (par 1000h)')
    )
    score_securite_global = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name=_('Score de sécurité global (/10)')
    )
    taux_conformite_qualite = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Taux de conformité qualité (%)')
    )
    
    # Période de référence
    periode_debut = models.DateField(
        verbose_name=_('Début de période')
    )
    periode_fin = models.DateField(
        verbose_name=_('Fin de période')
    )
    
    # Audit et gestion
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de création')
    )
    derniere_mise_a_jour = models.DateTimeField(
        auto_now=True, 
        verbose_name=_('Dernière mise à jour')
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        verbose_name=_('Créé par')
    )
    est_actif = models.BooleanField(
        default=True,
        verbose_name=_('Est actif')
    )
    
    @property
    def taux_completion_projets(self):
        """Calcule le taux de complétion des projets."""
        if self.total_puits == 0:
            return 0
        return (self.puits_termines / self.total_puits) * 100
    
    @property
    def performance_budgetaire(self):
        """Évalue la performance budgétaire."""
        if self.budget_total_alloue == 0:
            return 0
        return ((self.budget_total_alloue - abs(self.variance_budgetaire)) / self.budget_total_alloue) * 100
    
    def calculer_metriques_globales(self):
        """Recalcule toutes les métriques du tableau de bord."""
        from django.db.models import Count, Sum, Avg
        # Cette méthode devrait être implémentée pour recalculer les métriques
        # basées sur les données actuelles des puits
        pass
    
    def __str__(self):
        return f"Tableau de bord - {self.nom_tableau} ({self.type_tableau})"
    
    class Meta:
        verbose_name = _('Tableau de bord exécutif')
        verbose_name_plural = _('Tableaux de bord exécutifs')
        ordering = ['-derniere_mise_a_jour']


class AlerteTableauBord(models.Model):
    """Modèle pour les alertes du tableau de bord."""
    
    class TypeAlerte(models.TextChoices):
        COUT_DEPASSE = 'COUT_DEPASSE', _('Coût dépassé')
        DELAI_RETARD = 'DELAI_RETARD', _('Délai en retard')
        SECURITE_INCIDENT = 'SECURITE_INCIDENT', _('Incident de sécurité')
        PERFORMANCE_FAIBLE = 'PERFORMANCE_FAIBLE', _('Performance faible')
        MAINTENANCE_REQUISE = 'MAINTENANCE_REQUISE', _('Maintenance requise')
        EQUIPEMENT_PANNE = 'EQUIPEMENT_PANNE', _('Panne d\'équipement')
        QUALITE_NON_CONFORME = 'QUALITE_NON_CONFORME', _('Qualité non conforme')
    
    class NiveauAlerte(models.TextChoices):
        INFO = 'INFO', _('Information')
        ATTENTION = 'ATTENTION', _('Attention')
        IMPORTANT = 'IMPORTANT', _('Important')
        CRITIQUE = 'CRITIQUE', _('Critique')
        URGENCE = 'URGENCE', _('Urgence')
    
    class StatutAlerte(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        ACCUSEE = 'ACCUSEE', _('Accusée de réception')
        EN_COURS = 'EN_COURS', _('En cours de traitement')
        RESOLUE = 'RESOLUE', _('Résolue')
        FERMEE = 'FERMEE', _('Fermée')
    
    # Relations
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE, 
        verbose_name=_('Puits'),
        related_name='alertes_tableau_bord'
    )
    
    # Classification de l'alerte
    type_alerte = models.CharField(
        max_length=25, 
        choices=TypeAlerte.choices, 
        verbose_name=_('Type d\'alerte')
    )
    niveau_alerte = models.CharField(
        max_length=20, 
        choices=NiveauAlerte.choices, 
        verbose_name=_('Niveau d\'alerte')
    )
    statut_alerte = models.CharField(
        max_length=20,
        choices=StatutAlerte.choices,
        default=StatutAlerte.ACTIVE,
        verbose_name=_('Statut de l\'alerte')
    )
    
    # Contenu de l'alerte
    titre_alerte = models.CharField(
        max_length=200, 
        verbose_name=_('Titre de l\'alerte')
    )
    description_detaillee = models.TextField(
        verbose_name=_('Description détaillée')
    )
    actions_recommandees = models.TextField(
        blank=True,
        verbose_name=_('Actions recommandées')
    )
    
    # Valeurs et seuils
    valeur_seuil_defini = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Valeur seuil défini')
    )
    valeur_actuelle_mesuree = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Valeur actuelle mesurée')
    )
    unite_valeur = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Unité de valeur')
    )
    
    # Gestion et traitement
    est_active = models.BooleanField(
        default=True, 
        verbose_name=_('Est active')
    )
    est_accusee_reception = models.BooleanField(
        default=False, 
        verbose_name=_('Accusé de réception')
    )
    accusee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='alertes_accusees',
        verbose_name=_('Accusée par')
    )
    traitee_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_traitees',
        verbose_name=_('Traitée par')
    )
    
    # Dates importantes
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de création')
    )
    date_accusation = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_('Date d\'accusation')
    )
    date_debut_traitement = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date début traitement')
    )
    date_resolution = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_('Date de résolution')
    )
    date_fermeture = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de fermeture')
    )
    
    @property
    def nom_puits(self):
        """Retourne le nom du puits."""
        return getattr(self.puits, 'nom', None) or getattr(self.puits, 'name', 'Puits sans nom')
    
    @property
    def duree_ouverture(self):
        """Calcule la durée d'ouverture de l'alerte."""
        from django.utils import timezone
        fin = self.date_resolution or timezone.now()
        return (fin - self.date_creation).days
    
    @property
    def est_critique_ou_urgente(self):
        """Vérifie si l'alerte est critique ou urgente."""
        return self.niveau_alerte in [self.NiveauAlerte.CRITIQUE, self.NiveauAlerte.URGENCE]
    
    def accuser_reception(self, utilisateur):
        """Marque l'alerte comme accusée de réception."""
        from django.utils import timezone
        self.est_accusee_reception = True
        self.accusee_par = utilisateur
        self.date_accusation = timezone.now()
        if self.statut_alerte == self.StatutAlerte.ACTIVE:
            self.statut_alerte = self.StatutAlerte.ACCUSEE
        self.save()
    
    def commencer_traitement(self, utilisateur):
        """Commence le traitement de l'alerte."""
        from django.utils import timezone
        self.traitee_par = utilisateur
        self.date_debut_traitement = timezone.now()
        self.statut_alerte = self.StatutAlerte.EN_COURS
        self.save()
    
    def resoudre_alerte(self):
        """Marque l'alerte comme résolue."""
        from django.utils import timezone
        self.date_resolution = timezone.now()
        self.statut_alerte = self.StatutAlerte.RESOLUE
        self.est_active = False
        self.save()
    
    def __str__(self):
        return f"Alerte {self.get_niveau_alerte_display()} - {self.titre_alerte}"
    
    class Meta:
        verbose_name = _('Alerte de tableau de bord')
        verbose_name_plural = _('Alertes de tableau de bord')
        ordering = ['-date_creation', 'niveau_alerte']
        indexes = [
            models.Index(fields=['niveau_alerte', 'est_active']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['puits', 'type_alerte']),
        ]


class RapportPerformanceDetaille(models.Model):
    """Modèle pour les rapports de performance détaillés."""
    
    class TypeRapport(models.TextChoices):
        HEBDOMADAIRE = 'HEBDOMADAIRE', _('Hebdomadaire')
        MENSUEL = 'MENSUEL', _('Mensuel')
        TRIMESTRIEL = 'TRIMESTRIEL', _('Trimestriel')
        ANNUEL = 'ANNUEL', _('Annuel')
        PROJET = 'PROJET', _('Par projet')
        PERSONNALISE = 'PERSONNALISE', _('Personnalisé')
    
    class StatutRapport(models.TextChoices):
        EN_PREPARATION = 'EN_PREPARATION', _('En préparation')
        GENERE = 'GENERE', _('Généré')
        VALIDE = 'VALIDE', _('Validé')
        PUBLIE = 'PUBLIE', _('Publié')
        ARCHIVE = 'ARCHIVE', _('Archivé')
    
    # Identification du rapport
    nom_rapport = models.CharField(
        max_length=100, 
        verbose_name=_('Nom du rapport')
    )
    type_rapport = models.CharField(
        max_length=20,
        choices=TypeRapport.choices,
        verbose_name=_('Type de rapport')
    )
    statut_rapport = models.CharField(
        max_length=20,
        choices=StatutRapport.choices,
        default=StatutRapport.EN_PREPARATION,
        verbose_name=_('Statut du rapport')
    )
    
    # Période couverte
    periode_debut = models.DateField(
        verbose_name=_('Période de début')
    )
    periode_fin = models.DateField(
        verbose_name=_('Période de fin')
    )
    
    # Contenu du rapport
    donnees_rapport = models.JSONField(
        verbose_name=_('Données du rapport')
    )
    resume_executif = models.TextField(
        verbose_name=_('Résumé exécutif')
    )
    analyse_performance = models.TextField(
        verbose_name=_('Analyse de performance')
    )
    recommandations_amelioration = models.TextField(
        blank=True, 
        verbose_name=_('Recommandations d\'amélioration')
    )
    plan_action_propose = models.TextField(
        blank=True,
        verbose_name=_('Plan d\'action proposé')
    )
    
    # Métriques clés incluses
    inclut_metriques_financieres = models.BooleanField(
        default=True,
        verbose_name=_('Inclut métriques financières')
    )
    inclut_metriques_operationnelles = models.BooleanField(
        default=True,
        verbose_name=_('Inclut métriques opérationnelles')
    )
    inclut_metriques_securite = models.BooleanField(
        default=True,
        verbose_name=_('Inclut métriques sécurité')
    )
    inclut_analyses_tendances = models.BooleanField(
        default=False,
        verbose_name=_('Inclut analyses de tendances')
    )
    
    # Gestion et distribution
    genere_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        related_name='rapports_generes',
        verbose_name=_('Généré par')
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_valides',
        verbose_name=_('Validé par')
    )
    destinataires = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='rapports_recus',
        verbose_name=_('Destinataires')
    )
    
    # Fichiers et exports
    fichier_rapport_pdf = models.FileField(
        upload_to='rapports/pdf/', 
        null=True, 
        blank=True, 
        verbose_name=_('Fichier rapport PDF')
    )
    fichier_donnees_excel = models.FileField(
        upload_to='rapports/excel/',
        null=True,
        blank=True,
        verbose_name=_('Fichier données Excel')
    )
    
    # Audit et dates
    date_generation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de génération')
    )
    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de validation')
    )
    date_publication = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de publication')
    )
    
    @property
    def duree_periode(self):
        """Calcule la durée de la période couverte."""
        return (self.periode_fin - self.periode_debut).days
    
    @property
    def est_recent(self):
        """Vérifie si le rapport est récent (moins de 30 jours)."""
        from django.utils import timezone
        return (timezone.now().date() - self.date_generation.date()).days <= 30
    
    def valider_rapport(self, validateur):
        """Valide le rapport."""
        from django.utils import timezone
        self.valide_par = validateur
        self.date_validation = timezone.now()
        self.statut_rapport = self.StatutRapport.VALIDE
        self.save()
    
    def publier_rapport(self):
        """Publie le rapport."""
        from django.utils import timezone
        if self.statut_rapport == self.StatutRapport.VALIDE:
            self.date_publication = timezone.now()
            self.statut_rapport = self.StatutRapport.PUBLIE
            self.save()
    
    def __str__(self):
        return f"Rapport {self.nom_rapport} - {self.date_generation.strftime('%Y-%m-%d')}"
    
    class Meta:
        verbose_name = _('Rapport de performance détaillé')
        verbose_name_plural = _('Rapports de performance détaillés')
        ordering = ['-date_generation']
        indexes = [
            models.Index(fields=['type_rapport', 'statut_rapport']),
            models.Index(fields=['periode_debut', 'periode_fin']),
            models.Index(fields=['date_generation']),
        ]