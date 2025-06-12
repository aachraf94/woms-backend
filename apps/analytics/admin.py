from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    JeuDonneesAnalytiques, AnalyseEcart, InteractionAssistantIA,
    IndicateurPerformance, AnalyseReservoir, TableauBordKPI,
    AnalysePredictive, AlerteAnalytique
)


@admin.register(JeuDonneesAnalytiques)
class JeuDonneesAnalytiquesAdmin(admin.ModelAdmin):
    list_display = ['nom_jeu_donnees', 'puits', 'type_donnees', 'taille_donnees_mb', 'source_donnees', 'date_creation']
    list_filter = ['type_donnees', 'source_donnees', 'date_creation']
    search_fields = ['nom_jeu_donnees', 'puits__nom', 'source_donnees']
    readonly_fields = ['date_creation', 'date_modification', 'taille_donnees_mb']
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('nom_jeu_donnees', 'puits', 'type_donnees', 'source_donnees')
        }),
        (_('Données'), {
            'fields': ('donnees', 'taille_donnees', 'taille_donnees_mb')
        }),
        (_('Métadonnées'), {
            'fields': ('cree_par', 'date_creation', 'date_modification')
        }),
    )
    
    def taille_donnees_mb(self, obj):
        if obj.taille_donnees:
            return f"{obj.taille_donnees / (1024 * 1024):.2f} MB"
        return "-"
    taille_donnees_mb.short_description = _('Taille (MB)')


@admin.register(AnalyseEcart)
class AnalyseEcartAdmin(admin.ModelAdmin):
    list_display = ['phase', 'type_indicateur', 'valeur_planifiee', 'valeur_reelle', 'pourcentage_ecart_display', 'niveau_criticite', 'date_analyse']
    list_filter = ['type_indicateur', 'niveau_criticite', 'date_analyse']
    search_fields = ['phase__nom', 'type_indicateur', 'commentaire']
    readonly_fields = ['ecart_absolu', 'pourcentage_ecart', 'niveau_criticite', 'date_analyse']
    fieldsets = (
        (_('Phase et Indicateur'), {
            'fields': ('phase', 'type_indicateur')
        }),
        (_('Valeurs'), {
            'fields': ('valeur_planifiee', 'valeur_reelle', 'ecart_absolu', 'pourcentage_ecart')
        }),
        (_('Analyse'), {
            'fields': ('niveau_criticite', 'commentaire', 'actions_correctives')
        }),
        (_('Métadonnées'), {
            'fields': ('analyseur', 'date_analyse')
        }),
    )
    
    def pourcentage_ecart_display(self, obj):
        if obj.pourcentage_ecart:
            color = 'red' if abs(obj.pourcentage_ecart) > 25 else 'orange' if abs(obj.pourcentage_ecart) > 10 else 'green'
            return format_html(
                '<span style="color: {};">{:.2f}%</span>',
                color, obj.pourcentage_ecart
            )
        return "-"
    pourcentage_ecart_display.short_description = _('Écart (%)')


@admin.register(InteractionAssistantIA)
class InteractionAssistantIAAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'type_requete', 'statut', 'score_pertinence', 'temps_traitement_display', 'horodatage_creation']
    list_filter = ['type_requete', 'statut', 'horodatage_creation']
    search_fields = ['utilisateur__username', 'requete', 'type_requete']
    readonly_fields = ['horodatage_creation', 'horodatage_reponse', 'temps_traitement_display']
    fieldsets = (
        (_('Interaction'), {
            'fields': ('utilisateur', 'type_requete', 'puits_associe')
        }),
        (_('Contenu'), {
            'fields': ('requete', 'reponse')
        }),
        (_('Performance'), {
            'fields': ('score_pertinence', 'temps_traitement', 'temps_traitement_display', 'statut')
        }),
        (_('Métadonnées'), {
            'fields': ('metadonnees', 'horodatage_creation', 'horodatage_reponse')
        }),
    )
    
    def temps_traitement_display(self, obj):
        if obj.temps_traitement:
            return f"{obj.temps_traitement.total_seconds():.2f}s"
        return "-"
    temps_traitement_display.short_description = _('Temps de traitement')


@admin.register(IndicateurPerformance)
class IndicateurPerformanceAdmin(admin.ModelAdmin):
    list_display = ['operation', 'type_indicateur', 'valeur_prevue', 'valeur_reelle', 'pourcentage_realisation_display', 'statut', 'date_mesure']
    list_filter = ['statut', 'date_mesure', 'type_indicateur__nom']
    search_fields = ['operation__nom', 'type_indicateur__nom', 'commentaire']
    readonly_fields = ['ecart_performance', 'pourcentage_realisation']
    fieldsets = (
        (_('Opération et Indicateur'), {
            'fields': ('operation', 'type_indicateur')
        }),
        (_('Valeurs'), {
            'fields': ('valeur_prevue', 'valeur_reelle', 'ecart_performance', 'pourcentage_realisation')
        }),
        (_('Planification'), {
            'fields': ('date_prevue', 'date_mesure', 'statut')
        }),
        (_('Détails'), {
            'fields': ('commentaire', 'mesure_par')
        }),
    )
    
    def pourcentage_realisation_display(self, obj):
        if obj.pourcentage_realisation:
            color = 'green' if obj.pourcentage_realisation >= 90 else 'orange' if obj.pourcentage_realisation >= 75 else 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.pourcentage_realisation
            )
        return "-"
    pourcentage_realisation_display.short_description = _('Réalisation (%)')


@admin.register(AnalyseReservoir)
class AnalyseReservoirAdmin(admin.ModelAdmin):
    list_display = ['nom_analyse', 'puits', 'nature_fluide', 'debit_estime', 'statut_analyse', 'date_analyse']
    list_filter = ['nature_fluide', 'statut_analyse', 'date_analyse']
    search_fields = ['nom_analyse', 'puits__nom', 'observations']
    readonly_fields = ['date_analyse']
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('nom_analyse', 'reservoir', 'puits', 'nature_fluide', 'statut_analyse')
        }),
        (_('Caractéristiques du réservoir'), {
            'fields': ('hauteur_utile', 'net_pay', 'contact_fluide', 'temperature_reservoir')
        }),
        (_('Propriétés pétrophysiques'), {
            'fields': ('porosite', 'permeabilite')
        }),
        (_('Production'), {
            'fields': ('debit_estime', 'pression_tete')
        }),
        (_('Analyse'), {
            'fields': ('observations', 'analyste', 'date_analyse')
        }),
    )


@admin.register(TableauBordKPI)
class TableauBordKPIAdmin(admin.ModelAdmin):
    list_display = ['nom_kpi', 'puits', 'categorie_kpi', 'valeur_actuelle', 'pourcentage_atteinte_display', 'statut_kpi', 'date_calcul']
    list_filter = ['categorie_kpi', 'statut_kpi', 'date_calcul']
    search_fields = ['nom_kpi', 'puits__nom']
    readonly_fields = ['pourcentage_atteinte', 'evolution_pourcentage', 'statut_kpi', 'date_calcul']
    fieldsets = (
        (_('KPI'), {
            'fields': ('nom_kpi', 'puits', 'categorie_kpi', 'periode_reference')
        }),
        (_('Valeurs'), {
            'fields': ('valeur_actuelle', 'valeur_precedente', 'unite_mesure')
        }),
        (_('Objectifs'), {
            'fields': ('objectif_cible', 'seuil_alerte', 'pourcentage_atteinte', 'evolution_pourcentage')
        }),
        (_('Statut'), {
            'fields': ('statut_kpi', 'calcule_par', 'date_calcul')
        }),
    )
    
    def pourcentage_atteinte_display(self, obj):
        if obj.pourcentage_atteinte:
            if obj.pourcentage_atteinte >= 100:
                color = 'green'
            elif obj.pourcentage_atteinte >= 75:
                color = 'orange'
            else:
                color = 'red'
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, obj.pourcentage_atteinte
            )
        return "-"
    pourcentage_atteinte_display.short_description = _('Atteinte (%)')


@admin.register(AnalysePredictive)
class AnalysePredictiveAdmin(admin.ModelAdmin):
    list_display = ['nom_analyse', 'puits', 'type_prediction', 'valeur_predite', 'intervalle_confiance', 'statut_prediction', 'date_creation']
    list_filter = ['type_prediction', 'statut_prediction', 'date_creation']
    search_fields = ['nom_analyse', 'puits__nom', 'modele_utilise']
    readonly_fields = ['date_creation']
    fieldsets = (
        (_('Analyse'), {
            'fields': ('nom_analyse', 'puits', 'type_prediction', 'statut_prediction')
        }),
        (_('Prédiction'), {
            'fields': ('valeur_predite', 'valeur_min_predite', 'valeur_max_predite', 'intervalle_confiance')
        }),
        (_('Temporalité'), {
            'fields': ('date_prediction_pour', 'horizon_prediction_jours')
        }),
        (_('Modèle'), {
            'fields': ('modele_utilise', 'version_modele', 'parametres_modele', 'metriques_performance')
        }),
        (_('Données'), {
            'fields': ('donnees_entree', 'observations')
        }),
        (_('Métadonnées'), {
            'fields': ('cree_par', 'date_creation')
        }),
    )


@admin.register(AlerteAnalytique)
class AlerteAnalytiqueAdmin(admin.ModelAdmin):
    list_display = ['titre_alerte', 'puits', 'type_alerte', 'niveau_urgence', 'statut_alerte', 'date_declenchement']
    list_filter = ['type_alerte', 'niveau_urgence', 'statut_alerte', 'date_declenchement']
    search_fields = ['titre_alerte', 'puits__nom', 'description']
    readonly_fields = ['date_declenchement']
    fieldsets = (
        (_('Alerte'), {
            'fields': ('titre_alerte', 'puits', 'type_alerte', 'niveau_urgence')
        }),
        (_('Détails'), {
            'fields': ('description', 'valeur_declenchante', 'seuil_reference', 'source_donnees')
        }),
        (_('Traitement'), {
            'fields': ('statut_alerte', 'assigne_a', 'resolu_par', 'actions_prises')
        }),
        (_('Dates'), {
            'fields': ('date_declenchement', 'date_resolution')
        }),
    )
    
    def get_list_display_links(self, request, list_display):
        return ['titre_alerte']
