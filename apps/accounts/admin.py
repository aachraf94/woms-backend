from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, FournisseurService, ProfilUtilisateur, JournalConnexion, TokenJWT
from django.utils.translation import gettext_lazy as _

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'entreprise', 'fonction', 'role', 'est_actif')
    list_filter = ('est_actif', 'role', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'entreprise')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Informations personnelles'), {'fields': ('first_name', 'last_name', 'telephone')}),
        (_('Informations professionnelles'), {'fields': ('entreprise', 'fonction')}),
        (_('Permissions'), {'fields': ('est_actif', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions')}),
        (_('Dates importantes'), {'fields': ('last_login', 'date_joined', 'date_derniere_connexion')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'entreprise', 'fonction'),
        }),
    )
    
    readonly_fields = ('date_derniere_connexion', 'last_login', 'date_joined')


@admin.register(FournisseurService)
class FournisseurServiceAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_service', 'entreprise', 'numero_contrat', 'date_validite', 'statut_actif')
    list_filter = ('type_service', 'statut_actif', 'date_validite')
    search_fields = ('utilisateur__email', 'entreprise', 'numero_contrat', 'type_service')
    readonly_fields = ('cree_le', 'mis_a_jour_le')
    
    fieldsets = (
        (_('Informations utilisateur'), {'fields': ('utilisateur',)}),
        (_('Informations service'), {'fields': ('type_service', 'numero_contrat', 'entreprise', 'specialites')}),
        (_('Validité'), {'fields': ('date_validite', 'statut_actif')}),
        (_('Audit'), {'fields': ('cree_le', 'mis_a_jour_le')}),
    )


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'ville', 'pays', 'experience_annees', 'langue_preferee')
    list_filter = ('langue_preferee', 'pays', 'ville')
    search_fields = ('utilisateur__email', 'ville', 'pays')
    readonly_fields = ('cree_le', 'mis_a_jour_le')


@admin.register(JournalConnexion)
class JournalConnexionAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_connexion', 'date_deconnexion', 'adresse_ip', 'type_connexion', 'succes_connexion')
    list_filter = ('type_connexion', 'succes_connexion', 'date_connexion')
    search_fields = ('utilisateur__email', 'adresse_ip')
    readonly_fields = ('date_connexion', 'duree_session')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(TokenJWT)
class TokenJWTAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_token', 'date_creation', 'date_expiration', 'est_sur_liste_noire', 'adresse_ip')
    list_filter = ('type_token', 'est_sur_liste_noire', 'date_creation')
    search_fields = ('utilisateur__email', 'jti', 'adresse_ip')
    readonly_fields = ('date_creation', 'date_mise_liste_noire')
    
    def has_add_permission(self, request):
        return False
