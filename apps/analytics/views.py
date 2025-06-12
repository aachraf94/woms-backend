from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import (
    JeuDonneesAnalytiques, AnalyseEcart, InteractionAssistantIA,
    IndicateurPerformance, AnalyseReservoir, TableauBordKPI,
    AnalysePredictive, AlerteAnalytique
)
from .serializers import (
    JeuDonneesAnalytiquesSerializer, AnalyseEcartSerializer,
    InteractionAssistantIASerializer, IndicateurPerformanceSerializer,
    AnalyseReservoirSerializer, TableauBordKPISerializer,
    AnalysePredictiveSerializer, AlerteAnalytiqueSerializer,
    StatistiquesAnalytiquesSerializer, ResumePerformanceSerializer
)


class JeuDonneesAnalytiquesViewSet(viewsets.ModelViewSet):
    """ViewSet pour JeuDonneesAnalytiques."""
    queryset = JeuDonneesAnalytiques.objects.all()
    serializer_class = JeuDonneesAnalytiquesSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type_donnees', 'puits', 'source_donnees']
    search_fields = ['nom_jeu_donnees', 'source_donnees']
    ordering_fields = ['date_creation', 'nom_jeu_donnees']
    ordering = ['-date_creation']

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)


class AnalyseEcartViewSet(viewsets.ModelViewSet):
    """ViewSet pour AnalyseEcart."""
    queryset = AnalyseEcart.objects.all()
    serializer_class = AnalyseEcartSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type_indicateur', 'niveau_criticite', 'phase']
    search_fields = ['commentaire', 'actions_correctives']
    ordering_fields = ['date_analyse', 'pourcentage_ecart']
    ordering = ['-date_analyse']

    def perform_create(self, serializer):
        serializer.save(analyseur=self.request.user)

    @action(detail=False, methods=['get'])
    def par_criticite(self, request):
        """Statistiques des analyses par niveau de criticité."""
        stats = self.queryset.values('niveau_criticite').annotate(
            count=Count('id')
        )
        return Response(stats)


class InteractionAssistantIAViewSet(viewsets.ModelViewSet):
    """ViewSet pour InteractionAssistantIA."""
    queryset = InteractionAssistantIA.objects.all()
    serializer_class = InteractionAssistantIASerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type_requete', 'statut', 'puits_associe']
    search_fields = ['requete', 'reponse']
    ordering_fields = ['horodatage_creation', 'score_pertinence']
    ordering = ['-horodatage_creation']

    def get_queryset(self):
        return self.queryset.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class IndicateurPerformanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour IndicateurPerformance."""
    queryset = IndicateurPerformance.objects.all()
    serializer_class = IndicateurPerformanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['statut', 'operation', 'type_indicateur']
    search_fields = ['commentaire']
    ordering_fields = ['date_mesure', 'pourcentage_realisation']
    ordering = ['-date_mesure']

    def perform_create(self, serializer):
        serializer.save(mesure_par=self.request.user)


class AnalyseReservoirViewSet(viewsets.ModelViewSet):
    """ViewSet pour AnalyseReservoir."""
    queryset = AnalyseReservoir.objects.all()
    serializer_class = AnalyseReservoirSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['nature_fluide', 'statut_analyse', 'puits']
    search_fields = ['nom_analyse', 'observations']
    ordering_fields = ['date_analyse', 'nom_analyse']
    ordering = ['-date_analyse']

    def perform_create(self, serializer):
        serializer.save(analyste=self.request.user)


class TableauBordKPIViewSet(viewsets.ModelViewSet):
    """ViewSet pour TableauBordKPI."""
    queryset = TableauBordKPI.objects.all()
    serializer_class = TableauBordKPISerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['categorie_kpi', 'statut_kpi', 'puits']
    search_fields = ['nom_kpi']
    ordering_fields = ['date_calcul', 'pourcentage_atteinte']
    ordering = ['-date_calcul']

    def perform_create(self, serializer):
        serializer.save(calcule_par=self.request.user)

    @action(detail=False, methods=['get'])
    def resume_performance(self, request):
        """Résumé des performances par puits."""
        puits_id = request.query_params.get('puits_id')
        if not puits_id:
            return Response(
                {'error': 'puits_id parameter required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        kpis = self.queryset.filter(puits_id=puits_id)
        
        if not kpis.exists():
            return Response(
                {'error': 'No KPIs found for this well'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        resume = {
            'puits_id': int(puits_id),
            'puits_nom': kpis.first().puits.nom,
            'nombre_kpis': kpis.count(),
            'kpis_excellents': kpis.filter(statut_kpi='EXCELLENT').count(),
            'kpis_critiques': kpis.filter(statut_kpi='CRITIQUE').count(),
            'alertes_actives': AlerteAnalytique.objects.filter(
                puits_id=puits_id, 
                statut_alerte='NOUVELLE'
            ).count(),
            'derniere_analyse': kpis.first().date_calcul,
            'score_performance_global': kpis.aggregate(
                avg_atteinte=Avg('pourcentage_atteinte')
            )['avg_atteinte'] or 0
        }
        
        serializer = ResumePerformanceSerializer(resume)
        return Response(serializer.data)


class AnalysePredictiveViewSet(viewsets.ModelViewSet):
    """ViewSet pour AnalysePredictive."""
    queryset = AnalysePredictive.objects.all()
    serializer_class = AnalysePredictiveSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type_prediction', 'statut_prediction', 'puits']
    search_fields = ['nom_analyse', 'modele_utilise', 'observations']
    ordering_fields = ['date_creation', 'date_prediction_pour']
    ordering = ['-date_creation']

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)


class AlerteAnalytiqueViewSet(viewsets.ModelViewSet):
    """ViewSet pour AlerteAnalytique."""
    queryset = AlerteAnalytique.objects.all()
    serializer_class = AlerteAnalytiqueSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['type_alerte', 'niveau_urgence', 'statut_alerte', 'puits']
    search_fields = ['titre_alerte', 'description']
    ordering_fields = ['date_declenchement', 'niveau_urgence']
    ordering = ['-date_declenchement']

    @action(detail=True, methods=['post'])
    def resoudre(self, request, pk=None):
        """Marquer une alerte comme résolue."""
        alerte = self.get_object()
        alerte.statut_alerte = 'RESOLUE'
        alerte.date_resolution = timezone.now()
        alerte.resolu_par = request.user
        alerte.actions_prises = request.data.get('actions_prises', '')
        alerte.save()
        
        serializer = self.get_serializer(alerte)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Statistiques générales des analyses."""
        stats = {
            'total_jeux_donnees': JeuDonneesAnalytiques.objects.count(),
            'total_analyses_ecart': AnalyseEcart.objects.count(),
            'total_interactions_ia': InteractionAssistantIA.objects.count(),
            'total_alertes_actives': AlerteAnalytique.objects.filter(
                statut_alerte='NOUVELLE'
            ).count(),
            'moyenne_score_pertinence_ia': InteractionAssistantIA.objects.aggregate(
                avg_score=Avg('score_pertinence')
            )['avg_score'] or 0,
            'repartition_types_alertes': dict(
                AlerteAnalytique.objects.values('type_alerte').annotate(
                    count=Count('id')
                ).values_list('type_alerte', 'count')
            ),
            'evolution_kpis': list(
                TableauBordKPI.objects.filter(
                    date_calcul__gte=timezone.now() - timedelta(days=30)
                ).values('date_calcul__date').annotate(
                    avg_performance=Avg('pourcentage_atteinte')
                ).order_by('date_calcul__date')
            )
        }
        
        serializer = StatistiquesAnalytiquesSerializer(stats)
        return Response(serializer.data)
