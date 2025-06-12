from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DocumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.documents'
    verbose_name = _('Gestion des Documents')
    verbose_name_plural = _('Gestion des Documents')

    def ready(self):
        """Actions à effectuer quand l'app est prête."""
        try:
            import apps.documents.signals  # noqa F401
        except ImportError:
            pass
