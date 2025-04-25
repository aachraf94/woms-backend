from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    ADMIN = 'Admin'
    MANAGER = 'Manager'
    OPERATOR = 'Operator'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
        (OPERATOR, 'Operator'),
    ]
    
    name = models.CharField(max_length=100, choices=ROLE_CHOICES, unique=True)
    
    # Permissions based on role
    can_manage_users = models.BooleanField(default=False)
    can_manage_wells = models.BooleanField(default=False)
    can_manage_operations = models.BooleanField(default=False)
    can_view_analytics = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Set default permissions based on role name
        if self.name == self.ADMIN:
            self.can_manage_users = True
            self.can_manage_wells = True
            self.can_manage_operations = True
            self.can_view_analytics = True
        elif self.name == self.MANAGER:
            self.can_manage_wells = True
            self.can_manage_operations = True
            self.can_view_analytics = True
        elif self.name == self.OPERATOR:
            self.can_manage_operations = True
            
        super().save(*args, **kwargs)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=255, blank=True)
    function = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Relation with role
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, related_name='users', null=True, blank=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Username still required for createsuperuser
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @classmethod
    def create_admin_user(cls, email, password, first_name='', last_name='', **extra_fields):
        """Helper method to create an admin user"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Ensure admin role exists
        admin_role, created = Role.objects.get_or_create(
            name=Role.ADMIN
        )
        
        extra_fields.setdefault('role', admin_role)
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