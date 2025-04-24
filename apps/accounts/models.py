from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.exceptions import ValidationError


class Agency(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    admins = models.ManyToManyField('CustomUser', blank=True, related_name='administered_agencies')

    class Meta:
        verbose_name_plural = "Agencies"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    @classmethod
    def create_agency(cls, name, location=None, **kwargs):
        """Helper method to create an agency with additional fields"""
        agency = cls(name=name, location=location, **kwargs)
        agency.save()
        return agency
        
    def get_users_count(self):
        """Return the number of users associated with this agency"""
        return self.users.count()

    def add_admin(self, user):
        """Add a user as an admin of this agency"""
        # Check if the user is affiliated with this agency
        if user.agency != self:
            raise ValueError(f"User {user} is not affiliated with agency {self}. Cannot add as admin.")
        
        # Check if user is already an admin of any agency (should only be this one)
        if user.administered_agencies.exists() and user not in self.admins.all():
            raise ValueError(f"User {user} is already an admin of another agency. Cannot be admin of multiple agencies.")
            
        self.admins.add(user)
    
    def remove_admin(self, user):
        """Remove a user as an admin of this agency"""
        self.admins.remove(user)


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    users_count = models.PositiveIntegerField(default=0)
    
    # WOMS specific permissions as boolean fields
    can_access_dashboard = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    can_manage_permissions = models.BooleanField(default=False)
    
    # Wells management permissions
    can_create_wells = models.BooleanField(default=False)
    can_edit_wells = models.BooleanField(default=False)
    can_delete_wells = models.BooleanField(default=False)
    can_view_wells = models.BooleanField(default=True)
    can_archive_wells = models.BooleanField(default=False)
    
    # Operations permissions
    can_plan_operations = models.BooleanField(default=False)
    can_submit_reports = models.BooleanField(default=False)
    can_approve_reports = models.BooleanField(default=False)
    
    # Analytics permissions
    can_access_analytics = models.BooleanField(default=False)
    can_export_data = models.BooleanField(default=False)
    can_use_assistant = models.BooleanField(default=False)
    
    # Alerts permissions
    can_create_alerts = models.BooleanField(default=False)
    can_manage_alerts = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    agency = models.ForeignKey('Agency', on_delete=models.PROTECT, null=True, related_name='users')
    company = models.CharField(max_length=255, blank=True)
    function = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Relation avec le rôle (one-to-many)
    role = models.ForeignKey('Role', on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Username still required for createsuperuser
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @classmethod
    def create_superAdmin_with_role(cls, email, password, first_name='', last_name='', **extra_fields):
        """Helper method to create a superuser with a role"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Ensure admin role exists
        SuperAdmin_role, created = Role.objects.get_or_create(
            name="Super Admin",
            defaults={
                'can_access_dashboard': True,
                'can_manage_users': True,
                'can_manage_permissions': True,
                'can_create_wells': True,
                'can_edit_wells': True,
                'can_delete_wells': True,
                'can_view_wells': True,
                'can_archive_wells': True,
                'can_plan_operations': True,
                'can_submit_reports': True,
                'can_approve_reports': True,
                'can_access_analytics': True,
                'can_export_data': True,
                'can_use_assistant': True,
                'can_create_alerts': True,
                'can_manage_alerts': True,
            }
        )
        
        extra_fields.setdefault('role', SuperAdmin_role)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Set username to be the same as email if not provided
        if 'username' not in extra_fields:
            extra_fields['username'] = email
        
        # Don't pass username separately since it's already in extra_fields
        user = User.objects.create_user(email=email, password=password, 
                                       first_name=first_name, last_name=last_name, **extra_fields)
        return user
    

# Signal handlers to keep users_count updated
@receiver(post_save, sender=CustomUser)
def update_role_count_on_save(sender, instance, **kwargs):
    """Update role.users_count when a user is created or updated"""
    if instance.role:
        instance.role.users_count = CustomUser.objects.filter(role=instance.role).count()
        instance.role.save()

@receiver(post_delete, sender=CustomUser)
def update_role_count_on_delete(sender, instance, **kwargs):
    """Update role.users_count when a user is deleted"""
    if instance.role:
        instance.role.users_count = CustomUser.objects.filter(role=instance.role).count()
        instance.role.save()

@receiver(m2m_changed, sender=Agency.admins.through)
def validate_agency_admin_relationship(sender, instance, action, pk_set, **kwargs):
    """Validate that users can only be admins of their affiliated agency"""
    if action == 'pre_add':
        for user_id in pk_set:
            try:
                user = CustomUser.objects.get(id=user_id)
                
                # Check if the user belongs to this agency
                if user.agency != instance:
                    raise ValidationError(f"User {user} is not affiliated with agency {instance}. Cannot add as admin.")
                
                # Check if the user is already an admin of another agency
                if user.administered_agencies.exists() and user not in instance.admins.all():
                    raise ValidationError(f"User {user} is already an admin of another agency. Cannot be admin of multiple agencies.")
                    
            except CustomUser.DoesNotExist:
                pass  # This will be handled by Django's foreign key validation