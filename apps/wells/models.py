from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class StatutPuit(models.TextChoices):
    """Statuts possibles d'un puit."""
    EN_COURS = 'EN_COURS', _('En cours')
    TERMINE = 'TERMINE', _('Terminé')
    ABANDONNE = 'ABANDONNE', _('Abandonné')
    PLANIFIE = 'PLANIFIE', _('Planifié')
    # Keep existing for backward compatibility
    PLANNED = 'planned', _('Planned')
    ACTIVE = 'active', _('Active')
    PAUSED = 'paused', _('Paused')
    COMPLETED = 'completed', _('Completed')
    ABANDONED = 'abandoned', _('Abandoned')
    ARCHIVED = 'archived', _('Archived')


class TypeOperation(models.TextChoices):
    """Types d'opérations standardisés."""
    FORAGE = 'forage', _('Forage')
    COMPLETION = 'completion', _('Complétion')
    RECONDITIONNEMENT = 'workover', _('Reconditionnement')
    MAINTENANCE = 'maintenance', _('Maintenance')
    TEST = 'testing', _('Test')


class StatutOperation(models.TextChoices):
    """Statuts possibles d'une opération."""
    PLANIFIE = 'planifie', _('Planifié')
    EN_COURS = 'en_cours', _('En cours')
    EN_PAUSE = 'en_pause', _('En pause')
    TERMINE = 'termine', _('Terminé')
    ANNULE = 'annule', _('Annulé')


class Region(models.Model):
    """Modèle représentant une région géographique pour les opérations de puits."""
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    localisation = models.CharField(max_length=255, verbose_name=_('Localisation'))
    responsable = models.CharField(max_length=100, verbose_name=_('Responsable'))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    class Meta:
        verbose_name = _('Région')
        verbose_name_plural = _('Régions')
        ordering = ['nom']


class Puit(models.Model):
    """Modèle représentant un puit."""
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    type = models.CharField(max_length=50, blank=True, verbose_name=_('Type'))
    
    # Relations
    region = models.ForeignKey(Region, on_delete=models.PROTECT, null=True, blank=True, verbose_name=_('Région'), 
                              related_name='puits')
    
    # Coordonnées
    coord_x = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('Coordonnée X'))
    coord_y = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name=_('Coordonnée Y'))
    
    statut = models.CharField(
        max_length=20,
        choices=StatutPuit.choices,
        default=StatutPuit.PLANIFIE,
        verbose_name=_('Statut')
    )
    
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Profondeur
    profondeur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Profondeur'))
    
    # Dates
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Date de début'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('Date de fin'))
    
    # Traçabilité
    cree_par = models.CharField(max_length=100, blank=True, verbose_name=_('Créé par'))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    cree_par_utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='puits_crees',
        null=True,
        blank=True,
        verbose_name=_('Créé par (utilisateur)')
    )
    derniere_maj = models.DateTimeField(auto_now=True, verbose_name=_('Dernière mise à jour'))
    maj_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='puits_mis_a_jour',
        null=True,
        blank=True,
        verbose_name=_('Mis à jour par')
    )
    est_archive = models.BooleanField(default=False, verbose_name=_('Est archivé'))
    
    # Keep existing fields for backward compatibility
    name = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatutPuit.choices, default=StatutPuit.PLANNED, blank=True)
    depth = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_by = models.CharField(max_length=100, blank=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_wells',
        null=True,
        blank=True
    )
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_wells',
        null=True,
        blank=True
    )
    is_archived = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nom or self.name} ({self.get_statut_display() if self.statut else self.get_status_display()})"
    
    class Meta:
        verbose_name = _('Puit')
        verbose_name_plural = _('Puits')
        ordering = ['-date_creation']


class Forage(models.Model):
    """Modèle représentant une opération de forage."""
    puit = models.OneToOneField(Puit, on_delete=models.CASCADE, related_name='forage', verbose_name=_('Puit'))
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Coût'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Date de début'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('Date de fin'))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_maj = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    def __str__(self):
        return f"Forage - {self.puit.nom or self.puit.name}"
    
    class Meta:
        verbose_name = _('Forage')
        verbose_name_plural = _('Forages')
        ordering = ['-date_debut']


class TypeOperationDetaille(models.Model):
    """Modèle représentant les types d'opérations qui peuvent être effectuées."""
    code = models.CharField(max_length=20, unique=True, primary_key=True, verbose_name=_('Code'))
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    duree_estimee = models.PositiveIntegerField(null=True, blank=True, help_text=_('Durée estimée en heures'), 
                                               verbose_name=_('Durée estimée'))
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                       verbose_name=_('Coût unitaire'))
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    class Meta:
        verbose_name = _('Type d\'opération')
        verbose_name_plural = _('Types d\'opérations')
        ordering = ['code']


class Phase(models.Model):
    """Modèle représentant les phases d'opérations de forage."""
    
    class Diametre(models.TextChoices):
        POUCES_26 = '26"', _('26 pouces')
        POUCES_16 = '16"', _('16 pouces')
        POUCES_12_25 = '12_1_4"', _('12 1/4 pouces')
        POUCES_8_5 = '8_1_2"', _('8 1/2 pouces')
    
    forage = models.ForeignKey(Forage, on_delete=models.CASCADE, related_name='phases', verbose_name=_('Forage'))
    numero_phase = models.PositiveIntegerField(verbose_name=_('Numéro de phase'))
    diametre = models.CharField(max_length=10, choices=Diametre.choices, verbose_name=_('Diamètre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Profondeurs planifiées vs réelles
    profondeur_prevue = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                           verbose_name=_('Profondeur prévue'))
    profondeur_reelle = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                           verbose_name=_('Profondeur réelle'))
    
    # Dates planifiées vs réelles
    date_debut_prevue = models.DateField(null=True, blank=True, verbose_name=_('Date de début prévue'))
    date_debut_reelle = models.DateField(null=True, blank=True, verbose_name=_('Date de début réelle'))
    date_fin_prevue = models.DateField(null=True, blank=True, verbose_name=_('Date de fin prévue'))
    date_fin_reelle = models.DateField(null=True, blank=True, verbose_name=_('Date de fin réelle'))
    
    def __str__(self):
        return f"Phase {self.numero_phase} - {self.forage.puit.nom or self.forage.puit.name}"
    
    class Meta:
        verbose_name = _('Phase')
        verbose_name_plural = _('Phases')
        ordering = ['forage', 'numero_phase']
        unique_together = ['forage', 'numero_phase']


class OperationDetaille(models.Model):
    """Modèle représentant les opérations effectuées lors des phases."""
    
    class Statut(models.TextChoices):
        PLANIFIE = 'PLANIFIE', _('Planifié')
        EN_COURS = 'EN_COURS', _('En cours')
        TERMINE = 'TERMINE', _('Terminé')
        PROBLEME = 'PROBLEME', _('Problème')
        ANNULE = 'ANNULE', _('Annulé')
    
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='operations', verbose_name=_('Phase'))
    type_operation = models.ForeignKey(TypeOperationDetaille, on_delete=models.CASCADE, 
                                      verbose_name=_('Type d\'opération'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Date de début'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('Date de fin'))
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Coût'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIE, verbose_name=_('Statut'))
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
                                related_name='operations_creees', verbose_name=_('Créé par'))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    
    def __str__(self):
        return f"{self.type_operation.nom} - Phase {self.phase.numero_phase}"
    
    class Meta:
        verbose_name = _('Opération')
        verbose_name_plural = _('Opérations')
        ordering = ['-date_creation']


class TypeIndicateur(models.Model):
    """Modèle représentant les types d'indicateurs de performance."""
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    unite = models.CharField(max_length=20, verbose_name=_('Unité'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    type_operation = models.ForeignKey(TypeOperationDetaille, on_delete=models.CASCADE, null=True, blank=True, 
                                      verbose_name=_('Type d\'opération'))
    est_obligatoire = models.BooleanField(default=False, verbose_name=_('Est obligatoire'))
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    class Meta:
        verbose_name = _('Type d\'indicateur')
        verbose_name_plural = _('Types d\'indicateurs')
        ordering = ['code']


class Indicateur(models.Model):
    """Modèle représentant les indicateurs de performance."""
    operation = models.ForeignKey(OperationDetaille, on_delete=models.CASCADE, related_name='indicateurs', 
                                 verbose_name=_('Opération'))
    type_indicateur = models.ForeignKey(TypeIndicateur, on_delete=models.CASCADE, 
                                       verbose_name=_('Type d\'indicateur'))
    valeur_prevue = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, 
                                       verbose_name=_('Valeur prévue'))
    valeur_reelle = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, 
                                       verbose_name=_('Valeur réelle'))
    date_mesure = models.DateTimeField(verbose_name=_('Date de mesure'))
    commentaire = models.TextField(blank=True, verbose_name=_('Commentaire'))
    
    def __str__(self):
        return f"{self.type_indicateur.nom} - {self.operation}"
    
    class Meta:
        verbose_name = _('Indicateur')
        verbose_name_plural = _('Indicateurs')
        ordering = ['-date_mesure']


class Reservoir(models.Model):
    """Modèle représentant les informations sur les réservoirs."""
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    puit = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='reservoirs', verbose_name=_('Puit'))
    nature_fluide = models.CharField(max_length=50, verbose_name=_('Nature du fluide'))
    hauteur_utile = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                       verbose_name=_('Hauteur utile'))
    contact_fluide = models.CharField(max_length=100, blank=True, verbose_name=_('Contact fluide'))
    net_pay = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Net Pay'))
    debit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Débit'))
    pression_tete = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                       verbose_name=_('Pression en tête'))
    profondeur = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                    verbose_name=_('Profondeur'))
    pression = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Pression'))
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                     verbose_name=_('Température'))
    type_fluide = models.CharField(max_length=50, blank=True, verbose_name=_('Type de fluide'))
    
    def __str__(self):
        return f"{self.nom} - {self.puit.nom or self.puit.name}"
    
    class Meta:
        verbose_name = _('Réservoir')
        verbose_name_plural = _('Réservoirs')
        ordering = ['nom']


class Probleme(models.Model):
    """Modèle représentant les problèmes et incidents."""
    
    class Type(models.TextChoices):
        DELAI = 'DELAI', _('Délai')
        COUT = 'COUT', _('Coût')
        SECURITE = 'SECURITE', _('Sécurité')
        TECHNIQUE = 'TECHNIQUE', _('Technique')
    
    class Gravite(models.TextChoices):
        FAIBLE = 'FAIBLE', _('Faible')
        MODEREE = 'MODEREE', _('Modérée')
        CRITIQUE = 'CRITIQUE', _('Critique')
    
    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', _('Ouvert')
        EN_COURS = 'EN_COURS', _('En cours')
        RESOLU = 'RESOLU', _('Résolu')
        FERME = 'FERME', _('Fermé')
    
    operation = models.ForeignKey(OperationDetaille, on_delete=models.CASCADE, related_name='problemes', 
                                 verbose_name=_('Opération'))
    
    titre = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(verbose_name=_('Description'))
    type_probleme = models.CharField(max_length=20, choices=Type.choices, verbose_name=_('Type de problème'))
    gravite = models.CharField(max_length=20, choices=Gravite.choices, verbose_name=_('Gravité'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT, verbose_name=_('Statut'))
    
    date_detection = models.DateField(auto_now_add=True, verbose_name=_('Date de détection'))
    date_resolution = models.DateField(null=True, blank=True, verbose_name=_('Date de résolution'))
    
    detecte_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
                                   related_name='problemes_detectes', verbose_name=_('Détecté par'))
    resolu_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
                                  related_name='problemes_resolus', verbose_name=_('Résolu par'))
    
    solution = models.TextField(blank=True, verbose_name=_('Solution'))
    impact_cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, 
                                     verbose_name=_('Impact coût'))
    impact_delai = models.PositiveIntegerField(null=True, blank=True, help_text=_('Impact délai en heures'), 
                                             verbose_name=_('Impact délai'))
    
    def __str__(self):
        return f"{self.titre} - {self.get_gravite_display()}"
    
    class Meta:
        verbose_name = _('Problème')
        verbose_name_plural = _('Problèmes')
        ordering = ['-date_detection']


# Modèles de compatibilité avec les versions précédentes (à conserver)

class OperationPuit(models.Model):
    """Modèle représentant une opération effectuée sur un puit."""
    puit = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='operations')
    type_operation = models.CharField(
        max_length=20,
        choices=TypeOperation.choices
    )
    nom = models.CharField(max_length=255, verbose_name=_('Nom'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    date_debut_prevue = models.DateTimeField(verbose_name=_('Date de début prévue'))
    date_fin_prevue = models.DateTimeField(verbose_name=_('Date de fin prévue'))
    date_debut_reelle = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de début réelle'))
    date_fin_reelle = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de fin réelle'))
    statut = models.CharField(
        max_length=20,
        choices=StatutOperation.choices,
        default=StatutOperation.PLANIFIE,
        verbose_name=_('Statut')
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='operations_puit_creees',
        verbose_name=_('Créé par')
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_maj = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    # Keep for backward compatibility
    well = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='well_operations', null=True)
    operation_type = models.CharField(max_length=20, choices=TypeOperation.choices, null=True)
    name = models.CharField(max_length=255, blank=True)
    planned_start_date = models.DateTimeField(null=True)
    planned_end_date = models.DateTimeField(null=True)
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=StatutOperation.choices, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_operations',
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.type_operation} - {self.puit.nom or self.puit.name} - {self.statut}"
    
    class Meta:
        verbose_name = _('Opération de puit')
        verbose_name_plural = _('Opérations de puit')
        ordering = ['-date_debut_prevue']


class RapportQuotidien(models.Model):
    """Modèle pour les rapports quotidiens sur les opérations de puits."""
    puit = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='rapports_quotidiens', 
                            verbose_name=_('Puit'))
    operation = models.ForeignKey(
        OperationPuit, 
        on_delete=models.CASCADE, 
        related_name='rapports_quotidiens',
        null=True, 
        blank=True,
        verbose_name=_('Opération')
    )
    date_rapport = models.DateField(verbose_name=_('Date du rapport'))
    activites = models.TextField(verbose_name=_('Activités'))
    progression = models.DecimalField(max_digits=5, decimal_places=2, 
                                     help_text=_('Progression en pourcentage'),
                                     verbose_name=_('Progression'))
    problemes = models.TextField(blank=True, verbose_name=_('Problèmes'))
    solutions = models.TextField(blank=True, verbose_name=_('Solutions'))
    heures_travaillees = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_('Heures travaillées'))
    soumis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rapports_soumis',
        verbose_name=_('Soumis par')
    )
    date_soumission = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de soumission'))
    date_maj = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    # Keep for backward compatibility
    well = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='daily_reports', null=True)
    report_date = models.DateField(null=True)
    activities = models.TextField(blank=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    issues = models.TextField(blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='submitted_reports',
        null=True
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Rapport pour {self.puit.nom or self.well.name} le {self.date_rapport or self.report_date}"
    
    class Meta:
        verbose_name = _('Rapport quotidien')
        verbose_name_plural = _('Rapports quotidiens')
        ordering = ['-date_rapport']
        unique_together = ['puit', 'date_rapport']


class Document(models.Model):
    """Modèle pour les documents liés aux puits."""
    # Relations
    puit = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='documents', verbose_name=_('Puit'))
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, null=True, blank=True, related_name='documents',
                             verbose_name=_('Phase'))
    operation = models.ForeignKey(OperationDetaille, on_delete=models.CASCADE, null=True, blank=True, 
                                 related_name='documents', verbose_name=_('Opération'))
    
    # Attributs
    nom = models.CharField(max_length=255, verbose_name=_('Nom'))
    type_document = models.CharField(max_length=100, verbose_name=_('Type de document'))
    fichier = models.FileField(upload_to='documents_puit/', verbose_name=_('Fichier'))
    taille = models.BigIntegerField(null=True, blank=True, verbose_name=_('Taille'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    est_public = models.BooleanField(default=False, verbose_name=_('Est public'))
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'upload'))
    uploade_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documents_uploades',
        verbose_name=_('Uploadé par')
    )
    
    # Keep for backward compatibility
    well = models.ForeignKey(Puit, on_delete=models.CASCADE, related_name='legacy_documents', null=True)
    title = models.CharField(max_length=255, blank=True)
    document_type = models.CharField(max_length=100, blank=True)
    file = models.FileField(upload_to='well_documents/', blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_documents',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nom or self.title} - {self.puit.nom if self.puit else (self.well.nom if self.well else 'N/A')}"
    
    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-date_upload']

# Alias for backward compatibility
Well = Puit
WellOperation = OperationPuit
DailyReport = RapportQuotidien
WellDocument = Document
WellDocument = Document
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_operations_detailed', verbose_name=_('Créé par'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    
    def __str__(self):
        return f"{self.type_operation.nom} - Phase {self.phase.numero_phase}"
    
    class Meta:
        verbose_name = _('Opération')
        verbose_name_plural = _('Opérations')
        ordering = ['-created_at']


# TypeIndicateur model 
class TypeIndicateur(models.Model):
    """Model representing types of performance indicators."""
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    unite = models.CharField(max_length=20, verbose_name=_('Unité'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    type_operation = models.ForeignKey(TypeOperation, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Type d\'opération'))
    est_obligatoire = models.BooleanField(default=False, verbose_name=_('Est obligatoire'))
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    class Meta:
        verbose_name = _('Type d\'indicateur')
        verbose_name_plural = _('Types d\'indicateurs')
        ordering = ['code']


# Indicateur model 
class Indicateur(models.Model):
    """Model representing performance indicators."""
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='indicateurs', verbose_name=_('Opération'))
    type_indicateur = models.ForeignKey(TypeIndicateur, on_delete=models.CASCADE, verbose_name=_('Type d\'indicateur'))
    valeur_prevue = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, verbose_name=_('Valeur prévue'))
    valeur_reelle = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, verbose_name=_('Valeur réelle'))
    date_mesure = models.DateTimeField(verbose_name=_('Date de mesure'))
    commentaire = models.TextField(blank=True, verbose_name=_('Commentaire'))
    notes = models.TextField(blank=True)  # Keep for backward compatibility
    
    def __str__(self):
        return f"{self.type_indicateur.nom} - {self.operation}"
    
    class Meta:
        verbose_name = _('Indicateur')
        verbose_name_plural = _('Indicateurs')
        ordering = ['-date_mesure']


# Reservoir model 
class Reservoir(models.Model):
    """Model representing reservoir information."""
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    puit = models.ForeignKey(Well, on_delete=models.CASCADE, related_name='reservoirs', verbose_name=_('Puits'))
    nature_fluide = models.CharField(max_length=50, verbose_name=_('Nature du fluide'))
    hauteur_utile = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Hauteur utile'))
    contact_fluide = models.CharField(max_length=100, blank=True, verbose_name=_('Contact fluide'))
    net_pay = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Net Pay'))
    debit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Débit'))
    pression_tete = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Pression en tête'))
    
    # Keep existing fields for backward compatibility
    profondeur = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Profondeur'))
    pression = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Pression'))
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('Température'))
    type_fluide = models.CharField(max_length=50, blank=True, verbose_name=_('Type de fluide'))
    
    def __str__(self):
        return f"{self.nom} - {self.puit.nom or self.puit.name}"
    
    class Meta:
        verbose_name = _('Réservoir')
        verbose_name_plural = _('Réservoirs')
        ordering = ['nom']

class Region(models.Model):
    """Modèle représentant une région géographique pour les opérations de puits."""
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    localisation = models.CharField(max_length=255, verbose_name=_('Localisation'))
    responsable = models.CharField(max_length=100, verbose_name=_('Responsable'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    class Meta:
        verbose_name = _('Région')
        verbose_name_plural = _('Régions')
        ordering = ['nom']


class Forage(models.Model):
    """Modèle représentant une opération de forage."""
    puit = models.OneToOneField('models.Puit', on_delete=models.CASCADE, related_name='forage', verbose_name=_('Puit'))
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Coût'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Date de début'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('Date de fin'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    
    def __str__(self):
        return f"Forage - {self.puit.nom}"
    
    class Meta:
        verbose_name = _('Forage')
        verbose_name_plural = _('Forages')
        ordering = ['-date_debut']


class TypeOperation(models.Model):
    """Modèle représentant les types d'opérations qui peuvent être effectuées."""
    code = models.CharField(max_length=20, unique=True, primary_key=True, verbose_name=_('Code'))
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    duree_estimee = models.PositiveIntegerField(null=True, blank=True, help_text=_('Durée estimée en heures'), 
                                               verbose_name=_('Durée estimée'))
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, 
                                       verbose_name=_('Coût unitaire'))
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    class Meta:
        verbose_name = _('Type d\'opération')
        verbose_name_plural = _('Types d\'opérations')
        ordering = ['code']


class Phase(models.Model):
    """Modèle représentant les phases d'opérations de forage."""
    
    class Diametre(models.TextChoices):
        POUCES_26 = '26"', _('26 pouces')
        POUCES_16 = '16"', _('16 pouces')
        POUCES_12_25 = '12_1_4"', _('12 1/4 pouces')
        POUCES_8_5 = '8_1_2"', _('8 1/2 pouces')
    
    forage = models.ForeignKey(Forage, on_delete=models.CASCADE, related_name='phases', verbose_name=_('Forage'))
    numero_phase = models.PositiveIntegerField(verbose_name=_('Numéro de phase'))
    diametre = models.CharField(max_length=10, choices=Diametre.choices, verbose_name=_('Diamètre'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Profondeurs planifiées vs réelles
    profondeur_prevue = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                           verbose_name=_('Profondeur prévue'))
    profondeur_reelle = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                           verbose_name=_('Profondeur réelle'))
    
    # Dates planifiées vs réelles
    date_debut_prevue = models.DateField(null=True, blank=True, verbose_name=_('Date de début prévue'))
    date_debut_reelle = models.DateField(null=True, blank=True, verbose_name=_('Date de début réelle'))
    date_fin_prevue = models.DateField(null=True, blank=True, verbose_name=_('Date de fin prévue'))
    date_fin_reelle = models.DateField(null=True, blank=True, verbose_name=_('Date de fin réelle'))
    
    def __str__(self):
        return f"Phase {self.numero_phase} - {self.forage.puit.nom}"
    
    class Meta:
        verbose_name = _('Phase')
        verbose_name_plural = _('Phases')
        ordering = ['forage', 'numero_phase']
        unique_together = ['forage', 'numero_phase']


class Operation(models.Model):
    """Modèle représentant les opérations effectuées lors des phases."""
    
    class Statut(models.TextChoices):
        PLANIFIE = 'PLANIFIE', _('Planifié')
        EN_COURS = 'EN_COURS', _('En cours')
        TERMINE = 'TERMINE', _('Terminé')
        PROBLEME = 'PROBLEME', _('Problème')
        ANNULE = 'ANNULE', _('Annulé')
    
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='operations', verbose_name=_('Phase'))
    type_operation = models.ForeignKey(TypeOperation, on_delete=models.CASCADE, verbose_name=_('Type d\'opération'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Date de début'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('Date de fin'))
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Coût'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIE, verbose_name=_('Statut'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='operations_creees', 
                                 verbose_name=_('Créé par'))
    
    def __str__(self):
        return f"{self.type_operation.nom} - Phase {self.phase.numero_phase}"
    
    class Meta:
        verbose_name = _('Opération')
        verbose_name_plural = _('Opérations')
        ordering = ['-date_debut']


class TypeIndicateur(models.Model):
    """Modèle représentant les types d'indicateurs de performance."""
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    unite = models.CharField(max_length=20, verbose_name=_('Unité'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    type_operation = models.ForeignKey(TypeOperation, on_delete=models.CASCADE, null=True, blank=True, 
                                     verbose_name=_('Type d\'opération'))
    est_obligatoire = models.BooleanField(default=False, verbose_name=_('Est obligatoire'))
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    class Meta:
        verbose_name = _('Type d\'indicateur')
        verbose_name_plural = _('Types d\'indicateurs')
        ordering = ['code']


class Indicateur(models.Model):
    """Modèle représentant les indicateurs de performance."""
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='indicateurs', 
                                verbose_name=_('Opération'))
    type_indicateur = models.ForeignKey(TypeIndicateur, on_delete=models.CASCADE, 
                                      verbose_name=_('Type d\'indicateur'))
    valeur_prevue = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, 
                                      verbose_name=_('Valeur prévue'))
    valeur_reelle = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True, 
                                      verbose_name=_('Valeur réelle'))
    date_mesure = models.DateTimeField(verbose_name=_('Date de mesure'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    def __str__(self):
        return f"{self.type_indicateur.nom} - {self.operation}"
    
    class Meta:
        verbose_name = _('Indicateur')
        verbose_name_plural = _('Indicateurs')
        ordering = ['-date_mesure']


class Reservoir(models.Model):
    """Modèle représentant les informations sur les réservoirs."""
    nom = models.CharField(max_length=100, verbose_name=_('Nom'))
    puit = models.ForeignKey('models.Puit', on_delete=models.CASCADE, related_name='reservoirs_region', 
                           verbose_name=_('Puit'))
    profondeur = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, 
                                   verbose_name=_('Profondeur'))
    pression = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Pression'))
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, 
                                    verbose_name=_('Température'))
    type_fluide = models.CharField(max_length=50, verbose_name=_('Type de fluide'))
    
    def __str__(self):
        return f"{self.nom} - {self.puit.nom}"
    
    class Meta:
        verbose_name = _('Réservoir')
        verbose_name_plural = _('Réservoirs')
        ordering = ['profondeur']


class Probleme(models.Model):
    """Modèle représentant les problèmes et incidents."""
    
    class Type(models.TextChoices):
        DELAI = 'DELAI', _('Délai')
        COUT = 'COUT', _('Coût')
        SECURITE = 'SECURITE', _('Sécurité')
        TECHNIQUE = 'TECHNIQUE', _('Technique')
    
    class Gravite(models.TextChoices):
        FAIBLE = 'FAIBLE', _('Faible')
        MODEREE = 'MODEREE', _('Modérée')
        CRITIQUE = 'CRITIQUE', _('Critique')
    
    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', _('Ouvert')
        EN_COURS = 'EN_COURS', _('En cours')
        RESOLU = 'RESOLU', _('Résolu')
        FERME = 'FERME', _('Fermé')
    
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='problemes', 
                                verbose_name=_('Opération'))
    titre = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(verbose_name=_('Description'))
    type_probleme = models.CharField(max_length=20, choices=Type.choices, verbose_name=_('Type de problème'))
    gravite = models.CharField(max_length=20, choices=Gravite.choices, verbose_name=_('Gravité'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT, verbose_name=_('Statut'))
    
    date_detection = models.DateField(auto_now_add=True, verbose_name=_('Date de détection'))
    date_resolution = models.DateField(null=True, blank=True, verbose_name=_('Date de résolution'))
    
    detecte_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, 
                                  related_name='problemes_detectes', verbose_name=_('Détecté par'))
    assigne_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, 
                                related_name='problemes_assignes', verbose_name=_('Assigné à'))
    
    solution = models.TextField(blank=True, verbose_name=_('Solution'))
    impact_cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, 
                                    verbose_name=_('Impact coût'))
    impact_delai = models.PositiveIntegerField(null=True, blank=True, help_text=_('Impact délai en heures'), 
                                             verbose_name=_('Impact délai'))
    
    def __str__(self):
        return f"{self.titre} - {self.get_gravite_display()}"
    
    class Meta:
        verbose_name = _('Problème')
        verbose_name_plural = _('Problèmes')
        ordering = ['-date_detection']


# Probleme model (converted from Java Probleme model)
class Probleme(models.Model):
    """Model representing problems and incidents."""
    
    class Type(models.TextChoices):
        DELAI = 'DELAI', _('Délai')
        COUT = 'COUT', _('Coût')
        SECURITE = 'SECURITE', _('Sécurité')
        TECHNIQUE = 'TECHNIQUE', _('Technique')
    
    class Gravite(models.TextChoices):
        FAIBLE = 'FAIBLE', _('Faible')
        MODEREE = 'MODEREE', _('Modérée')
        CRITIQUE = 'CRITIQUE', _('Critique')
    
    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', _('Ouvert')
        EN_COURS = 'EN_COURS', _('En cours')
        RESOLU = 'RESOLU', _('Résolu')
        FERME = 'FERME', _('Fermé')
    
    # Can be associated with operation (from Java model)
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, related_name='problemes', verbose_name=_('Opération'))
    
    # French field names to match Java model
    titre = models.CharField(max_length=200, verbose_name=_('Titre'))
    description = models.TextField(verbose_name=_('Description'))
    type = models.CharField(max_length=20, choices=Type.choices, verbose_name=_('Type'))
    gravite = models.CharField(max_length=20, choices=Gravite.choices, verbose_name=_('Gravité'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT, verbose_name=_('Statut'))
    
    date_detection = models.DateField(auto_now_add=True, verbose_name=_('Date de détection'))
    date_resolution = models.DateField(null=True, blank=True, verbose_name=_('Date de résolution'))
    
    signale_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='problemes_signales', verbose_name=_('Signalé par'))
    resolu_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='problemes_resolus', verbose_name=_('Résolu par'))
    
    solution_propose = models.TextField(blank=True, verbose_name=_('Solution proposée'))
    solution_implemente = models.TextField(blank=True, verbose_name=_('Solution implémentée'))
    impact_delai = models.PositiveIntegerField(null=True, blank=True, help_text=_('Impact délai en heures'), verbose_name=_('Impact délai'))
    impact_cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Impact coût'))
    
    def __str__(self):
        return f"{self.titre} - {self.get_gravite_display()}"
    
    class Meta:
        verbose_name = _('Problème')
        verbose_name_plural = _('Problèmes')
        ordering = ['-date_detection']


class DailyReport(models.Model):
    """Model for daily reports on well operations."""
    well = models.ForeignKey(Well, on_delete=models.CASCADE, related_name='daily_reports')
    operation = models.ForeignKey(
        WellOperation, 
        on_delete=models.CASCADE, 
        related_name='daily_reports',
        null=True, 
        blank=True
    )
    report_date = models.DateField()
    activities = models.TextField()
    progress = models.DecimalField(max_digits=5, decimal_places=2, help_text='Progress in percentage')
    issues = models.TextField(blank=True)
    solutions = models.TextField(blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='submitted_reports'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Report for {self.well.nom} on {self.report_date}"
    
    class Meta:
        ordering = ['-report_date']
        unique_together = ['well', 'report_date']
        verbose_name = _('Daily Report')
        verbose_name_plural = _('Daily Reports')


class WellDocument(models.Model):
    """Model for documents related to wells."""
    well = models.ForeignKey(Well, on_delete=models.CASCADE, related_name='documents')
    phase = models.ForeignKey('region_models.Phase', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    operation = models.ForeignKey(WellOperation, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    
    nom = models.CharField(max_length=255, verbose_name=_('Name'))  # French field name to match Java
    title = models.CharField(max_length=255, blank=True)  # Keep for backward compatibility
    type = models.CharField(max_length=100, verbose_name=_('Type'))
    document_type = models.CharField(max_length=100, blank=True)  # Keep for backward compatibility
    chemin = models.FileField(upload_to='well_documents/', verbose_name=_('File Path'))  # French field name to match Java
    file = models.FileField(upload_to='well_documents/', blank=True)  # Keep for backward compatibility
    taille = models.BigIntegerField(null=True, blank=True, verbose_name=_('Size'))  # French field name to match Java
    description = models.TextField(blank=True)
    est_public = models.BooleanField(default=False, verbose_name=_('Is Public'))  # French field name to match Java
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name=_('Upload Date'))  # French field name to match Java
    uploade_par = models.ForeignKey(  # French field name to match Java
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_documents_fr',
        verbose_name=_('Uploaded By')
    )
    uploaded_by = models.ForeignKey(  # Keep for backward compatibility
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_documents',
        null=True,
        blank=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Keep for backward compatibility
    
    def __str__(self):
        return f"{self.nom} - {self.well.nom}"
    
    class Meta:
        ordering = ['-date_upload']
        verbose_name = _('Well Document')
        verbose_name_plural = _('Well Documents')




class Region(models.Model):
    """Model representing a geographical region for well operations."""
    nom = models.CharField(max_length=100, verbose_name=_('Name'))
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    localisation = models.CharField(max_length=255, verbose_name=_('Location'))
    responsable = models.CharField(max_length=100, verbose_name=_('Responsible Person'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    
    def __str__(self):
        return f"{self.nom} ({self.code})"
    
    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ['nom']

class Forage(models.Model):
    """Model representing a drilling operation."""
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Cost'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Start Date'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('End Date'))
    puit = models.OneToOneField('wells.Well', on_delete=models.CASCADE, related_name='forage', verbose_name=_('Well'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    def __str__(self):
        return f"Forage - {self.puit.nom}"
    
    class Meta:
        verbose_name = _('Drilling Operation')
        verbose_name_plural = _('Drilling Operations')
        ordering = ['-date_debut']

class TypeOperation(models.Model):
    """Model representing types of operations that can be performed."""
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    nom = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    duree_estimee = models.PositiveIntegerField(null=True, blank=True, help_text=_('Estimated duration in hours'))
    cout_unitaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Unit Cost'))
    
    def __str__(self):
        return f"{self.code} - {self.nom}"
    
    class Meta:
        verbose_name = _('Operation Type')
        verbose_name_plural = _('Operation Types')
        ordering = ['code']

class Phase(models.Model):
    """Model representing phases of drilling operations."""
    
    class Diametre(models.TextChoices):
        POUCES_26 = '26"', _('26"')
        POUCES_16 = '16"', _('16"')
        POUCES_12_25 = '12_1_4"', _('12 1/4"')
        POUCES_8_5 = '8_1_2"', _('8 1/2"')
    
    forage = models.ForeignKey(Forage, on_delete=models.CASCADE, related_name='phases', verbose_name=_('Drilling Operation'))
    numero_phase = models.PositiveIntegerField(verbose_name=_('Phase Number'))
    diametre = models.CharField(max_length=10, choices=Diametre.choices, verbose_name=_('Diameter'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Planned vs Actual depths and dates (matching Java model)
    profondeur_prevue = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Planned Depth'))
    profondeur_reelle = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Actual Depth'))
    date_debut_prevue = models.DateField(null=True, blank=True, verbose_name=_('Planned Start Date'))
    date_debut_reelle = models.DateField(null=True, blank=True, verbose_name=_('Actual Start Date'))
    date_fin_prevue = models.DateField(null=True, blank=True, verbose_name=_('Planned End Date'))
    date_fin_reelle = models.DateField(null=True, blank=True, verbose_name=_('Actual End Date'))
    
    # Keep existing fields for backward compatibility
    profondeur_debut = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Start Depth'))
    profondeur_fin = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('End Depth'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Start Date'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('End Date'))
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Cost'))
    
    def __str__(self):
        return f"Phase {self.numero_phase} - {self.forage.puit.nom}"
    
    class Meta:
        verbose_name = _('Phase')
        verbose_name_plural = _('Phases')
        ordering = ['forage', 'numero_phase']
        unique_together = ['forage', 'numero_phase']


class Operation(models.Model):
    """Model representing operations performed during phases (matching Java Operation model)."""
    
    class Statut(models.TextChoices):
        PLANIFIE = 'PLANIFIE', _('Planifié')
        EN_COURS = 'EN_COURS', _('En cours')
        TERMINE = 'TERMINE', _('Terminé')
        PROBLEME = 'PROBLEME', _('Problème')
        ANNULE = 'ANNULE', _('Annulé')
    
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='operations', verbose_name=_('Phase'))
    type_operation = models.ForeignKey(TypeOperation, on_delete=models.CASCADE, verbose_name=_('Operation Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    date_debut = models.DateField(null=True, blank=True, verbose_name=_('Start Date'))
    date_fin = models.DateField(null=True, blank=True, verbose_name=_('End Date'))
    cout = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Cost'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PLANIFIE, verbose_name=_('Status'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_operations_detailed', verbose_name=_('Created By'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    
    def __str__(self):
        return f"{self.type_operation.nom} - Phase {self.phase.numero_phase}"
    
    class Meta:
        verbose_name = _('Operation')
        verbose_name_plural = _('Operations')
        ordering = ['-created_at']


class Reservoir(models.Model):
    """Model representing reservoir information."""
    nom = models.CharField(max_length=100, verbose_name=_('Name'))
    profondeur = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_('Depth'))
    pression = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name=_('Pressure'))
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_('Temperature'))
    type_fluide = models.CharField(max_length=50, verbose_name=_('Fluid Type'))
    puit = models.ForeignKey('wells.Well', on_delete=models.CASCADE, related_name='reservoirs', verbose_name=_('Well'))
      def __str__(self):
        return f"{self.nom} - {self.puit.nom}"
    
    class Meta:
        verbose_name = _('Reservoir')
        verbose_name_plural = _('Reservoirs')
        ordering = ['profondeur']

class Probleme(models.Model):
    """Model representing problems and incidents."""
    
    class Type(models.TextChoices):
        DELAI = 'DELAI', _('Délai')
        COUT = 'COUT', _('Coût')
        SECURITE = 'SECURITE', _('Sécurité')
        TECHNIQUE = 'TECHNIQUE', _('Technique')
    
    class Gravite(models.TextChoices):
        FAIBLE = 'FAIBLE', _('Faible')
        MODEREE = 'MODEREE', _('Modérée')
        CRITIQUE = 'CRITIQUE', _('Critique')
    
    class Statut(models.TextChoices):
        OUVERT = 'OUVERT', _('Ouvert')
        EN_COURS = 'EN_COURS', _('En cours')
        RESOLU = 'RESOLU', _('Résolu')
        FERME = 'FERME', _('Fermé')
    
    # Can be associated with either a phase, operation, or well operation
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, null=True, blank=True, related_name='problemes', verbose_name=_('Phase'))
    operation = models.ForeignKey(Operation, on_delete=models.CASCADE, null=True, blank=True, related_name='problemes', verbose_name=_('Operation'))
    well_operation = models.ForeignKey('wells.WellOperation', on_delete=models.CASCADE, null=True, blank=True, related_name='problemes', verbose_name=_('Well Operation'))
    
    titre = models.CharField(max_length=200, verbose_name=_('Title'))
    description = models.TextField(verbose_name=_('Description'))
    type_probleme = models.CharField(max_length=20, choices=Type.choices, verbose_name=_('Problem Type'))
    gravite = models.CharField(max_length=20, choices=Gravite.choices, verbose_name=_('Severity'))
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT, verbose_name=_('Status'))
    
    date_detection = models.DateTimeField(auto_now_add=True, verbose_name=_('Detection Date'))
    date_resolution = models.DateTimeField(null=True, blank=True, verbose_name=_('Resolution Date'))
    
    detecte_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='problemes_detectes', verbose_name=_('Detected By'))
    assigne_a = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='problemes_assignes', verbose_name=_('Assigned To'))
    
    solution = models.TextField(blank=True, verbose_name=_('Solution'))
    cout_impact = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_('Impact Cost'))
    delai_impact = models.PositiveIntegerField(null=True, blank=True, help_text=_('Impact delay in hours'), verbose_name=_('Delay Impact'))
    
    def __str__(self):
        return f"{self.titre} - {self.get_gravite_display()}"
    
    class Meta:
        verbose_name = _('Problem')
        verbose_name_plural = _('Problems')
        ordering = ['-date_detection']

