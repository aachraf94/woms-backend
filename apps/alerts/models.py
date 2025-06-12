from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class TypeNotification(models.TextChoices):
    """Choix pour les types de notifications"""
    INFO = 'info', _('Information')
    ALERTE = 'alerte', _('Alerte')
    URGENCE = 'urgence', _('Urgence')
    MAINTENANCE = 'maintenance', _('Maintenance')


class StatutIncident(models.TextChoices):
    """Choix pour les statuts d'incidents"""
    NOUVEAU = 'nouveau', _('Nouveau')
    EN_COURS = 'en_cours', _('En cours')
    RESOLU = 'resolu', _('Résolu')
    FERME = 'ferme', _('Fermé')


class TypeIncident(models.TextChoices):
    """Choix pour les types d'incidents"""
    PANNE_EQUIPEMENT = 'panne_equipement', _('Panne équipement')
    PROBLEME_RESEAU = 'probleme_reseau', _('Problème réseau')
    DEFAILLANCE_CAPTEUR = 'defaillance_capteur', _('Défaillance capteur')
    MAINTENANCE_URGENTE = 'maintenance_urgente', _('Maintenance urgente')
    AUTRE = 'autre', _('Autre')


class Notification(models.Model):
    """
    Modèle pour représenter une notification système.
    """
    type_notification = models.CharField(
        max_length=50,
        choices=TypeNotification.choices,
        default=TypeNotification.INFO,
        verbose_name=_("Type de notification")
    )
    titre = models.CharField(max_length=255, verbose_name=_("Titre"))
    message = models.TextField(verbose_name=_("Message"))
    destinataire = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_recues',
        verbose_name=_("Destinataire")
    )
    lu = models.BooleanField(default=False, verbose_name=_("Lu"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_lecture = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de lecture"))

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.destinataire.username}"


class Incident(models.Model):
    """
    Modèle pour représenter un incident système.
    """
    titre = models.CharField(max_length=255, verbose_name=_("Titre"))
    type_incident = models.CharField(
        max_length=50,
        choices=TypeIncident.choices,
        verbose_name=_("Type d'incident")
    )
    description = models.TextField(verbose_name=_("Description"))
    statut = models.CharField(
        max_length=50,
        choices=StatutIncident.choices,
        default=StatutIncident.NOUVEAU,
        verbose_name=_("Statut")
    )
    priorite = models.IntegerField(
        choices=[(1, _('Basse')), (2, _('Normale')), (3, _('Haute')), (4, _('Critique'))],
        default=2,
        verbose_name=_("Priorité")
    )
    rapporte_par = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='incidents_rapportes',
        verbose_name=_("Rapporté par")
    )
    assigne_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents_assignes',
        verbose_name=_("Assigné à")
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))
    date_resolution = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de résolution"))

    class Meta:
        verbose_name = _("Incident")
        verbose_name_plural = _("Incidents")
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.titre} - {self.get_statut_display()}"


class RegleAlerte(models.Model):
    """
    Modèle pour représenter une règle d'alerte automatique.
    """
    nom = models.CharField(max_length=255, verbose_name=_("Nom de la règle"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    condition = models.TextField(verbose_name=_("Condition de déclenchement"))
    action = models.TextField(verbose_name=_("Action à effectuer"))
    active = models.BooleanField(default=True, verbose_name=_("Active"))
    seuil_declenchement = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Seuil de déclenchement")
    )
    type_capteur = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Type de capteur concerné")
    )
    creee_par = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='regles_creees',
        verbose_name=_("Créée par")
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_mise_a_jour = models.DateTimeField(auto_now=True, verbose_name=_("Date de mise à jour"))

    class Meta:
        verbose_name = _("Règle d'alerte")
        verbose_name_plural = _("Règles d'alerte")
        ordering = ['nom']

    def __str__(self):
        return self.nom


class JournalAction(models.Model):
    """
    Modèle pour représenter un journal des actions utilisateur.
    """
    action = models.CharField(max_length=255, verbose_name=_("Action"))
    details = models.TextField(blank=True, verbose_name=_("Détails"))
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name=_("Adresse IP"))
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))
    horodatage = models.DateTimeField(auto_now_add=True, verbose_name=_("Horodatage"))
    utilisateur = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='actions_effectuees',
        verbose_name=_("Utilisateur")
    )
    incident_lie = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_associees',
        verbose_name=_("Incident lié")
    )

    class Meta:
        verbose_name = _("Journal d'action")
        verbose_name_plural = _("Journaux d'actions")
        ordering = ['-horodatage']

    def __str__(self):
        return f"{self.action} - {self.utilisateur.username} - {self.horodatage}"