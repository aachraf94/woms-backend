from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    DocumentPuits, RapportQuotidien, RapportPlanification,
    ModeleDocument, ArchiveDocument
)


@admin.register(DocumentPuits)
class DocumentPuitsAdmin(admin.ModelAdmin):
    list_display = [
        'nom_document', 'type_document', 'puits', 'statut', 'est_approuve',
        'taille_fichier_formatee', 'date_creation', 'cree_par'
    ]
    list_filter = [
        'type_document', 'statut', 'est_approuve', 'est_public', 'est_confidentiel',
        'date_creation', 'phase'
    ]
    search_fields = ['nom_document', 'description', 'mots_cles', 'puits__name']
    readonly_fields = [
        'taille_fichier', 'date_creation', 'date_modification',
        'nombre_telechargements', 'extension_fichier_display'
    ]
    fieldsets = (
        (_('Informations générales'), {
            'fields': (
                'nom_document', 'type_document', 'description',
                'mots_cles', 'fichier', 'extension_fichier_display'
            )
        }),
        (_('Relations'), {
            'fields': ('puits', 'phase', 'operation')
        }),
        (_('Contrôle d\'accès'), {
            'fields': ('est_public', 'est_confidentiel')
        }),
        (_('Versioning'), {
            'fields': ('numero_version', 'version_precedente')
        }),
        (_('Workflow'), {
            'fields': (
                'statut', 'est_approuve', 'approuve_par',
                'date_approbation', 'commentaires_approbation'
            )
        }),
        (_('Validité'), {
            'fields': ('date_validite_debut', 'date_validite_fin')
        }),
        (_('Audit'), {
            'fields': (
                'cree_par', 'modifie_par', 'date_creation',
                'date_modification', 'taille_fichier', 'nombre_telechargements'
            )
        }),
    )
    
    def taille_fichier_formatee(self, obj):
        if obj.taille_fichier:
            if obj.taille_fichier < 1024:
                return f"{obj.taille_fichier} B"
            elif obj.taille_fichier < 1024*1024:
                return f"{obj.taille_fichier/1024:.1f} KB"
            else:
                return f"{obj.taille_fichier/(1024*1024):.1f} MB"
        return "-"
    taille_fichier_formatee.short_description = _('Taille du fichier')
    
    def extension_fichier_display(self, obj):
        ext = obj.extension_fichier()
        if ext:
            return format_html('<span class="badge badge-info">{}</span>', ext)
        return "-"
    extension_fichier_display.short_description = _('Extension')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.cree_par = request.user
        else:
            obj.modifie_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(RapportQuotidien)
class RapportQuotidienAdmin(admin.ModelAdmin):
    list_display = [
        'numero_rapport', 'puits', 'date_rapport', 'statut',
        'avancement_pourcentage', 'heures_travaillees', 'soumis_par'
    ]
    list_filter = [
        'statut', 'date_rapport', 'puits', 'phase',
        'date_creation'
    ]
    search_fields = [
        'numero_rapport', 'puits__name', 'activites_realisees',
        'problemes_rencontres'
    ]
    readonly_fields = [
        'numero_rapport', 'date_creation', 'date_modification'
    ]
    fieldsets = (
        (_('Informations générales'), {
            'fields': (
                'puits', 'phase', 'date_rapport', 'numero_rapport',
                'fichier_rapport'
            )
        }),
        (_('Contenu du rapport'), {
            'fields': (
                'activites_realisees', 'objectifs_jour', 'objectifs_lendemain',
                'problemes_rencontres', 'solutions_appliquees'
            )
        }),
        (_('Indicateurs'), {
            'fields': (
                'avancement_pourcentage', 'heures_travaillees', 'nombre_personnel'
            )
        }),
        (_('Conditions'), {
            'fields': (
                'conditions_meteo', 'temperature_min', 'temperature_max',
                'vitesse_vent'
            )
        }),
        (_('Équipements et sécurité'), {
            'fields': (
                'statut_equipement', 'incidents_securite',
                'mesures_securite_prises'
            )
        }),
        (_('Validation'), {
            'fields': (
                'statut', 'valide_par', 'date_validation',
                'commentaires_validation'
            )
        }),
        (_('Audit'), {
            'fields': ('soumis_par', 'date_creation', 'date_modification')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.soumis_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(RapportPlanification)
class RapportPlanificationAdmin(admin.ModelAdmin):
    list_display = [
        'code_projet', 'nom_projet', 'puits', 'statut_planification',
        'priorite', 'date_debut_prevue', 'date_fin_prevue',
        'pourcentage_avancement'
    ]
    list_filter = [
        'statut_planification', 'priorite', 'niveau_risque_global',
        'date_debut_prevue', 'devise'
    ]
    search_fields = [
        'nom_projet', 'code_projet', 'description_projet',
        'objectifs', 'puits__name'
    ]
    readonly_fields = [
        'code_projet', 'date_creation', 'date_modification',
        'duree_reelle_calculee', 'pourcentage_budget_display',
        'est_en_retard_display'
    ]
    fieldsets = (
        (_('Informations du projet'), {
            'fields': (
                'nom_projet', 'code_projet', 'puits', 'phase',
                'fichier_plan', 'priorite'
            )
        }),
        (_('Planification'), {
            'fields': (
                'date_debut_prevue', 'date_fin_prevue', 'duree_prevue_jours',
                'date_debut_reelle', 'date_fin_reelle', 'duree_reelle_calculee'
            )
        }),
        (_('Budget'), {
            'fields': (
                'budget_prevu', 'budget_consomme', 'devise',
                'pourcentage_budget_display'
            )
        }),
        (_('Description'), {
            'fields': (
                'description_projet', 'objectifs', 'livrables_attendus'
            )
        }),
        (_('Gestion des risques'), {
            'fields': (
                'niveau_risque_global', 'risques_identifies',
                'mesures_mitigation'
            )
        }),
        (_('Ressources'), {
            'fields': (
                'ressources_humaines', 'equipements_requis',
                'materiaux_necessaires'
            )
        }),
        (_('Suivi'), {
            'fields': (
                'jalons_principaux', 'pourcentage_avancement',
                'statut_planification', 'est_en_retard_display'
            )
        }),
        (_('Approbation'), {
            'fields': (
                'approuve_par', 'date_approbation',
                'commentaires_approbation'
            )
        }),
        (_('Audit'), {
            'fields': ('cree_par', 'date_creation', 'date_modification')
        }),
    )
    
    def duree_reelle_calculee(self, obj):
        duree = obj.duree_reelle_jours()
        return f"{duree} jours" if duree else "-"
    duree_reelle_calculee.short_description = _('Durée réelle')
    
    def pourcentage_budget_display(self, obj):
        pourcentage = obj.pourcentage_budget_consomme()
        color = "green" if pourcentage <= 80 else "orange" if pourcentage <= 100 else "red"
        return format_html(
            '<span style="color: {}">{:.1f}%</span>',
            color, pourcentage
        )
    pourcentage_budget_display.short_description = _('Budget consommé')
    
    def est_en_retard_display(self, obj):
        en_retard = obj.est_en_retard()
        if en_retard:
            return format_html('<span style="color: red;">⚠️ En retard</span>')
        return format_html('<span style="color: green;">✅ Dans les temps</span>')
    est_en_retard_display.short_description = _('Statut délai')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModeleDocument)
class ModeleDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'nom_modele', 'type_modele', 'version', 'est_actif',
        'est_par_defaut', 'nombre_utilisations', 'cree_par'
    ]
    list_filter = [
        'type_modele', 'est_actif', 'est_par_defaut', 'est_public',
        'date_creation'
    ]
    search_fields = ['nom_modele', 'code_modele', 'description']
    readonly_fields = [
        'code_modele', 'nombre_utilisations', 'derniere_utilisation',
        'date_creation', 'date_modification'
    ]
    filter_horizontal = ['utilisateurs_autorises']
    fieldsets = (
        (_('Informations générales'), {
            'fields': (
                'nom_modele', 'code_modele', 'type_modele',
                'fichier_modele', 'version'
            )
        }),
        (_('Description'), {
            'fields': ('description', 'instructions_utilisation')
        }),
        (_('Configuration'), {
            'fields': ('champs_variables', 'champs_obligatoires')
        }),
        (_('Statut'), {
            'fields': ('est_actif', 'est_par_defaut', 'est_public')
        }),
        (_('Permissions'), {
            'fields': ('utilisateurs_autorises',)
        }),
        (_('Statistiques'), {
            'fields': (
                'nombre_utilisations', 'derniere_utilisation'
            )
        }),
        (_('Audit'), {
            'fields': ('cree_par', 'date_creation', 'date_modification')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(ArchiveDocument)
class ArchiveDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'document_original', 'raison_archivage', 'date_archivage',
        'peut_etre_restaure', 'date_suppression_prevue', 'archive_par'
    ]
    list_filter = [
        'raison_archivage', 'peut_etre_restaure', 'date_archivage',
        'date_suppression_prevue'
    ]
    search_fields = [
        'document_original__nom_document', 'description_archivage',
        'raison_archivage'
    ]
    readonly_fields = [
        'date_archivage', 'taille_archive', 'checksum_archive',
        'peut_etre_supprime_display'
    ]
    fieldsets = (
        (_('Document archivé'), {
            'fields': ('document_original',)
        }),
        (_('Informations d\'archivage'), {
            'fields': (
                'raison_archivage', 'description_archivage',
                'date_archivage', 'archive_par'
            )
        }),
        (_('Gestion de la rétention'), {
            'fields': (
                'peut_etre_restaure', 'duree_retention_jours',
                'date_suppression_prevue', 'peut_etre_supprime_display'
            )
        }),
        (_('Sauvegarde'), {
            'fields': (
                'chemin_sauvegarde', 'taille_archive', 'checksum_archive'
            )
        }),
    )
    
    def peut_etre_supprime_display(self, obj):
        peut_supprimer = obj.peut_etre_supprime()
        if peut_supprimer:
            return format_html('<span style="color: red;">⚠️ Peut être supprimé</span>')
        return format_html('<span style="color: green;">✅ Protégé</span>')
    peut_etre_supprime_display.short_description = _('Statut suppression')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.archive_par = request.user
        super().save_model(request, obj, form, change)
