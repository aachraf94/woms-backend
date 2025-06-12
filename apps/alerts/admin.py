from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count
from .models import Notification, Incident, RegleAlerte, JournalAction


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administration des notifications"""
    list_display = [
        'titre', 'type_notification', 'destinataire', 'lu',
        'date_creation', 'colored_status'
    ]
    list_filter = [
        'type_notification', 'lu', 'date_creation',
        ('destinataire', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['titre', 'message', 'destinataire__username']
    readonly_fields = ['date_creation', 'date_lecture']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('type_notification', 'titre', 'message', 'destinataire')
        }),
        ('État', {
            'fields': ('lu', 'date_lecture')
        }),
        ('Métadonnées', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_comme_lues', 'marquer_comme_non_lues']

    def colored_status(self, obj):
        """Affichage coloré du statut de lecture"""
        if obj.lu:
            return format_html('<span style="color: green;">✓ Lu</span>')
        else:
            return format_html('<span style="color: red;">✗ Non lu</span>')
    colored_status.short_description = 'Statut'

    def marquer_comme_lues(self, request, queryset):
        """Action pour marquer les notifications comme lues"""
        updated = queryset.update(lu=True, date_lecture=timezone.now())
        self.message_user(request, f'{updated} notifications marquées comme lues.')
    marquer_comme_lues.short_description = 'Marquer comme lues'

    def marquer_comme_non_lues(self, request, queryset):
        """Action pour marquer les notifications comme non lues"""
        updated = queryset.update(lu=False, date_lecture=None)
        self.message_user(request, f'{updated} notifications marquées comme non lues.')
    marquer_comme_non_lues.short_description = 'Marquer comme non lues'


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    """Administration des incidents"""
    list_display = [
        'titre', 'type_incident', 'statut', 'priorite_colored',
        'rapporte_par', 'assigne_a', 'date_creation'
    ]
    list_filter = [
        'type_incident', 'statut', 'priorite', 'date_creation',
        ('rapporte_par', admin.RelatedOnlyFieldListFilter),
        ('assigne_a', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['titre', 'description', 'rapporte_par__username']
    readonly_fields = ['date_creation', 'date_mise_a_jour']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('titre', 'type_incident', 'description', 'priorite')
        }),
        ('Assignation', {
            'fields': ('rapporte_par', 'assigne_a', 'statut')
        }),
        ('Résolution', {
            'fields': ('date_resolution',)
        }),
        ('Métadonnées', {
            'fields': ('date_creation', 'date_mise_a_jour'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['marquer_en_cours', 'marquer_resolu']

    def priorite_colored(self, obj):
        """Affichage coloré de la priorité"""
        colors = {1: 'blue', 2: 'green', 3: 'orange', 4: 'red'}
        color = colors.get(obj.priorite, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priorite_display()
        )
    priorite_colored.short_description = 'Priorité'

    def marquer_en_cours(self, request, queryset):
        """Action pour marquer les incidents comme en cours"""
        updated = queryset.update(statut='en_cours')
        self.message_user(request, f'{updated} incidents marqués comme en cours.')
    marquer_en_cours.short_description = 'Marquer comme en cours'

    def marquer_resolu(self, request, queryset):
        """Action pour marquer les incidents comme résolus"""
        updated = queryset.update(statut='resolu', date_resolution=timezone.now())
        self.message_user(request, f'{updated} incidents marqués comme résolus.')
    marquer_resolu.short_description = 'Marquer comme résolus'


@admin.register(RegleAlerte)
class RegleAlerteAdmin(admin.ModelAdmin):
    """Administration des règles d'alerte"""
    list_display = [
        'nom', 'type_capteur', 'seuil_declenchement', 'active_colored',
        'creee_par', 'date_creation'
    ]
    list_filter = [
        'active', 'type_capteur', 'date_creation',
        ('creee_par', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['nom', 'description', 'condition']
    readonly_fields = ['date_creation', 'date_mise_a_jour']
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'description', 'active')
        }),
        ('Configuration', {
            'fields': ('condition', 'action', 'seuil_declenchement', 'type_capteur')
        }),
        ('Métadonnées', {
            'fields': ('creee_par', 'date_creation', 'date_mise_a_jour'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activer_regles', 'desactiver_regles']

    def active_colored(self, obj):
        """Affichage coloré du statut actif"""
        if obj.active:
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    active_colored.short_description = 'État'

    def activer_regles(self, request, queryset):
        """Action pour activer les règles"""
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} règles activées.')
    activer_regles.short_description = 'Activer les règles'

    def desactiver_regles(self, request, queryset):
        """Action pour désactiver les règles"""
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} règles désactivées.')
    desactiver_regles.short_description = 'Désactiver les règles'


@admin.register(JournalAction)
class JournalActionAdmin(admin.ModelAdmin):
    """Administration du journal d'actions"""
    list_display = [
        'action', 'utilisateur', 'incident_lie', 'adresse_ip', 'horodatage'
    ]
    list_filter = [
        'horodatage',
        ('utilisateur', admin.RelatedOnlyFieldListFilter),
        ('incident_lie', admin.RelatedOnlyFieldListFilter)
    ]
    search_fields = ['action', 'details', 'utilisateur__username']
    readonly_fields = ['horodatage']
    date_hierarchy = 'horodatage'
    
    fieldsets = (
        ('Action', {
            'fields': ('action', 'details', 'utilisateur', 'incident_lie')
        }),
        ('Informations techniques', {
            'fields': ('adresse_ip', 'user_agent', 'horodatage'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Désactiver l'ajout manuel d'entrées dans le journal"""
        return False

    def has_change_permission(self, request, obj=None):
        """Désactiver la modification des entrées du journal"""
        return False


# Configuration du site admin
admin.site.site_header = "Administration WOMS - Alertes"
admin.site.site_title = "WOMS Admin"
admin.site.index_title = "Gestion des Alertes et Notifications"
