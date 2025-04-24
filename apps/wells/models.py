from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class WellStatus(models.TextChoices):
    PLANNED = 'planned', _('Planned')
    ACTIVE = 'active', _('Active')
    PAUSED = 'paused', _('Paused')
    COMPLETED = 'completed', _('Completed')
    ABANDONED = 'abandoned', _('Abandoned')
    ARCHIVED = 'archived', _('Archived')

class OperationType(models.TextChoices):
    DRILLING = 'drilling', _('Drilling')
    LOGGING = 'logging', _('Logging')
    CASING = 'casing', _('Casing')
    TESTING = 'testing', _('Testing')
    COMPLETION = 'completion', _('Completion')
    WORKOVER = 'workover', _('Workover')
    MAINTENANCE = 'maintenance', _('Maintenance')

class Well(models.Model):
    """Model representing a well."""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=WellStatus.choices,
        default=WellStatus.PLANNED
    )
    depth = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_wells'
    )
    last_updated = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='updated_wells',
        null=True
    )
    is_archived = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    class Meta:
        ordering = ['-creation_date']
        verbose_name = _('Well')
        verbose_name_plural = _('Wells')

class WellOperation(models.Model):
    """Model representing an operation performed on a well."""
    well = models.ForeignKey(Well, on_delete=models.CASCADE, related_name='operations')
    operation_type = models.CharField(
        max_length=20,
        choices=OperationType.choices
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    planned_start_date = models.DateTimeField()
    planned_end_date = models.DateTimeField()
    actual_start_date = models.DateTimeField(null=True, blank=True)
    actual_end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=WellStatus.choices,
        default=WellStatus.PLANNED
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_operations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.operation_type} - {self.well.name} - {self.status}"
    
    class Meta:
        ordering = ['-planned_start_date']
        verbose_name = _('Well Operation')
        verbose_name_plural = _('Well Operations')

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
        return f"Report for {self.well.name} on {self.report_date}"
    
    class Meta:
        ordering = ['-report_date']
        unique_together = ['well', 'report_date']
        verbose_name = _('Daily Report')
        verbose_name_plural = _('Daily Reports')

class WellDocument(models.Model):
    """Model for documents related to wells."""
    well = models.ForeignKey(Well, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=100)
    file = models.FileField(upload_to='well_documents/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.well.name}"
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = _('Well Document')
        verbose_name_plural = _('Well Documents')
