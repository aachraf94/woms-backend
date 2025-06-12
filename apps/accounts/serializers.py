from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth.password_validation import validate_password
from .models import FournisseurService, ProfilUtilisateur

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)
    # Champs de compatibilité
    company = serializers.CharField(source='entreprise', required=False)
    function = serializers.CharField(source='fonction', required=False)
    is_active = serializers.BooleanField(source='est_actif', required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'username', 
            'entreprise', 'fonction', 'est_actif', 'telephone', 'role', 'role_display', 
            'password', 'company', 'function', 'is_active', 'date_derniere_connexion'
        ]
        read_only_fields = ['id', 'role_display', 'date_derniere_connexion']
        extra_kwargs = {
            'role': {'required': False},
            'password': {'write_only': True}
        }
    
    @extend_schema_field(str)
    def get_role_display(self, obj):
        return obj.get_role_display()
        
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        
        if password:
            user.set_password(password)
            user.save()
            
        return user
        
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
            
        return user


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD
    
    def validate(self, attrs):
        data = super().validate(attrs)
        # Mettre à jour la dernière connexion
        self.user.mettre_a_jour_derniere_connexion()
        return data


class UserRoleChangeSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices, required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
        
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Les deux champs de mot de passe ne correspondent pas."})
        return data


class FournisseurServiceSerializer(serializers.ModelSerializer):
    utilisateur_email = serializers.EmailField(source='utilisateur.email', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    est_valide = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = FournisseurService
        fields = [
            'id', 'utilisateur', 'utilisateur_email', 'utilisateur_nom',
            'type_service', 'numero_contrat', 'date_validite', 'entreprise',
            'specialites', 'statut_actif', 'est_valide', 'cree_le', 'mis_a_jour_le'
        ]
        read_only_fields = ['id', 'cree_le', 'mis_a_jour_le', 'est_valide']


class ProfilUtilisateurSerializer(serializers.ModelSerializer):
    utilisateur_email = serializers.EmailField(source='utilisateur.email', read_only=True)
    
    class Meta:
        model = ProfilUtilisateur
        fields = [
            'id', 'utilisateur', 'utilisateur_email', 'photo_profil', 'biographie',
            'experience_annees', 'certifications', 'preferences_notification',
            'langue_preferee', 'ville', 'pays', 'code_postal', 'cree_le', 'mis_a_jour_le'
        ]
        read_only_fields = ['id', 'cree_le', 'mis_a_jour_le']


class RoleSerializer(serializers.Serializer):
    """Serializer simple pour les choix de rôles"""
    value = serializers.CharField()
    display = serializers.CharField()
