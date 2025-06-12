from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

from .models import Notification, Incident, RegleAlerte, JournalAction
from .serializers import (
    NotificationSerializer, NotificationCreateSerializer,
    IncidentSerializer, IncidentCreateSerializer,
    RegleAlerteSerializer, JournalActionSerializer,
    StatistiquesSerializer
)


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des notifications"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type_notification', 'lu']
    search_fields = ['titre', 'message']
    ordering_fields = ['date_creation', 'titre']
    ordering = ['-date_creation']

    def get_queryset(self):
        """Filtrer les notifications pour l'utilisateur connecté"""
        return self.queryset.filter(destinataire=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    @action(detail=False, methods=['get'])
    def non_lues(self, request):
        """Récupérer les notifications non lues"""
        notifications = self.get_queryset().filter(lu=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marquer_comme_lue(self, request, pk=None):
        """Marquer une notification comme lue"""
        notification = self.get_object()
        notification.lu = True
        notification.date_lecture = timezone.now()
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def marquer_toutes_lues(self, request):
        """Marquer toutes les notifications comme lues"""
        notifications = self.get_queryset().filter(lu=False)
        notifications.update(lu=True, date_lecture=timezone.now())
        return Response({'message': 'Toutes les notifications ont été marquées comme lues'})


class IncidentViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des incidents"""
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['type_incident', 'statut', 'priorite', 'assigne_a']
    search_fields = ['titre', 'description']
    ordering_fields = ['date_creation', 'priorite', 'titre']
    ordering = ['-date_creation']

    def get_serializer_class(self):
        if self.action == 'create':
            return IncidentCreateSerializer
        return IncidentSerializer

    @action(detail=False, methods=['get'])
    def mes_incidents(self, request):
        """Récupérer les incidents de l'utilisateur connecté"""
        incidents = self.queryset.filter(
            Q(rapporte_par=request.user) | Q(assigne_a=request.user)
        )
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def ouverts(self, request):
        """Récupérer les incidents ouverts (nouveau, en_cours)"""
        incidents = self.queryset.filter(statut__in=['nouveau', 'en_cours'])
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def critiques(self, request):
        """Récupérer les incidents critiques"""
        incidents = self.queryset.filter(priorite=4)
        serializer = self.get_serializer(incidents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assigner(self, request, pk=None):
        """Assigner un incident à un utilisateur"""
        incident = self.get_object()
        assigne_a_id = request.data.get('assigne_a_id')
        
        if assigne_a_id:
            incident.assigne_a_id = assigne_a_id
            incident.save()
            
            # Créer une entrée dans le journal
            JournalAction.objects.create(
                action=f"Incident assigné à l'utilisateur ID {assigne_a_id}",
                utilisateur=request.user,
                incident_lie=incident
            )
            
        serializer = self.get_serializer(incident)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def changer_statut(self, request, pk=None):
        """Changer le statut d'un incident"""
        incident = self.get_object()
        nouveau_statut = request.data.get('statut')
        
        if nouveau_statut and nouveau_statut in dict(incident._meta.get_field('statut').choices):
            ancien_statut = incident.get_statut_display()
            incident.statut = nouveau_statut
            
            if nouveau_statut == 'resolu':
                incident.date_resolution = timezone.now()
                
            incident.save()
            
            # Créer une entrée dans le journal
            JournalAction.objects.create(
                action=f"Statut changé de '{ancien_statut}' à '{incident.get_statut_display()}'",
                utilisateur=request.user,
                incident_lie=incident
            )
            
        serializer = self.get_serializer(incident)
        return Response(serializer.data)


class RegleAlerteViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des règles d'alerte"""
    queryset = RegleAlerte.objects.all()
    serializer_class = RegleAlerteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['active', 'type_capteur']
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'date_creation']
    ordering = ['nom']

    @action(detail=False, methods=['get'])
    def actives(self, request):
        """Récupérer les règles d'alerte actives"""
        regles = self.queryset.filter(active=True)
        serializer = self.get_serializer(regles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def activer(self, request, pk=None):
        """Activer une règle d'alerte"""
        regle = self.get_object()
        regle.active = True
        regle.save()
        
        # Créer une entrée dans le journal
        JournalAction.objects.create(
            action=f"Règle d'alerte '{regle.nom}' activée",
            utilisateur=request.user
        )
        
        serializer = self.get_serializer(regle)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactiver une règle d'alerte"""
        regle = self.get_object()
        regle.active = False
        regle.save()
        
        # Créer une entrée dans le journal
        JournalAction.objects.create(
            action=f"Règle d'alerte '{regle.nom}' désactivée",
            utilisateur=request.user
        )
        
        serializer = self.get_serializer(regle)
        return Response(serializer.data)


class JournalActionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour consulter le journal d'actions (lecture seule)"""
    queryset = JournalAction.objects.all()
    serializer_class = JournalActionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['utilisateur', 'incident_lie']
    search_fields = ['action', 'details']
    ordering_fields = ['horodatage']
    ordering = ['-horodatage']

    @action(detail=False, methods=['get'])
    def mes_actions(self, request):
        """Récupérer les actions de l'utilisateur connecté"""
        actions = self.queryset.filter(utilisateur=request.user)
        serializer = self.get_serializer(actions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Récupérer les actions récentes (dernières 24h)"""
        hier = timezone.now() - timedelta(hours=24)
        actions = self.queryset.filter(horodatage__gte=hier)
        serializer = self.get_serializer(actions, many=True)
        return Response(serializer.data)


class StatistiquesViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques du dashboard"""
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Récupérer les statistiques pour le dashboard"""
        user = request.user
        aujourd_hui = timezone.now().date()
        
        stats = {
            'total_notifications': Notification.objects.filter(destinataire=user).count(),
            'notifications_non_lues': Notification.objects.filter(destinataire=user, lu=False).count(),
            'total_incidents': Incident.objects.count(),
            'incidents_ouverts': Incident.objects.filter(statut__in=['nouveau', 'en_cours']).count(),
            'incidents_critiques': Incident.objects.filter(priorite=4).count(),
            'regles_actives': RegleAlerte.objects.filter(active=True).count(),
            'actions_aujourd_hui': JournalAction.objects.filter(horodatage__date=aujourd_hui).count(),
        }
        
        serializer = StatistiquesSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def incidents_par_type(self, request):
        """Statistiques des incidents par type"""
        stats = Incident.objects.values('type_incident').annotate(
            count=Count('id')
        ).order_by('-count')
        return Response(stats)

    @action(detail=False, methods=['get'])
    def incidents_par_statut(self, request):
        """Statistiques des incidents par statut"""
        stats = Incident.objects.values('statut').annotate(
            count=Count('id')
        ).order_by('-count')
        return Response(stats)
