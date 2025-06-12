from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Well, WellOperation, DailyReport, WellDocument
from .region_models import Region, Forage, Phase, TypeOperation, Operation, Probleme, TypeIndicateur, Indicateur, Reservoir
from .serializers import (
    WellSerializer, WellDetailSerializer, WellOperationSerializer,
    DailyReportSerializer, WellDocumentSerializer,
    RegionSerializer, ForageSerializer, PhaseSerializer, 
    TypeOperationSerializer, OperationSerializer, ProblemeSerializer,
    TypeIndicateurSerializer, IndicateurSerializer, ReservoirSerializer
)
from apps.accounts.permissions import IsOperatorOrAbove, IsManagerOrAdmin
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

class WellViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing wells.
    """
    serializer_class = WellSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'location', 'description']
    ordering_fields = ['name', 'creation_date', 'status', 'start_date']
    ordering = ['-creation_date']
    
    def get_queryset(self):
        """
        This view should return a list of all wells for admins,
        or only active wells for regular users.
        """
        user = self.request.user
        queryset = Well.objects.all()
        
        # Filter by status if provided
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter archived wells
        show_archived = self.request.query_params.get('archived', 'false').lower() == 'true'
        if not show_archived:
            queryset = queryset.filter(is_archived=False)
            
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return WellDetailSerializer
        return WellSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, last_updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(last_updated_by=self.request.user)
    
    @extend_schema(
        description="Archive a well",
        responses={
            200: OpenApiResponse(description="Well archived successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Well not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='archive')
    def archive_well(self, request, pk=None):
        well = self.get_object()
        if not request.user.can_archive_wells:
            return Response(
                {"detail": "You don't have permission to archive wells."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        well.is_archived = True
        well.status = 'archived'
        well.last_updated_by = request.user
        well.save()
        
        return Response(
            {"detail": f"Well {well.name} has been archived."},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        description="Unarchive a well",
        responses={
            200: OpenApiResponse(description="Well unarchived successfully"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Well not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='unarchive')
    def unarchive_well(self, request, pk=None):
        well = self.get_object()
        if not request.user.can_archive_wells:
            return Response(
                {"detail": "You don't have permission to unarchive wells."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        well.is_archived = False
        # Keep the previous status rather than changing to active
        well.last_updated_by = request.user
        well.save()
        
        return Response(
            {"detail": f"Well {well.name} has been unarchived."},
            status=status.HTTP_200_OK
        )


class WellOperationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing well operations.
    """
    serializer_class = WellOperationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'well__name']
    ordering_fields = ['planned_start_date', 'operation_type', 'status']
    ordering = ['-planned_start_date']
    
    def get_queryset(self):
        """Return all operations or filter by well if specified."""
        queryset = WellOperation.objects.all()
        
        # Filter by well if provided
        well_id = self.request.query_params.get('well_id', None)
        if well_id:
            queryset = queryset.filter(well_id=well_id)
            
        # Filter by status if provided
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by operation type if provided
        operation_type = self.request.query_params.get('type', None)
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        description="Start an operation",
        responses={
            200: OpenApiResponse(description="Operation started successfully"),
            400: OpenApiResponse(description="Operation already started"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Operation not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='start')
    def start_operation(self, request, pk=None):
        operation = self.get_object()
        if not request.user.can_plan_operations:
            return Response(
                {"detail": "You don't have permission to start operations."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if operation.actual_start_date is not None:
            return Response(
                {"detail": "This operation has already been started."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        operation.actual_start_date = timezone.now()
        operation.status = 'active'
        operation.save()
        
        # Update the well status if needed
        well = operation.well
        if well.status in ['planned', 'paused']:
            well.status = 'active'
            well.last_updated_by = request.user
            well.save()
        
        return Response(
            {"detail": f"Operation {operation.name} has been started."},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        description="Complete an operation",
        responses={
            200: OpenApiResponse(description="Operation completed successfully"),
            400: OpenApiResponse(description="Operation not started or already completed"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Operation not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='complete')
    def complete_operation(self, request, pk=None):
        operation = self.get_object()
        if not request.user.can_plan_operations:
            return Response(
                {"detail": "You don't have permission to complete operations."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if operation.actual_start_date is None:
            return Response(
                {"detail": "Cannot complete an operation that hasn't started."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if operation.actual_end_date is not None:
            return Response(
                {"detail": "This operation has already been completed."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        operation.actual_end_date = timezone.now()
        operation.status = 'completed'
        operation.save()
        
        # Check if all operations for this well are completed
        well = operation.well
        active_operations = well.operations.exclude(status='completed').count()
        if active_operations == 0:
            well.status = 'completed'
            well.last_updated_by = request.user
            well.save()
        
        return Response(
            {"detail": f"Operation {operation.name} has been completed."},
            status=status.HTTP_200_OK
        )


class DailyReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing daily reports.
    """
    serializer_class = DailyReportSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['activities', 'issues', 'solutions', 'well__name']
    ordering_fields = ['report_date', 'submitted_at', 'well']
    ordering = ['-report_date']
    
    def get_queryset(self):
        """Return all reports or filter by well if specified."""
        queryset = DailyReport.objects.all()
        
        # Filter by well if provided
        well_id = self.request.query_params.get('well_id', None)
        if well_id:
            queryset = queryset.filter(well_id=well_id)
            
        # Filter by operation if provided
        operation_id = self.request.query_params.get('operation_id', None)
        if operation_id:
            queryset = queryset.filter(operation_id=operation_id)
            
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(report_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(report_date__lte=end_date)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)


class WellDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing well documents.
    """
    serializer_class = WellDocumentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'title', 'description', 'type', 'document_type', 'well__nom', 'well__name']
    ordering_fields = ['date_upload', 'uploaded_at', 'nom', 'title', 'type']
    ordering = ['-date_upload']
    
    def get_queryset(self):
        """Return all documents or filter by well if specified."""
        queryset = WellDocument.objects.all()
        
        # Filter by well if provided
        well_id = self.request.query_params.get('well_id', None)
        if well_id:
            queryset = queryset.filter(well_id=well_id)
            
        # Filter by document type if provided
        document_type = self.request.query_params.get('type', None)
        if document_type:
            queryset = queryset.filter(Q(type=document_type) | Q(document_type=document_type))
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploade_par=self.request.user, uploaded_by=self.request.user)


class RegionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing regions.
    """
    queryset = Region.objects.all()
    serializer_class = RegionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'code', 'localisation', 'responsable']
    ordering_fields = ['nom', 'code', 'created_at']
    ordering = ['nom']


class ForageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing drilling operations (forages).
    """
    queryset = Forage.objects.all()
    serializer_class = ForageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['puit__nom', 'puit__name']
    ordering_fields = ['date_debut', 'date_fin', 'cout', 'created_at']
    ordering = ['-date_debut']
    
    def get_queryset(self):
        queryset = Forage.objects.all()
        
        # Filter by well if provided
        well_id = self.request.query_params.get('well_id', None)
        if well_id:
            queryset = queryset.filter(puit_id=well_id)
            
        return queryset


class PhaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing drilling phases.
    """
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero_phase', 'diametre', 'description', 'forage__puit__nom']
    ordering_fields = ['numero_phase', 'date_debut_prevue', 'date_debut_reelle']
    ordering = ['forage', 'numero_phase']
    
    def get_queryset(self):
        queryset = Phase.objects.all()
        
        # Filter by forage if provided
        forage_id = self.request.query_params.get('forage_id', None)
        if forage_id:
            queryset = queryset.filter(forage_id=forage_id)
            
        return queryset


class TypeOperationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing operation types.
    """
    queryset = TypeOperation.objects.all()
    serializer_class = TypeOperationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'nom', 'description']
    ordering_fields = ['code', 'nom']
    ordering = ['code']


class OperationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing phase operations.
    """
    queryset = Operation.objects.all()
    serializer_class = OperationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'type_operation__nom', 'phase__numero_phase']
    ordering_fields = ['date_debut', 'date_fin', 'statut', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Operation.objects.all()
        
        # Filter by phase if provided
        phase_id = self.request.query_params.get('phase_id', None)
        if phase_id:
            queryset = queryset.filter(phase_id=phase_id)
            
        # Filter by status if provided
        statut = self.request.query_params.get('statut', None)
        if statut:
            queryset = queryset.filter(statut=statut)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ProblemeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing problems and incidents.
    """
    queryset = Probleme.objects.all()
    serializer_class = ProblemeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titre', 'description', 'solution']
    ordering_fields = ['date_detection', 'date_resolution', 'gravite', 'statut']
    ordering = ['-date_detection']
    
    def get_queryset(self):
        queryset = Probleme.objects.all()
        
        # Filter by various parameters
        gravite = self.request.query_params.get('gravite', None)
        if gravite:
            queryset = queryset.filter(gravite=gravite)
            
        statut = self.request.query_params.get('statut', None)
        if statut:
            queryset = queryset.filter(statut=statut)
            
        type_probleme = self.request.query_params.get('type', None)
        if type_probleme:
            queryset = queryset.filter(type_probleme=type_probleme)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(detecte_par=self.request.user)


class TypeIndicateurViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing indicator types.
    """
    queryset = TypeIndicateur.objects.all()
    serializer_class = TypeIndicateurSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'nom', 'unite', 'description']
    ordering_fields = ['code', 'nom']
    ordering = ['code']


class IndicateurViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing performance indicators.
    """
    queryset = Indicateur.objects.all()
    serializer_class = IndicateurSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['type_indicateur__nom', 'notes']
    ordering_fields = ['date_mesure', 'valeur']
    ordering = ['-date_mesure']
    
    def get_queryset(self):
        queryset = Indicateur.objects.all()
        
        # Filter by phase if provided
        phase_id = self.request.query_params.get('phase_id', None)
        if phase_id:
            queryset = queryset.filter(phase_id=phase_id)
            
        return queryset


class ReservoirViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing reservoir information.
    """
    queryset = Reservoir.objects.all()
    serializer_class = ReservoirSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'type_fluide', 'puit__nom']
    ordering_fields = ['profondeur', 'pression', 'temperature']
    ordering = ['profondeur']
    
    def get_queryset(self):
        queryset = Reservoir.objects.all()
        
        # Filter by well if provided
        well_id = self.request.query_params.get('well_id', None)
        if well_id:
            queryset = queryset.filter(puit_id=well_id)
            
        return queryset
