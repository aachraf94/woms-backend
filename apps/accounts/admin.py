from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Agency, Role
from django.utils.translation import gettext_lazy as _

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'agency', 'company', 'function', 'role', 'is_active')
    list_filter = ('is_active', 'role', 'agency')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Contact info'), {'fields': ('agency', 'company', 'function')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role'),
        }),
    )

@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'get_admins')
    
    def get_admins(self, obj):
        return ", ".join([admin.username for admin in obj.admins.all()])
    
    get_admins.short_description = 'Admins'

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'users_count', 'updated_at')
