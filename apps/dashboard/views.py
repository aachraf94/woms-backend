from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    VisualisationPuits,
    IndicateurClePerformance,
    TableauBordExecutif,
    AlerteTableauBord,
    RapportPerformanceDetaille
)
from .serializers import (
    VisualisationPuitsSerializer,
    IndicateurClePerformanceSerializer,
    TableauBordExecutifSerializer,
    AlerteTableauBordSerializer,
    RapportPerformanceDetailleSerializer,
    DashboardSummarySerializer
)


class VisualisationPuitsViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des visualisations de puits."""
    queryset = VisualisationPuits.objects.all()
    serializer_class = VisualisationPuitsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres optionnels
        statut = self.request.query_params.get('statut', None)
        if statut:
            queryset = queryset.filter(statut_visuel=statut)
        
        critiques_seulement = self.request.query_params.get('critiques', None)
        if critiques_seulement == 'true':
            queryset = queryset.filter(
                statut_visuel__in=[
                    VisualisationPuits.StatutVisuel.CRITIQUE,
                    VisualisationPuits.StatutVisuel.ALERTE
                ]
            )
        
        return queryset.select_related('puits')
    
    @action(detail=True, methods=['post'])
    def mettre_a_jour_statut(self, request, pk=None):
        """Met à jour le statut d'une visualisation."""
        visualisation = self.get_object()
        visualisation.mettre_a_jour_statut()
        
        return Response({
            'message': _('Statut mis à jour avec succès'),
            'nouveau_statut': visualisation.statut_visuel,
            'nouveau_code_couleur': visualisation.code_couleur
        })
    
    @action(detail=False, methods=['get'])
    def resume_global(self, request):
        """Retourne un résumé global des visualisations."""
        queryset = self.get_queryset()
        
        resume = {
            'total_puits': queryset.count(),
            'puits_actifs': queryset.filter(statut_visuel=VisualisationPuits.StatutVisuel.ACTIF).count(),
            'puits_critiques': queryset.filter(
                statut_visuel__in=[
                    VisualisationPuits.StatutVisuel.CRITIQUE,
                    VisualisationPuits.StatutVisuel.ALERTE
                ]
            ).count(),
            'alertes_actives': queryset.aggregate(
                total=Sum('nombre_alertes_non_lues')
            )['total'] or 0,
            'incidents_actifs': queryset.aggregate(
                total=Sum('nombre_incidents_actifs')
            )['total'] or 0,
            'efficacite_moyenne': queryset.aggregate(
                moyenne=Avg('efficacite_globale')
            )['moyenne'] or 0,
            'cout_total_realise': queryset.aggregate(
                total=Sum('cout_total_realise')
            )['total'] or 0,
        }
        
        return Response(resume)


class IndicateurClePerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des indicateurs de performance."""
    queryset = IndicateurClePerformance.objects.all()
    serializer_class = IndicateurClePerformanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres par type d'indicateur
        type_indicateur = self.request.query_params.get('type', None)
        if type_indicateur:
            queryset = queryset.filter(type_indicateur=type_indicateur)
        
        # Filtres par puits
        puits_id = self.request.query_params.get('puits', None)
        if puits_id:
            queryset = queryset.filter(puits_id=puits_id)
        
        # Filtres par période
        date_debut = self.request.query_params.get('date_debut', None)
        date_fin = self.request.query_params.get('date_fin', None)
        if date_debut:
            queryset = queryset.filter(periode_debut__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(periode_fin__lte=date_fin)
        
        return queryset.select_related('puits')
    
    @action(detail=False, methods=['get'])
    def hors_seuils(self, request):
        """Retourne les indicateurs qui dépassent leurs seuils."""
        indicateurs_problematiques = []
        
        for indicateur in self.get_queryset():
            if not indicateur.est_dans_seuils():
                indicateurs_problematiques.append(indicateur)
        
        serializer = self.get_serializer(indicateurs_problematiques, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tendances(self, request):
        """Analyse les tendances des indicateurs."""
        type_indicateur = request.query_params.get('type', 'FINANCIER')
        puits_id = request.query_params.get('puits', None)
        
        queryset = self.get_queryset().filter(type_indicateur=type_indicateur)
        if puits_id:
            queryset = queryset.filter(puits_id=puits_id)
        
        # Calculer les tendances par mois
        tendances = queryset.extra(
            select={'mois': "DATE_FORMAT(periode_debut, '%%Y-%%m')"}
        ).values('mois').annotate(
            performance_moyenne=Avg('efficacite_operationnelle'),
            nombre_indicateurs=Count('id')
        ).order_by('mois')
        
        return Response(list(tendances))


class TableauBordExecutifViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des tableaux de bord exécutifs."""
    queryset = TableauBordExecutif.objects.all()
    serializer_class = TableauBordExecutifSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().filter(est_actif=True).select_related('cree_par')
    
    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)
    
    @action(detail=True, methods=['post'])
    def recalculer_metriques(self, request, pk=None):
        """Recalcule les métriques du tableau de bord."""
        tableau = self.get_object()
        tableau.calculer_metriques_globales()
        
        return Response({
            'message': _('Métriques recalculées avec succès'),
            'derniere_mise_a_jour': tableau.derniere_mise_a_jour
        })


class AlerteTableauBordViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des alertes."""
    queryset = AlerteTableauBord.objects.all()
    serializer_class = AlerteTableauBordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer par statut
        actives_seulement = self.request.query_params.get('actives', None)
        if actives_seulement == 'true':
            queryset = queryset.filter(est_active=True)
        
        # Filtrer par niveau
        niveau = self.request.query_params.get('niveau', None)
        if niveau:
            queryset = queryset.filter(niveau_alerte=niveau)
        
        # Filtrer les alertes critiques
        critiques_seulement = self.request.query_params.get('critiques', None)
        if critiques_seulement == 'true':
            queryset = queryset.filter(
                niveau_alerte__in=[
                    AlerteTableauBord.NiveauAlerte.CRITIQUE,
                    AlerteTableauBord.NiveauAlerte.URGENCE
                ]
            )
        
        return queryset.select_related('puits', 'accusee_par', 'traitee_par')
    
    @action(detail=True, methods=['post'])
    def accuser_reception(self, request, pk=None):
        """Accuse réception d'une alerte."""
        alerte = self.get_object()
        
        if alerte.est_accusee_reception:
            return Response(
                {'error': _('Cette alerte a déjà été accusée de réception')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alerte.accuser_reception(request.user)
        
        return Response({
            'message': _('Alerte accusée de réception avec succès'),
            'date_accusation': alerte.date_accusation
        })
    
    @action(detail=True, methods=['post'])
    def commencer_traitement(self, request, pk=None):
        """Commence le traitement d'une alerte."""
        alerte = self.get_object()
        
        if alerte.statut_alerte == AlerteTableauBord.StatutAlerte.EN_COURS:
            return Response(
                {'error': _('Cette alerte est déjà en cours de traitement')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alerte.commencer_traitement(request.user)
        
        return Response({
            'message': _('Traitement de l\'alerte commencé'),
            'date_debut_traitement': alerte.date_debut_traitement
        })
    
    @action(detail=True, methods=['post'])
    def resoudre(self, request, pk=None):
        """Résout une alerte."""
        alerte = self.get_object()
        
        if not alerte.est_active:
            return Response(
                {'error': _('Cette alerte est déjà résolue')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alerte.resoudre_alerte()
        
        return Response({
            'message': _('Alerte résolue avec succès'),
            'date_resolution': alerte.date_resolution
        })
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des alertes."""
        queryset = self.get_queryset()
        
        stats = {
            'total_alertes': queryset.count(),
            'alertes_actives': queryset.filter(est_active=True).count(),
            'alertes_critiques': queryset.filter(
                niveau_alerte__in=[
                    AlerteTableauBord.NiveauAlerte.CRITIQUE,
                    AlerteTableauBord.NiveauAlerte.URGENCE
                ]
            ).count(),
            'alertes_non_accusees': queryset.filter(est_accusee_reception=False).count(),
            'repartition_par_type': dict(
                queryset.values_list('type_alerte').annotate(Count('id'))
            ),
            'repartition_par_niveau': dict(
                queryset.values_list('niveau_alerte').annotate(Count('id'))
            ),
            'duree_moyenne_resolution': queryset.filter(
                date_resolution__isnull=False
            ).aggregate(
                duree_moyenne=Avg('duree_ouverture')
            )['duree_moyenne'] or 0
        }
        
        return Response(stats)


class RapportPerformanceDetailleViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rapports de performance."""
    queryset = RapportPerformanceDetaille.objects.all()
    serializer_class = RapportPerformanceDetailleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().select_related('genere_par', 'valide_par')
    
    def perform_create(self, serializer):
        serializer.save(genere_par=self.request.user)
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide un rapport."""
        rapport = self.get_object()
        
        if rapport.statut_rapport != RapportPerformanceDetaille.StatutRapport.GENERE:
            return Response(
                {'error': _('Seuls les rapports générés peuvent être validés')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rapport.valider_rapport(request.user)
        
        return Response({
            'message': _('Rapport validé avec succès'),
            'date_validation': rapport.date_validation
        })
    
    @action(detail=True, methods=['post'])
    def publier(self, request, pk=None):
        """Publie un rapport."""
        rapport = self.get_object()
        
        if rapport.statut_rapport != RapportPerformanceDetaille.StatutRapport.VALIDE:
            return Response(
                {'error': _('Seuls les rapports validés peuvent être publiés')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rapport.publier_rapport()
        
        return Response({
            'message': _('Rapport publié avec succès'),
            'date_publication': rapport.date_publication
        })
    
    @action(detail=False, methods=['get'])
    def recents(self, request):
        """Retourne les rapports récents."""
        date_limite = timezone.now() - timedelta(days=30)
        rapports_recents = self.get_queryset().filter(
            date_generation__gte=date_limite
        )
        
        serializer = self.get_serializer(rapports_recents, many=True)
        return Response(serializer.data)
