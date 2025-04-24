from django.contrib import admin
from .models import Well, WellOperation, DailyReport, WellDocument

@admin.register(Well)
class WellAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'status', 'creation_date', 'is_archived')
    list_filter = ('status', 'is_archived', 'creation_date')
    search_fields = ('name', 'location', 'description')
    date_hierarchy = 'creation_date'

@admin.register(WellOperation)
class WellOperationAdmin(admin.ModelAdmin):
    list_display = ('well', 'operation_type', 'name', 'status', 'planned_start_date')
    list_filter = ('operation_type', 'status', 'planned_start_date')
    search_fields = ('name', 'description', 'well__name')
    date_hierarchy = 'planned_start_date'

@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ('well', 'report_date', 'progress', 'submitted_by')
    list_filter = ('report_date', 'submitted_by')
    search_fields = ('well__name', 'activities', 'issues')
    date_hierarchy = 'report_date'

@admin.register(WellDocument)
class WellDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'well', 'document_type', 'uploaded_by', 'uploaded_at')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('title', 'description', 'well__name')
    date_hierarchy = 'uploaded_at'
