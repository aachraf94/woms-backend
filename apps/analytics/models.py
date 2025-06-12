from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.wells.models import Well, Phase, Operation


class JeuDonneesAnalytiques(models.Model):
    """Modèle pour stocker les jeux de données analytiques."""
    
    TYPE_DONNEES_CHOICES = [
        ('PRODUCTION', _('Production')),
        ('FORAGE', _('Forage')),
        ('COMPLETION', _('Complétion')),
        ('RESERVOIR', _('Réservoir')),
        ('GEOLOGIE', _('Géologie')),
        ('PERFORMANCE', _('Performance')),
    ]
    
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE, 
        related_name='jeux_donnees_analytiques',
        verbose_name=_('Puits')
    )
    type_donnees = models.CharField(
        max_length=50, 
        choices=TYPE_DONNEES_CHOICES,
        verbose_name=_('Type de données')
    )
    nom_jeu_donnees = models.CharField(
        max_length=200,
        verbose_name=_('Nom du jeu de données')
    )
    donnees = models.JSONField(
        verbose_name=_('Données'),
        help_text=_('Stockage des données brutes au format JSON')
    )
    taille_donnees = models.PositiveIntegerField(
        null=True, 
        blank=True,
        verbose_name=_('Taille des données (octets)')
    )
    source_donnees = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Source des données')
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de création')
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Date de modification')
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Créé par')
    )
    
    def __str__(self):
        return f"{self.nom_jeu_donnees} - {self.puits.nom}"
    
    class Meta:
        verbose_name = _('Jeu de données analytiques')
        verbose_name_plural = _('Jeux de données analytiques')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['type_donnees']),
            models.Index(fields=['puits', 'type_donnees']),
            models.Index(fields=['-date_creation']),
        ]


class AnalyseEcart(models.Model):
    """Modèle pour l'analyse des écarts entre valeurs planifiées et réelles."""
    
    TYPES_INDICATEUR_CHOICES = [
        ('TEMPS', _('Temps')),
        ('COUT', _('Coût')),
        ('QUALITE', _('Qualité')),
        ('SECURITE', _('Sécurité')),
        ('PRODUCTION', _('Production')),
        ('PERFORMANCE', _('Performance')),
    ]
    
    NIVEAU_CRITICITE_CHOICES = [
        ('FAIBLE', _('Faible')),
        ('MOYEN', _('Moyen')),
        ('ELEVE', _('Élevé')),
        ('CRITIQUE', _('Critique')),
    ]
    
    phase = models.ForeignKey(
        Phase, 
        on_delete=models.CASCADE,
        related_name='analyses_ecart',
        verbose_name=_('Phase')
    )
    valeur_planifiee = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        verbose_name=_('Valeur planifiée')
    )
    valeur_reelle = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        verbose_name=_('Valeur réelle')
    )
    ecart_absolu = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        verbose_name=_('Écart absolu')
    )
    pourcentage_ecart = models.DecimalField(
        max_digits=7, 
        decimal_places=4, 
        null=True, 
        blank=True, 
        verbose_name=_('Pourcentage d\'écart'),
        validators=[MinValueValidator(-100), MaxValueValidator(100)]
    )
    type_indicateur = models.CharField(
        max_length=50,
        choices=TYPES_INDICATEUR_CHOICES,
        verbose_name=_('Type d\'indicateur')
    )
    niveau_criticite = models.CharField(
        max_length=20,
        choices=NIVEAU_CRITICITE_CHOICES,
        default='MOYEN',
        verbose_name=_('Niveau de criticité')
    )
    date_analyse = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date d\'analyse')
    )
    commentaire = models.TextField(
        blank=True, 
        verbose_name=_('Commentaire')
    )
    actions_correctives = models.TextField(
        blank=True,
        verbose_name=_('Actions correctives proposées')
    )
    analyseur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Analyseur')
    )
    
    def save(self, *args, **kwargs):
        # Calculer l'écart absolu
        self.ecart_absolu = self.valeur_reelle - self.valeur_planifiee
        
        # Calculer le pourcentage d'écart
        if self.valeur_planifiee and self.valeur_planifiee != 0:
            self.pourcentage_ecart = (self.ecart_absolu / self.valeur_planifiee) * 100
            
        # Déterminer le niveau de criticité automatiquement
        if self.pourcentage_ecart is not None:
            abs_pourcentage = abs(self.pourcentage_ecart)
            if abs_pourcentage >= 50:
                self.niveau_criticite = 'CRITIQUE'
            elif abs_pourcentage >= 25:
                self.niveau_criticite = 'ELEVE'
            elif abs_pourcentage >= 10:
                self.niveau_criticite = 'MOYEN'
            else:
                self.niveau_criticite = 'FAIBLE'
                
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Analyse {self.type_indicateur} - Phase {self.phase.numero_phase}"
    
    class Meta:
        verbose_name = _('Analyse d\'écart')
        verbose_name_plural = _('Analyses d\'écart')
        ordering = ['-date_analyse']
        indexes = [
            models.Index(fields=['type_indicateur']),
            models.Index(fields=['niveau_criticite']),
            models.Index(fields=['-date_analyse']),
        ]


class InteractionAssistantIA(models.Model):
    """Modèle pour les interactions avec l'assistant IA."""
    
    TYPES_REQUETE_CHOICES = [
        ('ANALYSE', _('Analyse de données')),
        ('PREDICTION', _('Prédiction')),
        ('RECOMMANDATION', _('Recommandation')),
        ('RECHERCHE', _('Recherche d\'information')),
        ('DIAGNOSTIC', _('Diagnostic')),
        ('OPTIMISATION', _('Optimisation')),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('EN_COURS', _('En cours de traitement')),
        ('COMPLETE', _('Complète')),
        ('ERREUR', _('Erreur')),
    ]
    
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='interactions_ia',
        verbose_name=_('Utilisateur')
    )
    requete = models.TextField(
        verbose_name=_('Requête utilisateur')
    )
    reponse = models.TextField(
        blank=True,
        verbose_name=_('Réponse de l\'IA')
    )
    type_requete = models.CharField(
        max_length=50,
        choices=TYPES_REQUETE_CHOICES,
        verbose_name=_('Type de requête')
    )
    puits_associe = models.ForeignKey(
        Well, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='interactions_ia',
        verbose_name=_('Puits associé')
    )
    score_pertinence = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_('Score de pertinence'),
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    temps_traitement = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_('Temps de traitement')
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE',
        verbose_name=_('Statut')
    )
    metadonnees = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Métadonnées'),
        help_text=_('Informations supplémentaires sur l\'interaction')
    )
    horodatage_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Horodatage de création')
    )
    horodatage_reponse = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Horodatage de réponse')
    )
    
    def __str__(self):
        return f"Interaction IA - {self.utilisateur.username} - {self.type_requete}"
    
    class Meta:
        verbose_name = _('Interaction Assistant IA')
        verbose_name_plural = _('Interactions Assistant IA')
        ordering = ['-horodatage_creation']
        indexes = [
            models.Index(fields=['utilisateur', '-horodatage_creation']),
            models.Index(fields=['type_requete']),
            models.Index(fields=['statut']),
        ]


class IndicateurPerformance(models.Model):
    """Modèle pour les indicateurs de performance."""
    
    STATUT_CHOICES = [
        ('PLANIFIE', _('Planifié')),
        ('EN_COURS', _('En cours')),
        ('REALISE', _('Réalisé')),
        ('ANNULE', _('Annulé')),
    ]
    
    operation = models.ForeignKey(
        Operation, 
        on_delete=models.CASCADE, 
        related_name='indicateurs_performance',
        verbose_name=_('Opération')
    )
    type_indicateur = models.ForeignKey(
        'wells.TypeIndicateur', 
        on_delete=models.CASCADE,
        verbose_name=_('Type d\'indicateur')
    )
    valeur_prevue = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        null=True, 
        blank=True, 
        verbose_name=_('Valeur prévue')
    )
    valeur_reelle = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        null=True, 
        blank=True, 
        verbose_name=_('Valeur réelle')
    )
    ecart_performance = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Écart de performance')
    )
    pourcentage_realisation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Pourcentage de réalisation')
    )
    date_mesure = models.DateTimeField(
        verbose_name=_('Date de mesure')
    )
    date_prevue = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date prévue')
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='PLANIFIE',
        verbose_name=_('Statut')
    )
    commentaire = models.TextField(
        blank=True, 
        verbose_name=_('Commentaire')
    )
    mesure_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Mesuré par')
    )
    
    def save(self, *args, **kwargs):
        # Calculer l'écart de performance
        if self.valeur_prevue is not None and self.valeur_reelle is not None:
            self.ecart_performance = self.valeur_reelle - self.valeur_prevue
            
            # Calculer le pourcentage de réalisation
            if self.valeur_prevue != 0:
                self.pourcentage_realisation = (self.valeur_reelle / self.valeur_prevue) * 100
                
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.type_indicateur.nom} - {self.operation}"
    
    class Meta:
        verbose_name = _('Indicateur de performance')
        verbose_name_plural = _('Indicateurs de performance')
        ordering = ['-date_mesure']
        indexes = [
            models.Index(fields=['operation', 'type_indicateur']),
            models.Index(fields=['-date_mesure']),
            models.Index(fields=['statut']),
        ]


class AnalyseReservoir(models.Model):
    """Modèle pour l'analyse des réservoirs."""
    
    TYPES_FLUIDE_CHOICES = [
        ('PETROLE', _('Pétrole')),
        ('GAZ', _('Gaz')),
        ('EAU', _('Eau')),
        ('MIXTE', _('Mixte')),
        ('CONDENSE', _('Condensé')),
    ]
    
    STATUT_ANALYSE_CHOICES = [
        ('PRELIMINAIRE', _('Préliminaire')),
        ('EN_COURS', _('En cours')),
        ('VALIDEE', _('Validée')),
        ('ARCHIVEE', _('Archivée')),
    ]
    
    reservoir = models.ForeignKey(
        'wells.Reservoir', 
        on_delete=models.CASCADE, 
        related_name='analyses_detaillees',
        verbose_name=_('Réservoir')
    )
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE,
        related_name='analyses_reservoir',
        verbose_name=_('Puits')
    )
    nom_analyse = models.CharField(
        max_length=200, 
        verbose_name=_('Nom de l\'analyse')
    )
    nature_fluide = models.CharField(
        max_length=50,
        choices=TYPES_FLUIDE_CHOICES,
        verbose_name=_('Nature du fluide')
    )
    hauteur_utile = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        null=True, 
        blank=True, 
        verbose_name=_('Hauteur utile (m)')
    )
    contact_fluide = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_('Contact fluide')
    )
    net_pay = models.DecimalField(
        max_digits=10, 
        decimal_places=3, 
        null=True, 
        blank=True, 
        verbose_name=_('Net Pay (m)')
    )
    debit_estime = models.DecimalField(
        max_digits=12, 
        decimal_places=3, 
        null=True, 
        blank=True, 
        verbose_name=_('Débit estimé (m³/j)')
    )
    pression_tete = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Pression en tête (bar)')
    )
    temperature_reservoir = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Température du réservoir (°C)')
    )
    porosite = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_('Porosité (%)')
    )
    permeabilite = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name=_('Perméabilité (mD)')
    )
    statut_analyse = models.CharField(
        max_length=20,
        choices=STATUT_ANALYSE_CHOICES,
        default='PRELIMINAIRE',
        verbose_name=_('Statut de l\'analyse')
    )
    date_analyse = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date d\'analyse')
    )
    analyste = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Analyste')
    )
    observations = models.TextField(
        blank=True,
        verbose_name=_('Observations')
    )
    
    def __str__(self):
        return f"Analyse {self.nom_analyse} - {self.puits.nom}"
    
    class Meta:
        verbose_name = _('Analyse de réservoir')
        verbose_name_plural = _('Analyses de réservoirs')
        ordering = ['-date_analyse']
        indexes = [
            models.Index(fields=['puits', 'reservoir']),
            models.Index(fields=['statut_analyse']),
            models.Index(fields=['-date_analyse']),
        ]


class TableauBordKPI(models.Model):
    """Modèle pour les KPIs du tableau de bord."""
    
    CATEGORIES_KPI_CHOICES = [
        ('PRODUCTION', _('Production')),
        ('OPERATION', _('Opération')),
        ('SECURITE', _('Sécurité')),
        ('ENVIRONNEMENT', _('Environnement')),
        ('FINANCIER', _('Financier')),
        ('TECHNIQUE', _('Technique')),
    ]
    
    STATUT_KPI_CHOICES = [
        ('EXCELLENT', _('Excellent')),
        ('BON', _('Bon')),
        ('SATISFAISANT', _('Satisfaisant')),
        ('MOYEN', _('Moyen')),
        ('INSUFFISANT', _('Insuffisant')),
        ('CRITIQUE', _('Critique')),
    ]
    
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE,
        related_name='kpis_tableau_bord',
        verbose_name=_('Puits')
    )
    nom_kpi = models.CharField(
        max_length=200, 
        verbose_name=_('Nom du KPI')
    )
    categorie_kpi = models.CharField(
        max_length=50,
        choices=CATEGORIES_KPI_CHOICES,
        verbose_name=_('Catégorie du KPI')
    )
    valeur_actuelle = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        verbose_name=_('Valeur actuelle')
    )
    valeur_precedente = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Valeur précédente')
    )
    unite_mesure = models.CharField(
        max_length=50, 
        verbose_name=_('Unité de mesure')
    )
    objectif_cible = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        null=True, 
        blank=True, 
        verbose_name=_('Objectif cible')
    )
    seuil_alerte = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Seuil d\'alerte')
    )
    pourcentage_atteinte = models.DecimalField(
        max_digits=7, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Pourcentage d\'atteinte')
    )
    evolution_pourcentage = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Évolution en pourcentage')
    )
    statut_kpi = models.CharField(
        max_length=20, 
        choices=STATUT_KPI_CHOICES,
        verbose_name=_('Statut KPI')
    )
    periode_reference = models.CharField(
        max_length=50,
        verbose_name=_('Période de référence')
    )
    date_calcul = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de calcul')
    )
    calcule_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Calculé par')
    )
    
    def save(self, *args, **kwargs):
        # Calculer le pourcentage d'atteinte
        if self.objectif_cible and self.objectif_cible != 0:
            self.pourcentage_atteinte = (self.valeur_actuelle / self.objectif_cible) * 100
        
        # Calculer l'évolution
        if self.valeur_precedente and self.valeur_precedente != 0:
            self.evolution_pourcentage = ((self.valeur_actuelle - self.valeur_precedente) / self.valeur_precedente) * 100
            
        # Déterminer automatiquement le statut
        if self.pourcentage_atteinte is not None:
            if self.pourcentage_atteinte >= 120:
                self.statut_kpi = 'EXCELLENT'
            elif self.pourcentage_atteinte >= 100:
                self.statut_kpi = 'BON'
            elif self.pourcentage_atteinte >= 90:
                self.statut_kpi = 'SATISFAISANT'
            elif self.pourcentage_atteinte >= 75:
                self.statut_kpi = 'MOYEN'
            elif self.pourcentage_atteinte >= 50:
                self.statut_kpi = 'INSUFFISANT'
            else:
                self.statut_kpi = 'CRITIQUE'
                
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nom_kpi} - {self.puits.nom}"
    
    class Meta:
        verbose_name = _('KPI de tableau de bord')
        verbose_name_plural = _('KPIs de tableau de bord')
        ordering = ['-date_calcul']
        indexes = [
            models.Index(fields=['puits', 'categorie_kpi']),
            models.Index(fields=['statut_kpi']),
            models.Index(fields=['-date_calcul']),
        ]


class AnalysePredictive(models.Model):
    """Modèle pour les analyses prédictives."""
    
    TYPES_PREDICTION_CHOICES = [
        ('PRODUCTION', _('Prédiction de production')),
        ('MAINTENANCE', _('Maintenance prédictive')),
        ('DEFAILLANCE', _('Prédiction de défaillance')),
        ('OPTIMISATION', _('Optimisation opérationnelle')),
        ('COUT', _('Prédiction de coût')),
        ('PERFORMANCE', _('Performance future')),
    ]
    
    STATUT_PREDICTION_CHOICES = [
        ('EN_COURS', _('En cours')),
        ('COMPLETE', _('Complète')),
        ('VALIDEE', _('Validée')),
        ('REJETEE', _('Rejetée')),
        ('ARCHIVEE', _('Archivée')),
    ]
    
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE,
        related_name='analyses_predictives',
        verbose_name=_('Puits')
    )
    nom_analyse = models.CharField(
        max_length=200,
        verbose_name=_('Nom de l\'analyse')
    )
    type_prediction = models.CharField(
        max_length=50,
        choices=TYPES_PREDICTION_CHOICES,
        verbose_name=_('Type de prédiction')
    )
    valeur_predite = models.DecimalField(
        max_digits=15, 
        decimal_places=4, 
        verbose_name=_('Valeur prédite')
    )
    valeur_min_predite = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Valeur minimale prédite')
    )
    valeur_max_predite = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Valeur maximale prédite')
    )
    intervalle_confiance = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name=_('Intervalle de confiance (%)'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    date_prediction_pour = models.DateField(
        verbose_name=_('Date cible de la prédiction')
    )
    horizon_prediction_jours = models.PositiveIntegerField(
        verbose_name=_('Horizon de prédiction (jours)')
    )
    modele_utilise = models.CharField(
        max_length=100, 
        verbose_name=_('Modèle utilisé')
    )
    version_modele = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Version du modèle')
    )
    parametres_modele = models.JSONField(
        verbose_name=_('Paramètres du modèle')
    )
    metriques_performance = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Métriques de performance du modèle')
    )
    donnees_entree = models.JSONField(
        verbose_name=_('Données d\'entrée utilisées')
    )
    statut_prediction = models.CharField(
        max_length=20,
        choices=STATUT_PREDICTION_CHOICES,
        default='EN_COURS',
        verbose_name=_('Statut de la prédiction')
    )
    date_creation = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_('Date de création')
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Créé par')
    )
    observations = models.TextField(
        blank=True,
        verbose_name=_('Observations')
    )
    
    def clean(self):
        super().clean()
        if self.intervalle_confiance and (self.intervalle_confiance < 0 or self.intervalle_confiance > 100):
            raise ValidationError(_('L\'intervalle de confiance doit être entre 0 et 100.'))
    
    def __str__(self):
        return f"Prédiction {self.nom_analyse} - {self.puits.nom}"
    
    class Meta:
        verbose_name = _('Analyse prédictive')
        verbose_name_plural = _('Analyses prédictives')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['puits', 'type_prediction']),
            models.Index(fields=['statut_prediction']),
            models.Index(fields=['-date_creation']),
            models.Index(fields=['date_prediction_pour']),
        ]


class AlerteAnalytique(models.Model):
    """Modèle pour les alertes analytiques automatisées."""
    
    TYPES_ALERTE_CHOICES = [
        ('SEUIL_DEPASSE', _('Seuil dépassé')),
        ('ANOMALIE_DETECTEE', _('Anomalie détectée')),
        ('PERFORMANCE_DEGRADEE', _('Performance dégradée')),
        ('PREDICTION_CRITIQUE', _('Prédiction critique')),
        ('ECART_IMPORTANT', _('Écart important')),
    ]
    
    NIVEAUX_URGENCE_CHOICES = [
        ('INFO', _('Information')),
        ('ATTENTION', _('Attention')),
        ('URGENT', _('Urgent')),
        ('CRITIQUE', _('Critique')),
    ]
    
    STATUT_ALERTE_CHOICES = [
        ('NOUVELLE', _('Nouvelle')),
        ('EN_COURS', _('En cours de traitement')),
        ('RESOLUE', _('Résolue')),
        ('IGNOREE', _('Ignorée')),
    ]
    
    puits = models.ForeignKey(
        Well,
        on_delete=models.CASCADE,
        related_name='alertes_analytiques',
        verbose_name=_('Puits')
    )
    type_alerte = models.CharField(
        max_length=50,
        choices=TYPES_ALERTE_CHOICES,
        verbose_name=_('Type d\'alerte')
    )
    niveau_urgence = models.CharField(
        max_length=20,
        choices=NIVEAUX_URGENCE_CHOICES,
        verbose_name=_('Niveau d\'urgence')
    )
    titre_alerte = models.CharField(
        max_length=200,
        verbose_name=_('Titre de l\'alerte')
    )
    description = models.TextField(
        verbose_name=_('Description')
    )
    valeur_declenchante = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Valeur déclenchante')
    )
    seuil_reference = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Seuil de référence')
    )
    source_donnees = models.CharField(
        max_length=100,
        verbose_name=_('Source des données')
    )
    statut_alerte = models.CharField(
        max_length=20,
        choices=STATUT_ALERTE_CHOICES,
        default='NOUVELLE',
        verbose_name=_('Statut de l\'alerte')
    )
    date_declenchement = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de déclenchement')
    )
    date_resolution = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Date de résolution')
    )
    assigne_a = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_assignees',
        verbose_name=_('Assigné à')
    )
    resolu_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_resolues',
        verbose_name=_('Résolu par')
    )
    actions_prises = models.TextField(
        blank=True,
        verbose_name=_('Actions prises')
    )
    
    def __str__(self):
        return f"Alerte {self.titre_alerte} - {self.puits.nom}"
    
    class Meta:
        verbose_name = _('Alerte analytique')
        verbose_name_plural = _('Alertes analytiques')
        ordering = ['-date_declenchement']
        indexes = [
            models.Index(fields=['statut_alerte', '-date_declenchement']),
            models.Index(fields=['niveau_urgence']),
            models.Index(fields=['puits', 'type_alerte']),
        ]
