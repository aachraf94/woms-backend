from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomUser, Agency, Role
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field

User = get_user_model()

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'

class AgencySerializer(serializers.ModelSerializer):
    admins_names = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Agency
        fields = ['id', 'name', 'location', 'admins', 'admins_names', 'users_count']
        read_only_fields = ['admins_names', 'users_count']
    
    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_admins_names(self, obj):
        return [str(admin) for admin in obj.admins.all()]
    
    @extend_schema_field(int)
    def get_users_count(self, obj):
        return obj.get_users_count()

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    agency_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'username', 'company', 
                  'function', 'is_active', 'role', 'role_name', 'agency', 'agency_name']
        read_only_fields = ['id', 'role_name', 'agency_name']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': False}
        }
    
    @extend_schema_field(str)
    def get_role_name(self, obj):
        return obj.role.name if obj.role else None
        
    @extend_schema_field(str)
    def get_agency_name(self, obj):
        return obj.agency.name if obj.agency else None

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

class AgencyAdminSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)

class UserRoleChangeSerializer(serializers.Serializer):
    role_id = serializers.IntegerField(required=True)
