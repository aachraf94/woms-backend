from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    VisualisationPuits,
    IndicateurClePerformance,
    TableauBordExecutif,
    AlerteTableauBord,
    RapportPerformanceDetaille
)


@admin.register(VisualisationPuits)
class VisualisationPuitsAdmin(admin.ModelAdmin):
    list_display = [
        'nom_puits_display', 'statut_visuel', 'code_couleur_display', 
        'efficacite_globale', 'nombre_incidents_actifs', 'derniere_mise_a_jour'
    ]
    list_filter = ['statut_visuel', 'code_couleur', 'derniere_mise_a_jour']
    search_fields = ['puits__nom', 'puits__name']
    readonly_fields = ['date_creation', 'derniere_mise_a_jour']
    fieldsets = (
        (_('Informations du puits'), {
            'fields': ('puits',)
        }),
        (_('Indicateurs visuels'), {
            'fields': ('statut_visuel', 'code_couleur', 'icone_statut')
        }),
        (_('Métriques de performance'), {
            'fields': (
                'taux_progression', 'efficacite_globale', 'cout_total_realise'
            )
        }),
        (_('Compteurs d\'alertes'), {
            'fields': (
                'nombre_incidents_actifs', 'nombre_alertes_non_lues', 
                'jours_depuis_derniere_activite'
            )
        }),
        (_('Audit'), {
            'fields': ('date_creation', 'derniere_mise_a_jour'),
            'classes': ('collapse',)
        })
    )
    
    def nom_puits_display(self, obj):
        return obj.nom_puits
    nom_puits_display.short_description = _('Nom du puits')
    
    def code_couleur_display(self, obj):
        colors = {
            'VERT': '#28a745',
            'ORANGE': '#fd7e14', 
            'ROUGE': '#dc3545',
            'BLEU': '#007bff',
            'GRIS': '#6c757d'
        }
        color = colors.get(obj.code_couleur, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color, obj.get_code_couleur_display()
        )
    code_couleur_display.short_description = _('Code couleur')
    
    actions = ['mettre_a_jour_statuts']
    
    def mettre_a_jour_statuts(self, request, queryset):
        for visualisation in queryset:
            visualisation.mettre_a_jour_statut()
        self.message_user(request, _('Statuts mis à jour avec succès.'))
    mettre_a_jour_statuts.short_description = _('Mettre à jour les statuts')


@admin.register(IndicateurClePerformance)
class IndicateurClePerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'nom_indicateur', 'nom_puits_display', 'type_indicateur',
        'performance_globale_display', 'periode_debut', 'periode_fin'
    ]
    list_filter = ['type_indicateur', 'date_calcul', 'periode_debut']
    search_fields = ['nom_indicateur', 'puits__nom', 'puits__name']
    readonly_fields = ['date_calcul', 'derniere_mise_a_jour', 'performance_globale_display']
    date_hierarchy = 'date_calcul'
    
    fieldsets = (
        (_('Identification'), {
            'fields': ('puits', 'nom_indicateur', 'type_indicateur', 'unite_mesure')
        }),
        (_('Période de mesure'), {
            'fields': ('periode_debut', 'periode_fin')
        }),
        (_('Variances principales'), {
            'fields': ('variance_cout', 'variance_temps', 'taux_forage_moyen')
        }),
        (_('Métriques de performance'), {
            'fields': (
                'efficacite_operationnelle', 'disponibilite_equipement',
                'taux_reussite_operations', 'indice_securite'
            )
        }),
        (_('Seuils et cibles'), {
            'fields': ('valeur_cible', 'seuil_alerte')
        }),
        (_('Audit'), {
            'fields': ('date_calcul', 'derniere_mise_a_jour'),
            'classes': ('collapse',)
        })
    )
    
    def nom_puits_display(self, obj):
        return obj.nom_puits
    nom_puits_display.short_description = _('Puits')
    
    def performance_globale_display(self, obj):
        score = obj.performance_globale
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, score
        )
    performance_globale_display.short_description = _('Performance globale')


@admin.register(TableauBordExecutif)
class TableauBordExecutifAdmin(admin.ModelAdmin):
    list_display = [
        'nom_tableau', 'type_tableau', 'total_puits', 'puits_actifs',
        'taux_completion_projets_display', 'est_actif', 'derniere_mise_a_jour'
    ]
    list_filter = ['type_tableau', 'est_actif', 'date_creation']
    search_fields = ['nom_tableau', 'description']
    readonly_fields = [
        'date_creation', 'derniere_mise_a_jour', 'taux_completion_projets_display',
        'performance_budgetaire_display'
    ]
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        (_('Identification'), {
            'fields': ('nom_tableau', 'type_tableau', 'description', 'est_actif')
        }),
        (_('Période de référence'), {
            'fields': ('periode_debut', 'periode_fin')
        }),
        (_('Métriques des puits'), {
            'fields': (
                'total_puits', 'puits_actifs', 'puits_termines',
                'puits_en_cours', 'puits_en_maintenance'
            )
        }),
        (_('Métriques financières'), {
            'fields': (
                'budget_total_alloue', 'cout_realise_cumule', 'variance_budgetaire',
                'taux_consommation_budget'
            )
        }),
        (_('Métriques temporelles'), {
            'fields': (
                'delai_moyen_completion', 'projets_en_retard', 'projets_en_avance',
                'taux_respect_delais'
            )
        }),
        (_('Métriques qualité et sécurité'), {
            'fields': (
                'nombre_incidents_total', 'taux_incidents', 'score_securite_global',
                'taux_conformite_qualite'
            )
        }),
        (_('Audit'), {
            'fields': ('cree_par', 'date_creation', 'derniere_mise_a_jour'),
            'classes': ('collapse',)
        })
    )
    
    def taux_completion_projets_display(self, obj):
        taux = obj.taux_completion_projets
        return f"{taux:.1f}%"
    taux_completion_projets_display.short_description = _('Taux de complétion')
    
    def performance_budgetaire_display(self, obj):
        perf = obj.performance_budgetaire
        return f"{perf:.1f}%"
    performance_budgetaire_display.short_description = _('Performance budgétaire')


@admin.register(AlerteTableauBord)
class AlerteTableauBordAdmin(admin.ModelAdmin):
    list_display = [
        'titre_alerte', 'nom_puits_display', 'type_alerte', 'niveau_alerte_display',
        'statut_alerte', 'est_active', 'date_creation'
    ]
    list_filter = [
        'type_alerte', 'niveau_alerte', 'statut_alerte', 'est_active', 'date_creation'
    ]
    search_fields = ['titre_alerte', 'description_detaillee', 'puits__nom', 'puits__name']
    readonly_fields = [
        'date_creation', 'duree_ouverture_display', 'est_critique_ou_urgente'
    ]
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        (_('Classification'), {
            'fields': ('puits', 'type_alerte', 'niveau_alerte', 'statut_alerte')
        }),
        (_('Contenu de l\'alerte'), {
            'fields': ('titre_alerte', 'description_detaillee', 'actions_recommandees')
        }),
        (_('Valeurs et seuils'), {
            'fields': ('valeur_seuil_defini', 'valeur_actuelle_mesuree', 'unite_valeur')
        }),
        (_('Gestion'), {
            'fields': (
                'est_active', 'est_accusee_reception', 'accusee_par', 'traitee_par'
            )
        }),
        (_('Dates importantes'), {
            'fields': (
                'date_creation', 'date_accusation', 'date_debut_traitement',
                'date_resolution', 'date_fermeture'
            ),
            'classes': ('collapse',)
        })
    )
    
    def nom_puits_display(self, obj):
        return obj.nom_puits
    nom_puits_display.short_description = _('Puits')
    
    def niveau_alerte_display(self, obj):
        colors = {
            'INFO': '#17a2b8',
            'ATTENTION': '#ffc107',
            'IMPORTANT': '#fd7e14',
            'CRITIQUE': '#dc3545',
            'URGENCE': '#721c24'
        }
        color = colors.get(obj.niveau_alerte, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_niveau_alerte_display()
        )
    niveau_alerte_display.short_description = _('Niveau')
    
    def duree_ouverture_display(self, obj):
        return f"{obj.duree_ouverture} jours"
    duree_ouverture_display.short_description = _('Durée ouverture')
    
    actions = ['accuser_reception_alertes', 'resoudre_alertes']
    
    def accuser_reception_alertes(self, request, queryset):
        for alerte in queryset.filter(est_accusee_reception=False):
            alerte.accuser_reception(request.user)
        self.message_user(request, _('Alertes accusées de réception.'))
    accuser_reception_alertes.short_description = _('Accuser réception')
    
    def resoudre_alertes(self, request, queryset):
        for alerte in queryset.filter(est_active=True):
            alerte.resoudre_alerte()
        self.message_user(request, _('Alertes résolues.'))
    resoudre_alertes.short_description = _('Résoudre les alertes')


@admin.register(RapportPerformanceDetaille)
class RapportPerformanceDetailleAdmin(admin.ModelAdmin):
    list_display = [
        'nom_rapport', 'type_rapport', 'statut_rapport',
        'periode_debut', 'periode_fin', 'genere_par', 'date_generation'
    ]
    list_filter = ['type_rapport', 'statut_rapport', 'date_generation']
    search_fields = ['nom_rapport', 'resume_executif']
    readonly_fields = [
        'date_generation', 'duree_periode_display', 'est_recent'
    ]
    filter_horizontal = ['destinataires']
    date_hierarchy = 'date_generation'
    
    fieldsets = (
        (_('Identification'), {
            'fields': ('nom_rapport', 'type_rapport', 'statut_rapport')
        }),
        (_('Période couverte'), {
            'fields': ('periode_debut', 'periode_fin')
        }),
        (_('Contenu'), {
            'fields': (
                'resume_executif', 'analyse_performance',
                'recommandations_amelioration', 'plan_action_propose'
            )
        }),
        (_('Configuration des métriques'), {
            'fields': (
                'inclut_metriques_financieres', 'inclut_metriques_operationnelles',
                'inclut_metriques_securite', 'inclut_analyses_tendances'
            )
        }),
        (_('Gestion et distribution'), {
            'fields': ('genere_par', 'valide_par', 'destinataires')
        }),
        (_('Fichiers'), {
            'fields': ('fichier_rapport_pdf', 'fichier_donnees_excel')
        }),
        (_('Données structurées'), {
            'fields': ('donnees_rapport',),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': (
                'date_generation', 'date_validation', 'date_publication'
            ),
            'classes': ('collapse',)
        })
    )
    
    def duree_periode_display(self, obj):
        return f"{obj.duree_periode} jours"
    duree_periode_display.short_description = _('Durée période')
    
    actions = ['valider_rapports', 'publier_rapports']
    
    def valider_rapports(self, request, queryset):
        for rapport in queryset.filter(statut_rapport='GENERE'):
            rapport.valider_rapport(request.user)
        self.message_user(request, _('Rapports validés.'))
    valider_rapports.short_description = _('Valider les rapports')
    
    def publier_rapports(self, request, queryset):
        for rapport in queryset.filter(statut_rapport='VALIDE'):
            rapport.publier_rapport()
        self.message_user(request, _('Rapports publiés.'))
    publier_rapports.short_description = _('Publier les rapports')
