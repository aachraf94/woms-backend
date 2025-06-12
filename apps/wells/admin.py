from django.contrib import admin
from .models import Well, WellOperation, DailyReport, WellDocument
from .region_models import Region, Forage, Phase, TypeOperation, Operation, Probleme, TypeIndicateur, Indicateur, Reservoir

@admin.register(Well)
class WellAdmin(admin.ModelAdmin):
    list_display = ('nom', 'name', 'type', 'region', 'statut', 'status', 'created_at', 'is_archived')
    list_filter = ('statut', 'status', 'is_archived', 'created_at', 'region')
    search_fields = ('nom', 'name', 'type', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

@admin.register(WellOperation)
class WellOperationAdmin(admin.ModelAdmin):
    list_display = ('well', 'operation_type', 'name', 'status', 'planned_start_date')
    list_filter = ('operation_type', 'status', 'planned_start_date')
    search_fields = ('name', 'description', 'well__nom', 'well__name')
    date_hierarchy = 'planned_start_date'

@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('well', 'report_date', 'progress', 'submitted_by')
    list_filter = ('report_date', 'submitted_by')
    search_fields = ('well__nom', 'well__name', 'activities', 'issues')
    date_hierarchy = 'report_date'

@admin.register(WellDocument)
class WellDocumentAdmin(admin.ModelAdmin):
    list_display = ('nom', 'title', 'well', 'type', 'document_type', 'uploade_par', 'uploaded_by', 'date_upload')
    list_filter = ('type', 'document_type', 'date_upload', 'est_public')
    search_fields = ('nom', 'title', 'description', 'well__nom', 'well__name')
    date_hierarchy = 'date_upload'

# New admin classes for Java-inspired models
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'localisation', 'responsable', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('nom', 'code', 'localisation', 'responsable')
    readonly_fields = ('created_at',)

@admin.register(Forage)
class ForageAdmin(admin.ModelAdmin):
    list_display = ('puit', 'cout', 'date_debut', 'date_fin', 'created_at')
    list_filter = ('date_debut', 'date_fin', 'created_at')
    search_fields = ('puit__nom', 'puit__name')
    date_hierarchy = 'date_debut'

@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ('forage', 'numero_phase', 'diametre', 'profondeur_prevue', 'profondeur_reelle', 'date_debut_prevue', 'date_debut_reelle')
    list_filter = ('diametre', 'date_debut_prevue', 'date_debut_reelle')
    search_fields = ('forage__puit__nom', 'description')
    ordering = ('forage', 'numero_phase')

@admin.register(TypeOperation)
class TypeOperationAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'duree_estimee', 'cout_unitaire')
    search_fields = ('code', 'nom', 'description')
    ordering = ('code',)

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('phase', 'type_operation', 'statut', 'date_debut', 'date_fin', 'cout', 'created_by')
    list_filter = ('statut', 'date_debut', 'date_fin', 'type_operation')
    search_fields = ('description', 'type_operation__nom', 'phase__forage__puit__nom')
    date_hierarchy = 'date_debut'

@admin.register(Probleme)
class ProblemeAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_probleme', 'gravite', 'statut', 'date_detection', 'detecte_par')
    list_filter = ('type_probleme', 'gravite', 'statut', 'date_detection')
    search_fields = ('titre', 'description', 'solution')
    date_hierarchy = 'date_detection'

@admin.register(TypeIndicateur)
class TypeIndicateurAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'unite')
    search_fields = ('code', 'nom', 'description')
    ordering = ('code',)

@admin.register(Indicateur)
class IndicateurAdmin(admin.ModelAdmin):
    list_display = ('phase', 'type_indicateur', 'valeur', 'date_mesure')
    list_filter = ('type_indicateur', 'date_mesure')
    search_fields = ('type_indicateur__nom', 'notes')
    date_hierarchy = 'date_mesure'

@admin.register(Reservoir)
class ReservoirAdmin(admin.ModelAdmin):
    list_display = ('nom', 'puit', 'profondeur', 'pression', 'temperature', 'type_fluide')
    list_filter = ('type_fluide',)
    search_fields = ('nom', 'puit__nom', 'puit__name')
    ordering = ('profondeur',)
