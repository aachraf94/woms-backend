from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action, permission_classes, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import CustomUser, Role, Agency
from .serializers import UserSerializer, RoleSerializer, AgencySerializer, EmailTokenObtainPairSerializer, AgencyAdminSerializer, UserRoleChangeSerializer
from .permissions import IsSuperAdmin, IsAgencyAdmin, IsSuperAdminOrAgencyAdmin
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from rest_framework.views import APIView

User = get_user_model()

# Authentication views (using Simple JWT)
@extend_schema(
    tags=["Accounts: Authentication"],
    description="Authentication endpoints for logging in and managing tokens."
)
class LoginView(TokenObtainPairView):
    """
    API endpoint for user login.
    Returns access and refresh tokens.
    """
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Accounts: Authentication"],
    description="Endpoint for refreshing JWT access tokens."
)
class RefreshTokenView(TokenRefreshView):
    """
    API endpoint for refreshing access tokens.
    """
    permission_classes = [AllowAny]


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

@extend_schema(
    tags=["Accounts: Authentication"],
    description="Endpoint for logging out users by blacklisting their refresh token."
)
class LogoutView(APIView):
    """
    API endpoint for user logout.
    Blacklists the refresh token.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    
    @extend_schema(
        request=LogoutSerializer, 
        responses={
            200: OpenApiResponse(
                description="Successfully logged out",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Invalid refresh token")
        }
    )
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"detail": "Successfully logged out."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=["Accounts: User Management"],
    description="API endpoints for managing users including creation, role management, and deactivation."
)
class UserManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoints for user management with appropriate permissions.
    
    SuperAdmins can manage all users in the system.
    Agency Admins can manage users in their agency.
    Regular users can only access their own information.
    """
    serializer_class = UserSerializer
    
    @extend_schema(
        description="List users based on the requester's permissions",
        responses={200: UserSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """
        List users based on the requester's permissions:
        - SuperAdmin: all users
        - Agency Admin: users in their agency
        - Regular user: only themselves
        """
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description="Retrieve a specific user by ID",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="User ID"
            )
        ],
        responses={
            200: UserSerializer,
            404: OpenApiResponse(description="User not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """Get a specific user by ID."""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description="Create a new user (SuperAdmin only)",
        request=UserSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description="Invalid input data")
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a new user (SuperAdmin only)."""
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description="Update a user (SuperAdmin or Agency Admin for their agency's users)",
        request=UserSerializer,
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="User ID"
            )
        ],
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid input data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="User not found")
        }
    )
    def update(self, request, *args, **kwargs):
        """Update a user (SuperAdmin or Agency Admin for their agency's users)."""
        return super().update(request, *args, **kwargs)
    
    def get_queryset(self):
        user = self.request.user
        
        if hasattr(user, 'role') and user.role.can_manage_users and user.is_superuser:
            return User.objects.all()
        
        elif hasattr(user, 'role') and user.role.can_manage_users and user.administered_agencies.exists():
            return User.objects.filter(agency__in=user.administered_agencies.all())
        
        return User.objects.filter(id=user.id)
    
    def get_permissions(self):
        if self.action in ['create', 'import_users_from_rh', 'list_all_users']:
            return [permissions.IsAuthenticated(), IsSuperAdmin()]
        elif self.action in ['update', 'partial_update', 'change_user_role', 'deactivate_user']:
            return [permissions.IsAuthenticated(), IsSuperAdminOrAgencyAdmin()]
        elif self.action == 'list_agency_users':
            return [permissions.IsAuthenticated(), IsAgencyAdmin()]
        return [permissions.IsAuthenticated()]
    
    @extend_schema(
        description="Import users from Yalidine RH API (SuperAdmin only)",
        responses={
            202: OpenApiResponse(
                description="Import task initiated",
                response={
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"},
                        "task_id": {"type": "string"},
                        "status": {"type": "string"}
                    }
                }
            ),
            500: OpenApiResponse(description="Failed to initiate import task")
        }
    )
    @action(detail=False, methods=['post'], url_path='import-from-rh')
    def import_users_from_rh(self, request):
        from .tasks import sync_users_task
        
        try:
            task = sync_users_task.apply_async(
                countdown=1,
                expires=3600,
                retry=True,
                retry_policy={
                    'max_retries': 3,
                    'interval_start': 60,
                    'interval_step': 60,
                    'interval_max': 300,
                }
            )
            
            return Response({
                "detail": "User import from RH API initiated.",
                "task_id": task.id,
                "status": "PENDING"
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response({
                "detail": f"Failed to initiate import task: {str(e)}",
                "status": "ERROR"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        description="Change a user's role (SuperAdmin or Agency Admin for their agency's users)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="User ID"
            )
        ],
        request=UserRoleChangeSerializer,
        responses={
            200: OpenApiResponse(
                description="Role changed successfully",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Role ID is required or invalid"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="User or role not found")
        }
    )
    @action(detail=True, methods=['patch'], url_path='change-role')
    @transaction.atomic
    def change_user_role(self, request, pk=None):
        user = self.get_object()
        
        if not request.user.is_superuser and user.agency not in request.user.administered_agencies.all():
            return Response(
                {"detail": "You don't have permission to modify this user's role."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        role_id = request.data.get('role_id')
        if not role_id:
            return Response(
                {"detail": "Role ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            role = Role.objects.get(id=role_id)
            
            if role.name == "Admin" and user.agency:
                user.agency.add_admin(user)
                
            user.role = role
            user.save()
                
            return Response(
                {"detail": f"User role changed to {role.name}."},
                status=status.HTTP_200_OK
            )
        except Role.DoesNotExist:
            return Response(
                {"detail": "Role not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        description="Deactivate a user account (SuperAdmin or Agency Admin for their agency's users)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="User ID"
            )
        ],
        responses={
            200: OpenApiResponse(
                description="User deactivated successfully",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="User not found")
        }
    )
    @action(detail=True, methods=['patch'], url_path='deactivate')
    def deactivate_user(self, request, pk=None):
        user = self.get_object()
        
        if not request.user.is_superuser and user.agency not in request.user.administered_agencies.all():
            return Response(
                {"detail": "You don't have permission to deactivate this user."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = False
        user.save()
        return Response(
            {"detail": f"User account {user.email} has been deactivated."},
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        description="List all users in the system (SuperAdmin only)",
        responses={
            200: UserSerializer(many=True),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    @action(detail=False, methods=['get'], url_path='all')
    def list_all_users(self, request):
        queryset = User.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description="List all users in the admin's agencies (Agency Admin only)",
        responses={
            200: UserSerializer(many=True),
            403: OpenApiResponse(description="Not an admin of any agency")
        }
    )
    @action(detail=False, methods=['get'], url_path='agency')
    def list_agency_users(self, request):
        if not request.user.administered_agencies.exists():
            return Response(
                {"detail": "You are not an admin of any agency."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        queryset = User.objects.filter(agency__in=request.user.administered_agencies.all())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Accounts: Role Management"],
    description="API endpoints for managing user roles and permissions."
)
class RoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for role management.
    
    Roles define sets of permissions that can be assigned to users.
    Most operations are restricted to SuperAdmin users.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    
    @extend_schema(
        description="List all roles",
        responses={200: RoleSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description="Retrieve details for a specific role",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Role ID"
            )
        ],
        responses={
            200: RoleSerializer,
            404: OpenApiResponse(description="Role not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description="Create a new role (SuperAdmin only)",
        request=RoleSerializer,
        responses={
            201: RoleSerializer,
            400: OpenApiResponse(description="Invalid input data"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        description="Update a role (SuperAdmin only)",
        request=RoleSerializer,
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Role ID"
            )
        ],
        responses={
            200: RoleSerializer,
            400: OpenApiResponse(description="Invalid input data"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Role not found")
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsSuperAdmin()]
    
    @extend_schema(
        description="Delete a role if it has no associated users (SuperAdmin only)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Role ID"
            )
        ],
        responses={
            204: OpenApiResponse(description="Role deleted successfully"),
            400: OpenApiResponse(description="Role has associated users"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Role not found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        role = self.get_object()
        
        if role.users_count > 0:
            return Response(
                {"detail": "Cannot delete role with associated users. Reassign users first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    tags=["Accounts: Agency Management"],
    description="API endpoints for managing agencies, including creation, deletion, and admin assignment."
)
class AgencyManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoints for agency management with appropriate permissions.
    Only SuperAdmin can access most operations.
    """
    serializer_class = AgencySerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    
    @extend_schema(
        description="List all agencies (SuperAdmin only)",
        responses={200: AgencySerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        description="Retrieve details for a specific agency",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Agency ID"
            )
        ],
        responses={
            200: AgencySerializer,
            404: OpenApiResponse(description="Agency not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        description="Create a new agency (SuperAdmin only)",
        request=AgencySerializer,
        responses={
            201: AgencySerializer,
            400: OpenApiResponse(description="Invalid input data"),
            403: OpenApiResponse(description="Permission denied")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    def get_queryset(self):
        return Agency.objects.all()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @extend_schema(
        description="Add an admin to an agency (SuperAdmin only)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Agency ID"
            )
        ],
        request=AgencyAdminSerializer,
        responses={
            200: OpenApiResponse(
                description="Admin added successfully",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Invalid user ID or user already admin of another agency"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Agency or user not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='add-admin')
    @transaction.atomic
    def add_agency_admin(self, request, pk=None):
        agency = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"detail": "User ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            new_admin = User.objects.get(id=user_id)
            
            if new_admin.agency != agency:
                return Response(
                    {"detail": f"User {new_admin.email} is not affiliated with agency {agency.name}. Cannot add as admin."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_admin.administered_agencies.exists() and new_admin not in agency.admins.all():
                return Response(
                    {"detail": f"User {new_admin.email} is already an admin of another agency."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            admin_role, created = Role.objects.get_or_create(
                name="Admin",
                defaults={
                    'can_manage_users': True,
                    'can_access_dashboard': True,
                    'can_view_history': True,
                    'can_search_vendors': True,
                }
            )
            
            agency.admins.add(new_admin)
            
            new_admin.role = admin_role
            new_admin.save()
            
            return Response(
                {"detail": f"{new_admin.get_full_name()} is now an admin of {agency.name}."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        description="Remove an admin from an agency (SuperAdmin only)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Agency ID"
            )
        ],
        request=AgencyAdminSerializer,
        responses={
            200: OpenApiResponse(
                description="Admin removed successfully",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Invalid user ID or user not an admin of this agency"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Agency or user not found")
        }
    )
    @action(detail=True, methods=['post'], url_path='remove-admin')
    @transaction.atomic
    def remove_agency_admin(self, request, pk=None):
        agency = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {"detail": "User ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            admin_to_remove = User.objects.get(id=user_id)
            
            if admin_to_remove not in agency.admins.all():
                return Response(
                    {"detail": "This user is not an admin of this agency."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            agency.remove_admin(admin_to_remove)
            
            if admin_to_remove.role and admin_to_remove.role.name == "Admin":
                if not admin_to_remove.administered_agencies.exists():
                    admin_to_remove.role = None
                    admin_to_remove.save()
            
            return Response(
                {"detail": f"{admin_to_remove.get_full_name()} is no longer an admin of {agency.name}."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        description="Delete an agency if it has no associated users (SuperAdmin only)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="Agency ID"
            )
        ],
        responses={
            204: OpenApiResponse(description="Agency deleted successfully"),
            400: OpenApiResponse(description="Agency has associated users"),
            403: OpenApiResponse(description="Permission denied"),
            404: OpenApiResponse(description="Agency not found")
        }
    )
    def destroy(self, request, *args, **kwargs):
        agency = self.get_object()
        
        if agency.users.exists():
            return Response(
                {"detail": "Cannot delete agency with associated users. Reassign users first."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        agency.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
