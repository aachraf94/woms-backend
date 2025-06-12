from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JeuDonneesAnalytiquesViewSet, AnalyseEcartViewSet,
    InteractionAssistantIAViewSet, IndicateurPerformanceViewSet,
    AnalyseReservoirViewSet, TableauBordKPIViewSet,
    AnalysePredictiveViewSet, AlerteAnalytiqueViewSet
)

app_name = 'analytics'

router = DefaultRouter()
router.register(r'jeux-donnees', JeuDonneesAnalytiquesViewSet)
router.register(r'analyses-ecart', AnalyseEcartViewSet)
router.register(r'interactions-ia', InteractionAssistantIAViewSet)
router.register(r'indicateurs-performance', IndicateurPerformanceViewSet)
router.register(r'analyses-reservoir', AnalyseReservoirViewSet)
router.register(r'kpis', TableauBordKPIViewSet)
router.register(r'analyses-predictives', AnalysePredictiveViewSet)
router.register(r'alertes', AlerteAnalytiqueViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
