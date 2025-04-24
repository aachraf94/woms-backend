from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'wells', views.WellViewSet, basename='well')
router.register(r'operations', views.WellOperationViewSet, basename='operation')
router.register(r'reports', views.DailyReportViewSet, basename='report')
router.register(r'documents', views.WellDocumentViewSet, basename='document')

app_name = 'wells'

urlpatterns = [
    path('', include(router.urls)),
]
