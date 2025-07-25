from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dashboard'
    verbose_name = _('Tableau de bord')
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.dashboard.signals
