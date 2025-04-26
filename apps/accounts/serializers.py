from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'username', 'company', 
                  'function', 'is_active', 'role', 'role_display', 'password']
        read_only_fields = ['id', 'role_display']
        extra_kwargs = {
            'role': {'required': False}
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
            raise serializers.ValidationError({"confirm_password": "The two password fields didn't match."})
        return data
