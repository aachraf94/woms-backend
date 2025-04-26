from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        MANAGER = 'MANAGER', _('Manager')
        OPERATOR = 'OPERATOR', _('Operator')
    
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=255, blank=True)
    function = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Role field (enum instead of ForeignKey)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OPERATOR,
    )
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Username still required for createsuperuser
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    # Role-based permission methods
    @property
    def can_manage_users(self):
        return self.role == self.Role.ADMIN
    
    @property
    def can_manage_wells(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def can_manage_operations(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER, self.Role.OPERATOR]
    
    @property
    def can_view_analytics(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def can_archive_wells(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def can_plan_operations(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER, self.Role.OPERATOR]
    
    @classmethod
    def create_admin_user(cls, email, password, first_name='', last_name='', **extra_fields):
        """Helper method to create an admin user"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        extra_fields.setdefault('role', cls.Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        
        # Set username to be the same as email if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        user = User.objects.create_user(
            email=email, 
            password=password,
            first_name=first_name, 
            last_name=last_name, 
            **extra_fields
        )
        return user