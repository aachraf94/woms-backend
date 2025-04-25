from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import CustomUser, Role
from .serializers import (
    UserSerializer, RoleSerializer, EmailTokenObtainPairSerializer, 
    UserRoleChangeSerializer, ChangePasswordSerializer
)
from .permissions import IsAdmin, IsManagerOrAdmin
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import serializers
from rest_framework.views import APIView

User = get_user_model()

# Authentication views (using Simple JWT)
@extend_schema(
    tags=["Authentication"],
    description="Authentication endpoint for logging in."
)
class LoginView(TokenObtainPairView):
    """
    API endpoint for user login.
    Returns access and refresh tokens.
    """
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Authentication"],
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
    tags=["Authentication"],
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
    tags=["User Management"],
    description="API endpoints for managing users."
)
class UserManagementViewSet(viewsets.ModelViewSet):
    """
    API endpoints for user management with appropriate permissions.
    
    Admin users can manage all users in the system.
    Regular users can only access their own information.
    """
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin users can see all users
        if user.role and user.role.name == Role.ADMIN:
            return User.objects.all()
        
        # Otherwise, users can only see themselves
        return User.objects.filter(id=user.id)
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ['update', 'partial_update', 'change_user_role', 'deactivate_user']:
            return [permissions.IsAuthenticated(), IsManagerOrAdmin()]
        elif self.action == 'list':
            # For list, we'll filter results based on role in get_queryset
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    @extend_schema(
        description="Change a user's role (Admin only)",
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
        
        role_id = request.data.get('role_id')
        if not role_id:
            return Response(
                {"detail": "Role ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            role = Role.objects.get(id=role_id)
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
        description="Deactivate a user account (Admin or Manager only)",
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
        
        user.is_active = False
        user.save()
        return Response(
            {"detail": f"User account {user.email} has been deactivated."},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Authentication"],
    description="Endpoint for users to change their password."
)
class ChangePasswordView(APIView):
    """
    API endpoint for users to change their password.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    @extend_schema(
        request=ChangePasswordSerializer, 
        responses={
            200: OpenApiResponse(
                description="Password changed successfully",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Invalid input or old password incorrect")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Check if old password is correct
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": ["Old password is incorrect."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {"detail": "Password changed successfully."}, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Role Management"],
    description="API endpoints for viewing role information."
)
class RoleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing role information.
    Roles are predefined and cannot be modified through the API.
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
