from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VisualisationPuitsViewSet,
    IndicateurClePerformanceViewSet,
    TableauBordExecutifViewSet,
    AlerteTableauBordViewSet,
    RapportPerformanceDetailleViewSet
)

app_name = 'dashboard'

router = DefaultRouter()
router.register(r'visualisations', VisualisationPuitsViewSet, basename='visualisation')
router.register(r'indicateurs', IndicateurClePerformanceViewSet, basename='indicateur')
router.register(r'tableaux-bord', TableauBordExecutifViewSet, basename='tableau-bord')
router.register(r'alertes', AlerteTableauBordViewSet, basename='alerte')
router.register(r'rapports', RapportPerformanceDetailleViewSet, basename='rapport')

urlpatterns = [
    path('api/', include(router.urls)),
]
