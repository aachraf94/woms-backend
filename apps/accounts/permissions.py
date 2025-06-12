from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour les utilisateurs Admin seulement.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.ADMIN
        )

class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour les utilisateurs Manager ou Admin.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.Role.MANAGER, User.Role.ADMIN]
        )

class IsSupervisorOrHigher(permissions.BasePermission):
    """
    Permission personnalisée pour les utilisateurs Supervisor, Manager ou Admin.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.Role.SUPERVISOR, User.Role.MANAGER, User.Role.ADMIN]
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission personnalisée pour permettre aux utilisateurs de modifier leurs propres données
    ou aux admins de modifier toutes les données.
    """
    def has_object_permission(self, request, view, obj):
        # Permission de lecture pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Permission d'écriture seulement pour le propriétaire ou l'admin
        if hasattr(obj, 'utilisateur'):
            return obj.utilisateur == request.user or request.user.role == User.Role.ADMIN
        elif hasattr(obj, 'user'):
            return obj.user == request.user or request.user.role == User.Role.ADMIN
        else:
            return obj == request.user or request.user.role == User.Role.ADMIN
