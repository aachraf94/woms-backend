from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentPuitsViewSet, RapportQuotidienViewSet,
    RapportPlanificationViewSet, ModeleDocumentViewSet,
    ArchiveDocumentViewSet
)

app_name = 'documents'

router = DefaultRouter()
router.register(r'documents-puits', DocumentPuitsViewSet, basename='documentpuits')
router.register(r'rapports-quotidiens', RapportQuotidienViewSet, basename='rapportquotidien')
router.register(r'rapports-planification', RapportPlanificationViewSet, basename='rapportplanification')
router.register(r'modeles-documents', ModeleDocumentViewSet, basename='modeledocument')
router.register(r'archives', ArchiveDocumentViewSet, basename='archivedocument')

urlpatterns = [
    path('api/', include(router.urls)),
]
