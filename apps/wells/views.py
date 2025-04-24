from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Well, WellOperation, DailyReport, WellDocument
from .serializers import (
    WellSerializer, WellDetailSerializer, WellOperationSerializer,
    DailyReportSerializer, WellDocumentSerializer
)
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
        if not request.user.role.can_archive_wells:
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
        if not request.user.role.can_archive_wells:
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
        if not request.user.role.can_plan_operations:
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
        if not request.user.role.can_plan_operations:
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
    search_fields = ['title', 'description', 'document_type', 'well__name']
    ordering_fields = ['uploaded_at', 'title', 'document_type']
    ordering = ['-uploaded_at']
    
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
            queryset = queryset.filter(document_type=document_type)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
