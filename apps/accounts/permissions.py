from rest_framework import permissions
from .models import Role

class IsAdmin(permissions.BasePermission):
    """
    Permission to only allow admin users to access/modify
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name == Role.ADMIN
        )

class IsOperator(permissions.BasePermission):
    """
    Permission to only allow operator users to access/modify
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name == Role.OPERATOR
        )

class IsManagerOrOperator(permissions.BasePermission):
    """
    Permission to only allow manager or operator users to access/modify
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role and 
            request.user.role.name in [Role.OPERATOR, Role.MANAGER]
        )

