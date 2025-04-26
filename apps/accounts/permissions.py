from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admin users to access/modify
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.ADMIN
        )

class IsOperator(permissions.BasePermission):
    """
    Permission to only allow operator users to access/modify
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == User.Role.OPERATOR
        )

class IsManagerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow manager or admin users to access/modify
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in [User.Role.ADMIN, User.Role.MANAGER]
        )

