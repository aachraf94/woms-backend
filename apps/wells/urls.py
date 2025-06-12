from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'wells', views.WellViewSet, basename='well')
router.register(r'operations', views.WellOperationViewSet, basename='operation')
router.register(r'reports', views.DailyReportViewSet, basename='report')
router.register(r'documents', views.WellDocumentViewSet, basename='document')

# New endpoints based on Java backend
router.register(r'regions', views.RegionViewSet, basename='region')
router.register(r'forages', views.ForageViewSet, basename='forage')
router.register(r'phases', views.PhaseViewSet, basename='phase')
router.register(r'type-operations', views.TypeOperationViewSet, basename='type-operation')
router.register(r'phase-operations', views.OperationViewSet, basename='phase-operation')
router.register(r'problemes', views.ProblemeViewSet, basename='probleme')
router.register(r'type-indicateurs', views.TypeIndicateurViewSet, basename='type-indicateur')
router.register(r'indicateurs', views.IndicateurViewSet, basename='indicateur')
router.register(r'reservoirs', views.ReservoirViewSet, basename='reservoir')

app_name = 'wells'

urlpatterns = [
    path('', include(router.urls)),
]
