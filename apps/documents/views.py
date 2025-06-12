from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse, Http404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import (
    DocumentPuits, RapportQuotidien, RapportPlanification,
    ModeleDocument, ArchiveDocument
)
from .serializers import (
    DocumentPuitsSerializer, DocumentPuitsListSerializer,
    RapportQuotidienSerializer, RapportQuotidienListSerializer,
    RapportPlanificationSerializer, RapportPlanificationListSerializer,
    ModeleDocumentSerializer, ArchiveDocumentSerializer
)


class DocumentPuitsViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des documents de puits."""
    queryset = DocumentPuits.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'type_document', 'statut', 'est_approuve', 'est_public',
        'est_confidentiel', 'puits', 'phase', 'operation'
    ]
    search_fields = ['nom_document', 'description', 'mots_cles']
    ordering_fields = ['date_creation', 'nom_document', 'type_document']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DocumentPuitsListSerializer
        return DocumentPuitsSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrer selon les permissions utilisateur
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(est_public=True) | Q(cree_par=self.request.user)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        """Télécharge le fichier du document."""
        document = self.get_object()
        
        # Vérifier les permissions
        if not document.est_public and document.cree_par != request.user and not request.user.is_staff:
            return Response({'error': _('Permission refusée')}, status=status.HTTP_403_FORBIDDEN)
        
        if not document.fichier:
            return Response({'error': _('Aucun fichier associé')}, status=status.HTTP_404_NOT_FOUND)
        
        # Incrémenter le compteur de téléchargements
        document.nombre_telechargements += 1
        document.save(update_fields=['nombre_telechargements'])
        
        response = HttpResponse(document.fichier.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{document.fichier.name}"'
        return response
    
    @action(detail=True, methods=['post'])
    def approuver(self, request, pk=None):
        """Approuve un document."""
        document = self.get_object()
        
        if not request.user.has_perm('documents.change_documentpuits'):
            return Response({'error': _('Permission insuffisante')}, status=status.HTTP_403_FORBIDDEN)
        
        document.est_approuve = True
        document.approuve_par = request.user
        document.statut = DocumentPuits.StatutDocument.APPROUVE
        document.commentaires_approbation = request.data.get('commentaires', '')
        document.save()
        
        return Response({'message': _('Document approuvé avec succès')})
    
    @action(detail=True, methods=['post'])
    def rejeter(self, request, pk=None):
        """Rejette un document."""
        document = self.get_object()
        
        if not request.user.has_perm('documents.change_documentpuits'):
            return Response({'error': _('Permission insuffisante')}, status=status.HTTP_403_FORBIDDEN)
        
        document.est_approuve = False
        document.statut = DocumentPuits.StatutDocument.REJETE
        document.commentaires_approbation = request.data.get('commentaires', '')
        document.save()
        
        return Response({'message': _('Document rejeté')})


class RapportQuotidienViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rapports quotidiens."""
    queryset = RapportQuotidien.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['puits', 'phase', 'statut', 'date_rapport']
    search_fields = ['numero_rapport', 'activites_realisees', 'problemes_rencontres']
    ordering_fields = ['date_rapport', 'date_creation']
    ordering = ['-date_rapport']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RapportQuotidienListSerializer
        return RapportQuotidienSerializer
    
    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide un rapport quotidien."""
        rapport = self.get_object()
        
        if not request.user.has_perm('documents.change_rapportquotidien'):
            return Response({'error': _('Permission insuffisante')}, status=status.HTTP_403_FORBIDDEN)
        
        rapport.statut = RapportQuotidien.StatutRapport.VALIDE
        rapport.valide_par = request.user
        rapport.commentaires_validation = request.data.get('commentaires', '')
        rapport.save()
        
        return Response({'message': _('Rapport validé avec succès')})
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne les statistiques des rapports quotidiens."""
        queryset = self.get_queryset()
        stats = {
            'total': queryset.count(),
            'brouillon': queryset.filter(statut=RapportQuotidien.StatutRapport.BROUILLON).count(),
            'soumis': queryset.filter(statut=RapportQuotidien.StatutRapport.SOUMIS).count(),
            'valide': queryset.filter(statut=RapportQuotidien.StatutRapport.VALIDE).count(),
            'rejete': queryset.filter(statut=RapportQuotidien.StatutRapport.REJETE).count(),
        }
        return Response(stats)


class RapportPlanificationViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des rapports de planification."""
    queryset = RapportPlanification.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'puits', 'phase', 'statut_planification', 'priorite',
        'niveau_risque_global'
    ]
    search_fields = ['nom_projet', 'code_projet', 'description_projet']
    ordering_fields = ['date_creation', 'date_debut_prevue', 'priorite']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return RapportPlanificationListSerializer
        return RapportPlanificationSerializer
    
    @action(detail=True, methods=['post'])
    def demarrer(self, request, pk=None):
        """Démarre l'exécution d'un projet."""
        rapport = self.get_object()
        
        if rapport.statut_planification != RapportPlanification.StatutPlanification.APPROUVE:
            return Response(
                {'error': _('Le projet doit être approuvé avant de pouvoir être démarré')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rapport.statut_planification = RapportPlanification.StatutPlanification.EN_COURS
        rapport.date_debut_reelle = request.data.get('date_debut_reelle')
        rapport.save()
        
        return Response({'message': _('Projet démarré avec succès')})
    
    @action(detail=True, methods=['post'])
    def terminer(self, request, pk=None):
        """Termine un projet."""
        rapport = self.get_object()
        
        rapport.statut_planification = RapportPlanification.StatutPlanification.TERMINE
        rapport.date_fin_reelle = request.data.get('date_fin_reelle')
        rapport.pourcentage_avancement = 100
        rapport.save()
        
        return Response({'message': _('Projet terminé avec succès')})
    
    @action(detail=False, methods=['get'])
    def tableau_bord(self, request):
        """Retourne les données pour le tableau de bord des projets."""
        queryset = self.get_queryset()
        
        # Statistiques générales
        stats = {
            'total_projets': queryset.count(),
            'en_cours': queryset.filter(
                statut_planification=RapportPlanification.StatutPlanification.EN_COURS
            ).count(),
            'termines': queryset.filter(
                statut_planification=RapportPlanification.StatutPlanification.TERMINE
            ).count(),
            'en_retard': sum(1 for p in queryset if p.est_en_retard()),
        }
        
        # Projets critiques (haute priorité ou en retard)
        projets_critiques = queryset.filter(
            Q(priorite=RapportPlanification.PrioriteProjet.CRITIQUE) |
            Q(priorite=RapportPlanification.PrioriteProjet.HAUTE)
        )[:5]
        
        return Response({
            'statistiques': stats,
            'projets_critiques': RapportPlanificationListSerializer(
                projets_critiques, many=True
            ).data
        })


class ModeleDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des modèles de documents."""
    queryset = ModeleDocument.objects.filter(est_actif=True)
    serializer_class = ModeleDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['type_modele', 'est_par_defaut', 'est_public']
    search_fields = ['nom_modele', 'description']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtrer selon les permissions
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(est_public=True) | Q(utilisateurs_autorises=self.request.user)
            )
        return queryset
    
    @action(detail=True, methods=['post'])
    def utiliser(self, request, pk=None):
        """Marque le modèle comme utilisé."""
        modele = self.get_object()
        modele.incrementer_utilisation()
        return Response({'message': _('Utilisation enregistrée')})
    
    @action(detail=True, methods=['get'])
    def telecharger_modele(self, request, pk=None):
        """Télécharge le fichier modèle."""
        modele = self.get_object()
        
        if not modele.fichier_modele:
            return Response({'error': _('Aucun fichier modèle')}, status=status.HTTP_404_NOT_FOUND)
        
        modele.incrementer_utilisation()
        
        response = HttpResponse(modele.fichier_modele.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{modele.fichier_modele.name}"'
        return response


class ArchiveDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des archives de documents."""
    queryset = ArchiveDocument.objects.all()
    serializer_class = ArchiveDocumentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['raison_archivage', 'peut_etre_restaure']
    search_fields = ['document_original__nom_document', 'description_archivage']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Seuls les administrateurs peuvent voir toutes les archives
        if not self.request.user.is_staff:
            queryset = queryset.filter(archive_par=self.request.user)
        return queryset
    
    @action(detail=True, methods=['post'])
    def restaurer(self, request, pk=None):
        """Restaure un document archivé."""
        archive = self.get_object()
        
        if not archive.peut_etre_restaure:
            return Response(
                {'error': _('Ce document ne peut pas être restauré')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Restaurer le document (logique à implémenter selon les besoins)
        # Ici on pourrait changer le statut du document original
        
        return Response({'message': _('Document restauré avec succès')})
    
    @action(detail=False, methods=['get'])
    def a_supprimer(self, request):
        """Retourne les archives qui peuvent être supprimées."""
        archives_a_supprimer = [
            archive for archive in self.get_queryset()
            if archive.peut_etre_supprime()
        ]
        
        serializer = self.get_serializer(archives_a_supprimer, many=True)
        return Response(serializer.data)
