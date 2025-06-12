from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import CustomUser, FournisseurService, ProfilUtilisateur, JournalConnexion, TokenJWT
from .serializers import (
    UserSerializer, RoleSerializer, EmailTokenObtainPairSerializer, 
    UserRoleChangeSerializer, ChangePasswordSerializer, FournisseurServiceSerializer,
    ProfilUtilisateurSerializer
)
from .permissions import IsAdmin, IsManagerOrAdmin
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import serializers
from rest_framework.views import APIView
from django.utils import timezone
import jwt
from django.conf import settings

User = get_user_model()

def get_client_ip(request):
    """Obtient l'adresse IP du client."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_journal_connexion(user, request, success=True):
    """Crée une entrée dans le journal de connexion."""
    JournalConnexion.objects.create(
        utilisateur=user,
        adresse_ip=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        type_connexion='API',
        succes_connexion=success
    )

# Authentication views (using Simple JWT)
@extend_schema(
    tags=["Authentication"],
    description="Point d'authentification pour la connexion."
)
class LoginView(TokenObtainPairView):
    """
    Point d'API pour la connexion utilisateur.
    Retourne les tokens d'accès et de rafraîchissement.
    """
    serializer_class = EmailTokenObtainPairSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Récupérer l'utilisateur depuis l'email
            email = request.data.get('email')
            try:
                user = User.objects.get(email=email)
                create_journal_connexion(user, request, success=True)
                
                # Créer des entrées de token JWT pour le suivi
                access_token = response.data.get('access')
                refresh_token = response.data.get('refresh')
                
                if access_token and refresh_token:
                    # Décoder les tokens pour obtenir les JTI
                    try:
                        access_payload = jwt.decode(access_token, options={"verify_signature": False})
                        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})
                        
                        # Créer les entrées de tokens
                        TokenJWT.objects.create(
                            utilisateur=user,
                            jti=access_payload.get('jti'),
                            type_token='ACCESS',
                            date_expiration=timezone.datetime.fromtimestamp(access_payload.get('exp'), tz=timezone.utc),
                            adresse_ip=get_client_ip(request)
                        )
                        
                        TokenJWT.objects.create(
                            utilisateur=user,
                            jti=refresh_payload.get('jti'),
                            type_token='REFRESH',
                            date_expiration=timezone.datetime.fromtimestamp(refresh_payload.get('exp'), tz=timezone.utc),
                            adresse_ip=get_client_ip(request)
                        )
                    except Exception as e:
                        # Log l'erreur mais ne pas échouer la connexion
                        pass
                        
            except User.DoesNotExist:
                pass
        
        return response


@extend_schema(
    tags=["Authentication"],
    description="Point pour rafraîchir les tokens d'accès JWT."
)
class RefreshTokenView(TokenRefreshView):
    """
    Point d'API pour rafraîchir les tokens d'accès.
    """
    permission_classes = [AllowAny]


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)

@extend_schema(
    tags=["Authentication"],
    description="Point pour déconnecter les utilisateurs en mettant leur token de rafraîchissement sur liste noire."
)
class LogoutView(APIView):
    """
    Point d'API pour la déconnexion utilisateur.
    Met le token de rafraîchissement sur liste noire.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    
    @extend_schema(
        request=LogoutSerializer, 
        responses={
            200: OpenApiResponse(
                description="Déconnexion réussie",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Token de rafraîchissement invalide")
        }
    )
    def post(self, request):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Mettre à jour le journal de connexion
            try:
                # Trouver la dernière session active de l'utilisateur
                derniere_session = JournalConnexion.objects.filter(
                    utilisateur=request.user,
                    date_deconnexion__isnull=True
                ).order_by('-date_connexion').first()
                
                if derniere_session:
                    derniere_session.terminer_session()
            except Exception:
                pass
            
            return Response(
                {"detail": "Déconnexion réussie."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    tags=["Gestion des utilisateurs"],
    description="Points d'API pour la gestion des utilisateurs."
)
class UserManagementViewSet(viewsets.ModelViewSet):
    """
    Points d'API pour la gestion des utilisateurs avec permissions appropriées.
    
    Les utilisateurs Admin peuvent gérer tous les utilisateurs du système.
    Les utilisateurs réguliers peuvent seulement accéder à leurs propres informations.
    """
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Les utilisateurs Admin peuvent voir tous les utilisateurs
        if user.role == User.Role.ADMIN:
            return User.objects.all()
        
        # Sinon, les utilisateurs peuvent seulement se voir eux-mêmes
        return User.objects.filter(id=user.id)
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [permissions.IsAuthenticated(), IsAdmin()]
        elif self.action in ['update', 'partial_update', 'change_user_role', 'deactivate_user']:
            return [permissions.IsAuthenticated(), IsManagerOrAdmin()]
        elif self.action == 'list':
            # Pour list, nous filtrerons les résultats basés sur le rôle dans get_queryset
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    @extend_schema(
        description="Changer le rôle d'un utilisateur (Admin seulement)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="ID Utilisateur"
            )
        ],
        request=UserRoleChangeSerializer,
        responses={
            200: OpenApiResponse(
                description="Rôle changé avec succès",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Rôle requis ou invalide"),
            403: OpenApiResponse(description="Permission refusée"),
            404: OpenApiResponse(description="Utilisateur non trouvé")
        }
    )
    @action(detail=True, methods=['patch'], url_path='change-role')
    @transaction.atomic
    def change_user_role(self, request, pk=None):
        user = self.get_object()
        
        role = request.data.get('role')
        if not role:
            return Response(
                {"detail": "Le rôle est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Valider le rôle
            if role not in [choice[0] for choice in User.Role.choices]:
                return Response(
                    {"detail": "Rôle invalide."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            user.role = role
            user.save()
                
            return Response(
                {"detail": f"Rôle utilisateur changé en {user.get_role_display()}."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @extend_schema(
        description="Désactiver un compte utilisateur (Admin ou Manager seulement)",
        parameters=[
            OpenApiParameter(
                name="pk",
                location=OpenApiParameter.PATH,
                type=int,
                description="ID Utilisateur"
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Utilisateur désactivé avec succès",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            403: OpenApiResponse(description="Permission refusée"),
            404: OpenApiResponse(description="Utilisateur non trouvé")
        }
    )
    @action(detail=True, methods=['patch'], url_path='deactivate')
    def deactivate_user(self, request, pk=None):
        user = self.get_object()
        
        user.est_actif = False
        user.save()
        return Response(
            {"detail": f"Compte utilisateur {user.email} a été désactivé."},
            status=status.HTTP_200_OK
        )


@extend_schema(
    tags=["Authentication"],
    description="Point pour que les utilisateurs changent leur mot de passe."
)
class ChangePasswordView(APIView):
    """
    Point d'API pour que les utilisateurs changent leur mot de passe.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    @extend_schema(
        request=ChangePasswordSerializer, 
        responses={
            200: OpenApiResponse(
                description="Mot de passe changé avec succès",
                response={"type": "object", "properties": {"detail": {"type": "string"}}}
            ),
            400: OpenApiResponse(description="Entrée invalide ou ancien mot de passe incorrect")
        }
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            # Vérifier si l'ancien mot de passe est correct
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": ["L'ancien mot de passe est incorrect."]}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Définir le nouveau mot de passe
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response(
                {"detail": "Mot de passe changé avec succès."}, 
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Fournisseurs de service"],
    description="Points d'API pour la gestion des fournisseurs de service."
)
class FournisseurServiceViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les fournisseurs de service."""
    serializer_class = FournisseurServiceSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return FournisseurService.objects.all()
        return FournisseurService.objects.filter(utilisateur=user)


@extend_schema(
    tags=["Profils utilisateurs"],
    description="Points d'API pour la gestion des profils utilisateurs."
)
class ProfilUtilisateurViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les profils utilisateurs."""
    serializer_class = ProfilUtilisateurSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == User.Role.ADMIN:
            return ProfilUtilisateur.objects.all()
        return ProfilUtilisateur.objects.filter(utilisateur=user)
    
    def perform_create(self, serializer):
        # Assurer que l'utilisateur ne peut créer un profil que pour lui-même
        if self.request.user.role != User.Role.ADMIN:
            serializer.save(utilisateur=self.request.user)
        else:
            serializer.save()


@extend_schema(
    tags=["Système"],
    description="Point pour obtenir les choix de rôles disponibles."
)
class RoleChoicesView(APIView):
    """
    Point d'API pour obtenir la liste des rôles disponibles.
    """
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="Liste des rôles",
                response={
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "display": {"type": "string"}
                        }
                    }
                }
            )
        }
    )
    def get(self, request):
        roles = [
            {"value": choice[0], "display": choice[1]}
            for choice in User.Role.choices
        ]
        return Response(roles, status=status.HTTP_200_OK)
