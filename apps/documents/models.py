from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from apps.wells.models import Well, Phase, Operation
import os


class DocumentPuits(models.Model):
    """Modèle pour les documents liés aux puits avec noms français."""
    
    class TypeDocument(models.TextChoices):
        RAPPORT_QUOTIDIEN = 'RAPPORT_QUOTIDIEN', _('Rapport quotidien')
        PLANIFICATION = 'PLANIFICATION', _('Planification')
        TECHNIQUE = 'TECHNIQUE', _('Technique')
        SECURITE = 'SECURITE', _('Sécurité')
        LEGAL = 'LEGAL', _('Légal')
        FINANCIER = 'FINANCIER', _('Financier')
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
        QUALITE = 'QUALITE', _('Qualité')
    
    class StatutDocument(models.TextChoices):
        BROUILLON = 'BROUILLON', _('Brouillon')
        EN_REVISION = 'EN_REVISION', _('En révision')
        APPROUVE = 'APPROUVE', _('Approuvé')
        ARCHIVE = 'ARCHIVE', _('Archivé')
        REJETE = 'REJETE', _('Rejeté')
    
    # Relations
    puits = models.ForeignKey(
        Well, 
        on_delete=models.CASCADE, 
        related_name='documents_puits', 
        verbose_name=_('Puits')
    )
    phase = models.ForeignKey(
        Phase, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='documents_phase', 
        verbose_name=_('Phase')
    )
    operation = models.ForeignKey(
        Operation, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='documents_operation', 
        verbose_name=_('Opération')
    )
    
    # Informations du document
    nom_document = models.CharField(max_length=255, verbose_name=_('Nom du document'))
    type_document = models.CharField(
        max_length=20, 
        choices=TypeDocument.choices, 
        verbose_name=_('Type de document')
    )
    fichier = models.FileField(
        upload_to='documents_puits/',
        verbose_name=_('Fichier'),
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'png', 'jpg', 'jpeg'])]
    )
    taille_fichier = models.BigIntegerField(
        null=True, 
        blank=True, 
        verbose_name=_('Taille du fichier (en octets)')
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    mots_cles = models.CharField(max_length=500, blank=True, verbose_name=_('Mots-clés'))
    
    # Contrôle d'accès
    est_public = models.BooleanField(default=False, verbose_name=_('Document public'))
    est_confidentiel = models.BooleanField(default=False, verbose_name=_('Document confidentiel'))
    
    # Gestion des versions
    numero_version = models.CharField(max_length=20, default='1.0', verbose_name=_('Numéro de version'))
    version_precedente = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Version précédente')
    )
    
    # Workflow d'approbation
    statut = models.CharField(
        max_length=20,
        choices=StatutDocument.choices,
        default=StatutDocument.BROUILLON,
        verbose_name=_('Statut')
    )
    est_approuve = models.BooleanField(default=False, verbose_name=_('Est approuvé'))
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_approuves',
        verbose_name=_('Approuvé par')
    )
    date_approbation = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_('Date d\'approbation')
    )
    commentaires_approbation = models.TextField(
        blank=True, 
        verbose_name=_('Commentaires d\'approbation')
    )
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documents_crees',
        verbose_name=_('Créé par')
    )
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='documents_modifies',
        verbose_name=_('Modifié par')
    )
    
    # Métadonnées
    date_validite_debut = models.DateField(null=True, blank=True, verbose_name=_('Date de début de validité'))
    date_validite_fin = models.DateField(null=True, blank=True, verbose_name=_('Date de fin de validité'))
    nombre_telechargements = models.PositiveIntegerField(default=0, verbose_name=_('Nombre de téléchargements'))
    
    def save(self, *args, **kwargs):
        if self.fichier:
            self.taille_fichier = self.fichier.size
        super().save(*args, **kwargs)
    
    def est_valide(self):
        """Vérifie si le document est encore valide."""
        if self.date_validite_fin:
            return timezone.now().date() <= self.date_validite_fin
        return True
    
    def extension_fichier(self):
        """Retourne l'extension du fichier."""
        if self.fichier:
            return os.path.splitext(self.fichier.name)[1][1:].upper()
        return ''
    
    def __str__(self):
        return f"{self.nom_document} - {self.puits.nom if hasattr(self.puits, 'nom') else self.puits.name}"
    
    class Meta:
        verbose_name = _('Document de puits')
        verbose_name_plural = _('Documents de puits')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['puits', 'type_document']),
            models.Index(fields=['statut']),
            models.Index(fields=['date_creation']),
        ]


class RapportQuotidien(models.Model):
    """Modèle pour les rapports quotidiens avec noms français."""
    
    class StatutRapport(models.TextChoices):
        BROUILLON = 'BROUILLON', _('Brouillon')
        SOUMIS = 'SOUMIS', _('Soumis')
        VALIDE = 'VALIDE', _('Validé')
        REJETE = 'REJETE', _('Rejeté')
    
    # Relations
    puits = models.ForeignKey(Well, on_delete=models.CASCADE, verbose_name=_('Puits'))
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Phase'))
    
    # Informations de base
    date_rapport = models.DateField(verbose_name=_('Date du rapport'))
    numero_rapport = models.CharField(max_length=50, blank=True, verbose_name=_('Numéro de rapport'))
    fichier_rapport = models.FileField(
        upload_to='rapports_quotidiens/',
        verbose_name=_('Fichier du rapport'),
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    
    # Contenu du rapport
    activites_realisees = models.TextField(verbose_name=_('Activités réalisées'))
    objectifs_jour = models.TextField(blank=True, verbose_name=_('Objectifs du jour'))
    objectifs_lendemain = models.TextField(blank=True, verbose_name=_('Objectifs du lendemain'))
    problemes_rencontres = models.TextField(blank=True, verbose_name=_('Problèmes rencontrés'))
    solutions_appliquees = models.TextField(blank=True, verbose_name=_('Solutions appliquées'))
    
    # Indicateurs de performance
    avancement_pourcentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Avancement en pourcentage')
    )
    heures_travaillees = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        verbose_name=_('Heures travaillées')
    )
    nombre_personnel = models.PositiveIntegerField(default=0, verbose_name=_('Nombre de personnel'))
    
    # Conditions opérationnelles
    conditions_meteo = models.CharField(max_length=100, blank=True, verbose_name=_('Conditions météo'))
    temperature_min = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Température minimale (°C)')
    )
    temperature_max = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Température maximale (°C)')
    )
    vitesse_vent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True, 
        verbose_name=_('Vitesse du vent (km/h)')
    )
    
    # Équipements et sécurité
    statut_equipement = models.TextField(blank=True, verbose_name=_('Statut des équipements'))
    incidents_securite = models.TextField(blank=True, verbose_name=_('Incidents de sécurité'))
    mesures_securite_prises = models.TextField(blank=True, verbose_name=_('Mesures de sécurité prises'))
    
    # Workflow et validation
    statut = models.CharField(
        max_length=20,
        choices=StatutRapport.choices,
        default=StatutRapport.BROUILLON,
        verbose_name=_('Statut du rapport')
    )
    valide_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_valides',
        verbose_name=_('Validé par')
    )
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de validation'))
    commentaires_validation = models.TextField(blank=True, verbose_name=_('Commentaires de validation'))
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    soumis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='rapports_soumis',
        verbose_name=_('Soumis par')
    )
    
    def save(self, *args, **kwargs):
        if not self.numero_rapport:
            self.numero_rapport = f"RQ-{self.puits.id}-{self.date_rapport.strftime('%Y%m%d')}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Rapport quotidien - {self.puits.nom if hasattr(self.puits, 'nom') else self.puits.name} - {self.date_rapport}"
    
    class Meta:
        verbose_name = _('Rapport quotidien')
        verbose_name_plural = _('Rapports quotidiens')
        ordering = ['-date_rapport']
        unique_together = ['puits', 'date_rapport']
        indexes = [
            models.Index(fields=['puits', 'date_rapport']),
            models.Index(fields=['statut']),
        ]


class RapportPlanification(models.Model):
    """Modèle pour les rapports de planification de projet avec noms français."""
    
    class StatutPlanification(models.TextChoices):
        BROUILLON = 'BROUILLON', _('Brouillon')
        EN_REVISION = 'EN_REVISION', _('En révision')
        APPROUVE = 'APPROUVE', _('Approuvé')
        EN_COURS = 'EN_COURS', _('En cours')
        TERMINE = 'TERMINE', _('Terminé')
        ANNULE = 'ANNULE', _('Annulé')
    
    class PrioriteProjet(models.TextChoices):
        BASSE = 'BASSE', _('Basse')
        NORMALE = 'NORMALE', _('Normale')
        HAUTE = 'HAUTE', _('Haute')
        CRITIQUE = 'CRITIQUE', _('Critique')
    
    # Relations
    puits = models.ForeignKey(Well, on_delete=models.CASCADE, verbose_name=_('Puits'))
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Phase'))
    
    # Informations du projet
    nom_projet = models.CharField(max_length=200, verbose_name=_('Nom du projet'))
    code_projet = models.CharField(max_length=50, unique=True, verbose_name=_('Code du projet'))
    fichier_plan = models.FileField(
        upload_to='rapports_planification/',
        verbose_name=_('Fichier de planification'),
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'mpp', 'xlsx'])]
    )
    
    # Planification temporelle
    date_debut_prevue = models.DateField(verbose_name=_('Date de début prévue'))
    date_fin_prevue = models.DateField(verbose_name=_('Date de fin prévue'))
    date_debut_reelle = models.DateField(null=True, blank=True, verbose_name=_('Date de début réelle'))
    date_fin_reelle = models.DateField(null=True, blank=True, verbose_name=_('Date de fin réelle'))
    duree_prevue_jours = models.PositiveIntegerField(verbose_name=_('Durée prévue (jours)'))
    
    # Budget et ressources
    budget_prevu = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Budget prévu'))
    budget_consomme = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=0, 
        verbose_name=_('Budget consommé')
    )
    devise = models.CharField(max_length=3, default='DZD', verbose_name=_('Devise'))
    
    # Description et objectifs
    description_projet = models.TextField(verbose_name=_('Description du projet'))
    objectifs = models.TextField(verbose_name=_('Objectifs'))
    livrables_attendus = models.TextField(verbose_name=_('Livrables attendus'))
    
    # Gestion des risques
    risques_identifies = models.TextField(blank=True, verbose_name=_('Risques identifiés'))
    mesures_mitigation = models.TextField(blank=True, verbose_name=_('Mesures de mitigation'))
    niveau_risque_global = models.CharField(
        max_length=10,
        choices=[
            ('FAIBLE', _('Faible')),
            ('MOYEN', _('Moyen')),
            ('ELEVE', _('Élevé')),
            ('CRITIQUE', _('Critique')),
        ],
        default='MOYEN',
        verbose_name=_('Niveau de risque global')
    )
    
    # Ressources
    ressources_humaines = models.TextField(blank=True, verbose_name=_('Ressources humaines'))
    equipements_requis = models.TextField(blank=True, verbose_name=_('Équipements requis'))
    materiaux_necessaires = models.TextField(blank=True, verbose_name=_('Matériaux nécessaires'))
    
    # Jalons et suivi
    jalons_principaux = models.JSONField(null=True, blank=True, verbose_name=_('Jalons principaux'))
    pourcentage_avancement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('Pourcentage d\'avancement')
    )
    
    # Priorité et statut
    priorite = models.CharField(
        max_length=20,
        choices=PrioriteProjet.choices,
        default=PrioriteProjet.NORMALE,
        verbose_name=_('Priorité')
    )
    statut_planification = models.CharField(
        max_length=20,
        choices=StatutPlanification.choices,
        default=StatutPlanification.BROUILLON,
        verbose_name=_('Statut de planification')
    )
    
    # Approbation
    approuve_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans_approuves',
        verbose_name=_('Approuvé par')
    )
    date_approbation = models.DateTimeField(null=True, blank=True, verbose_name=_('Date d\'approbation'))
    commentaires_approbation = models.TextField(blank=True, verbose_name=_('Commentaires d\'approbation'))
    
    # Audit
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='plans_crees',
        verbose_name=_('Créé par')
    )
    
    def save(self, *args, **kwargs):
        if not self.code_projet:
            self.code_projet = f"PROJ-{self.puits.id}-{timezone.now().strftime('%Y%m%d%H%M')}"
        super().save(*args, **kwargs)
    
    def duree_reelle_jours(self):
        """Calcule la durée réelle du projet en jours."""
        if self.date_debut_reelle and self.date_fin_reelle:
            return (self.date_fin_reelle - self.date_debut_reelle).days
        return None
    
    def est_en_retard(self):
        """Vérifie si le projet est en retard."""
        if self.date_fin_reelle:
            return self.date_fin_reelle > self.date_fin_prevue
        return timezone.now().date() > self.date_fin_prevue
    
    def pourcentage_budget_consomme(self):
        """Calcule le pourcentage de budget consommé."""
        if self.budget_prevu > 0:
            return (self.budget_consomme / self.budget_prevu) * 100
        return 0
    
    def __str__(self):
        return f"Plan {self.nom_projet} - {self.puits.nom if hasattr(self.puits, 'nom') else self.puits.name}"
    
    class Meta:
        verbose_name = _('Rapport de planification')
        verbose_name_plural = _('Rapports de planification')
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['puits', 'statut_planification']),
            models.Index(fields=['date_debut_prevue']),
            models.Index(fields=['priorite']),
        ]


class ModeleDocument(models.Model):
    """Modèle pour les templates de documents."""
    
    class TypeModele(models.TextChoices):
        RAPPORT_QUOTIDIEN = 'RAPPORT_QUOTIDIEN', _('Rapport quotidien')
        PLANIFICATION = 'PLANIFICATION', _('Planification')
        TECHNIQUE = 'TECHNIQUE', _('Technique')
        SECURITE = 'SECURITE', _('Sécurité')
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
    
    # Informations du template
    nom_modele = models.CharField(max_length=100, verbose_name=_('Nom du modèle'))
    code_modele = models.CharField(max_length=50, unique=True, verbose_name=_('Code du modèle'))
    type_modele = models.CharField(
        max_length=50,
        choices=TypeModele.choices,
        verbose_name=_('Type de modèle')
    )
    fichier_modele = models.FileField(
        upload_to='modeles_documents/',
        verbose_name=_('Fichier modèle'),
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'])]
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    instructions_utilisation = models.TextField(blank=True, verbose_name=_('Instructions d\'utilisation'))
    
    # Configuration du template
    champs_variables = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name=_('Champs variables'),
        help_text=_('Liste des champs qui peuvent être personnalisés')
    )
    champs_obligatoires = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Champs obligatoires'),
        help_text=_('Liste des champs qui doivent être renseignés')
    )
    
    # Statistiques d'utilisation
    nombre_utilisations = models.PositiveIntegerField(default=0, verbose_name=_('Nombre d\'utilisations'))
    derniere_utilisation = models.DateTimeField(null=True, blank=True, verbose_name=_('Dernière utilisation'))
    
    # Version et statut
    version = models.CharField(max_length=10, default='1.0', verbose_name=_('Version'))
    est_actif = models.BooleanField(default=True, verbose_name=_('Est actif'))
    est_par_defaut = models.BooleanField(default=False, verbose_name=_('Modèle par défaut'))
    
    # Permissions
    est_public = models.BooleanField(default=True, verbose_name=_('Modèle public'))
    utilisateurs_autorises = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='modeles_autorises',
        verbose_name=_('Utilisateurs autorisés')
    )
    
    # Audit
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='modeles_crees',
        verbose_name=_('Créé par')
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    
    def save(self, *args, **kwargs):
        if not self.code_modele:
            self.code_modele = f"TPL-{self.type_modele}-{timezone.now().strftime('%Y%m%d%H%M')}"
        super().save(*args, **kwargs)
    
    def incrementer_utilisation(self):
        """Incrémente le compteur d'utilisation."""
        self.nombre_utilisations += 1
        self.derniere_utilisation = timezone.now()
        self.save(update_fields=['nombre_utilisations', 'derniere_utilisation'])
    
    def __str__(self):
        return f"Modèle {self.nom_modele} v{self.version}"
    
    class Meta:
        verbose_name = _('Modèle de document')
        verbose_name_plural = _('Modèles de documents')
        ordering = ['nom_modele', '-version']
        unique_together = ['type_modele', 'est_par_defaut']


class ArchiveDocument(models.Model):
    """Modèle pour les documents archivés."""
    
    class RaisonArchivage(models.TextChoices):
        OBSOLETE = 'OBSOLETE', _('Document obsolète')
        REMPLACE = 'REMPLACE', _('Document remplacé')
        EXPIRE = 'EXPIRE', _('Document expiré')
        DEMANDE_UTILISATEUR = 'DEMANDE_UTILISATEUR', _('Demande utilisateur')
        NETTOYAGE = 'NETTOYAGE', _('Nettoyage automatique')
        CONFORME_POLITIQUE = 'CONFORME_POLITIQUE', _('Conformité à la politique')
    
    # Document archivé
    document_original = models.OneToOneField(
        DocumentPuits,
        on_delete=models.CASCADE,
        verbose_name=_('Document original')
    )
    
    # Informations d'archivage
    raison_archivage = models.CharField(
        max_length=50,
        choices=RaisonArchivage.choices,
        verbose_name=_('Raison d\'archivage')
    )
    description_archivage = models.TextField(blank=True, verbose_name=_('Description de l\'archivage'))
    date_archivage = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'archivage'))
    archive_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documents_archives',
        verbose_name=_('Archivé par')
    )
    
    # Gestion de la rétention
    peut_etre_restaure = models.BooleanField(default=True, verbose_name=_('Peut être restauré'))
    date_suppression_prevue = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Date de suppression prévue')
    )
    duree_retention_jours = models.PositiveIntegerField(
        default=365,
        verbose_name=_('Durée de rétention (jours)')
    )
    
    # Informations de sauvegarde
    chemin_sauvegarde = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Chemin de sauvegarde')
    )
    taille_archive = models.BigIntegerField(null=True, blank=True, verbose_name=_('Taille de l\'archive'))
    checksum_archive = models.CharField(max_length=64, blank=True, verbose_name=_('Checksum de l\'archive'))
    
    def save(self, *args, **kwargs):
        if not self.date_suppression_prevue and self.duree_retention_jours:
            self.date_suppression_prevue = timezone.now().date() + timezone.timedelta(days=self.duree_retention_jours)
        super().save(*args, **kwargs)
    
    def peut_etre_supprime(self):
        """Vérifie si l'archive peut être supprimée."""
        if self.date_suppression_prevue:
            return timezone.now().date() >= self.date_suppression_prevue
        return False
    
    def __str__(self):
        return f"Archive - {self.document_original.nom_document}"
    
    class Meta:
        verbose_name = _('Archive de document')
        verbose_name_plural = _('Archives de documents')
        ordering = ['-date_archivage']
        indexes = [
            models.Index(fields=['date_suppression_prevue']),
            models.Index(fields=['raison_archivage']),
        ]
