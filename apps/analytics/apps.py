from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'
    verbose_name = _('Analyses et Insights')
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        try:
            import apps.analytics.signals
        except ImportError:
            pass
