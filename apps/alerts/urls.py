from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, IncidentViewSet, 
    RegleAlerteViewSet, JournalActionViewSet,
    StatistiquesViewSet
)

app_name = 'alerts'

# Router pour les ViewSets
router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'incidents', IncidentViewSet, basename='incident')
router.register(r'regles-alerte', RegleAlerteViewSet, basename='regle-alerte')
router.register(r'journal-actions', JournalActionViewSet, basename='journal-action')
router.register(r'statistiques', StatistiquesViewSet, basename='statistiques')

urlpatterns = [
    # API REST
    path('api/', include(router.urls)),
    
    # URLs spécifiques pour les actions
    path('api/notifications/non-lues/', 
         NotificationViewSet.as_view({'get': 'non_lues'}), 
         name='notifications-non-lues'),
    
    path('api/notifications/<int:pk>/marquer-lue/', 
         NotificationViewSet.as_view({'post': 'marquer_comme_lue'}), 
         name='notification-marquer-lue'),
    
    path('api/notifications/marquer-toutes-lues/', 
         NotificationViewSet.as_view({'post': 'marquer_toutes_lues'}), 
         name='notifications-marquer-toutes-lues'),
    
    path('api/incidents/mes-incidents/', 
         IncidentViewSet.as_view({'get': 'mes_incidents'}), 
         name='incidents-mes-incidents'),
    
    path('api/incidents/ouverts/', 
         IncidentViewSet.as_view({'get': 'ouverts'}), 
         name='incidents-ouverts'),
    
    path('api/incidents/critiques/', 
         IncidentViewSet.as_view({'get': 'critiques'}), 
         name='incidents-critiques'),
    
    path('api/incidents/<int:pk>/assigner/', 
         IncidentViewSet.as_view({'post': 'assigner'}), 
         name='incident-assigner'),
    
    path('api/incidents/<int:pk>/changer-statut/', 
         IncidentViewSet.as_view({'post': 'changer_statut'}), 
         name='incident-changer-statut'),
    
    path('api/regles-alerte/actives/', 
         RegleAlerteViewSet.as_view({'get': 'actives'}), 
         name='regles-alerte-actives'),
    
    path('api/regles-alerte/<int:pk>/activer/', 
         RegleAlerteViewSet.as_view({'post': 'activer'}), 
         name='regle-alerte-activer'),
    
    path('api/regles-alerte/<int:pk>/desactiver/', 
         RegleAlerteViewSet.as_view({'post': 'desactiver'}), 
         name='regle-alerte-desactiver'),
    
    path('api/journal-actions/mes-actions/', 
         JournalActionViewSet.as_view({'get': 'mes_actions'}), 
         name='journal-actions-mes-actions'),
    
    path('api/journal-actions/recent/', 
         JournalActionViewSet.as_view({'get': 'recent'}), 
         name='journal-actions-recent'),
    
    path('api/statistiques/dashboard/', 
         StatistiquesViewSet.as_view({'get': 'dashboard'}), 
         name='statistiques-dashboard'),
    
    path('api/statistiques/incidents-par-type/', 
         StatistiquesViewSet.as_view({'get': 'incidents_par_type'}), 
         name='statistiques-incidents-par-type'),
    
    path('api/statistiques/incidents-par-statut/', 
         StatistiquesViewSet.as_view({'get': 'incidents_par_statut'}), 
         name='statistiques-incidents-par-statut'),
]
