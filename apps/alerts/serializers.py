from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Notification, Incident, RegleAlerte, JournalAction

User = get_user_model()


class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer pour les données utilisateur de base"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications"""
    destinataire = UtilisateurSerializer(read_only=True)
    destinataire_id = serializers.IntegerField(write_only=True)
    type_notification_display = serializers.CharField(source='get_type_notification_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type_notification', 'type_notification_display', 'titre', 'message',
            'destinataire', 'destinataire_id', 'lu', 'date_creation', 'date_lecture'
        ]
        read_only_fields = ['id', 'date_creation']

    def update(self, instance, validated_data):
        # Marquer comme lu et enregistrer la date de lecture
        if 'lu' in validated_data and validated_data['lu'] and not instance.lu:
            validated_data['date_lecture'] = timezone.now()
        return super().update(instance, validated_data)


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer des notifications"""
    class Meta:
        model = Notification
        fields = ['type_notification', 'titre', 'message', 'destinataire']


class IncidentSerializer(serializers.ModelSerializer):
    """Serializer pour les incidents"""
    rapporte_par = UtilisateurSerializer(read_only=True)
    assigne_a = UtilisateurSerializer(read_only=True)
    assigne_a_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    type_incident_display = serializers.CharField(source='get_type_incident_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    priorite_display = serializers.CharField(source='get_priorite_display', read_only=True)
    
    class Meta:
        model = Incident
        fields = [
            'id', 'titre', 'type_incident', 'type_incident_display', 'description',
            'statut', 'statut_display', 'priorite', 'priorite_display',
            'rapporte_par', 'assigne_a', 'assigne_a_id',
            'date_creation', 'date_mise_a_jour', 'date_resolution'
        ]
        read_only_fields = ['id', 'rapporte_par', 'date_creation', 'date_mise_a_jour']

    def create(self, validated_data):
        validated_data['rapporte_par'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Enregistrer la date de résolution si le statut passe à résolu
        if 'statut' in validated_data and validated_data['statut'] == 'resolu' and instance.statut != 'resolu':
            validated_data['date_resolution'] = timezone.now()
        return super().update(instance, validated_data)


class IncidentCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer des incidents"""
    class Meta:
        model = Incident
        fields = ['titre', 'type_incident', 'description', 'priorite']


class RegleAlerteSerializer(serializers.ModelSerializer):
    """Serializer pour les règles d'alerte"""
    creee_par = UtilisateurSerializer(read_only=True)
    
    class Meta:
        model = RegleAlerte
        fields = [
            'id', 'nom', 'description', 'condition', 'action', 'active',
            'seuil_declenchement', 'type_capteur', 'creee_par',
            'date_creation', 'date_mise_a_jour'
        ]
        read_only_fields = ['id', 'creee_par', 'date_creation', 'date_mise_a_jour']

    def create(self, validated_data):
        validated_data['creee_par'] = self.context['request'].user
        return super().create(validated_data)


class JournalActionSerializer(serializers.ModelSerializer):
    """Serializer pour le journal d'actions"""
    utilisateur = UtilisateurSerializer(read_only=True)
    incident_lie = serializers.StringRelatedField(read_only=True)
    incident_lie_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = JournalAction
        fields = [
            'id', 'action', 'details', 'adresse_ip', 'user_agent',
            'horodatage', 'utilisateur', 'incident_lie', 'incident_lie_id'
        ]
        read_only_fields = ['id', 'utilisateur', 'horodatage']

    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        # Capturer l'IP et user agent de la requête
        request = self.context.get('request')
        if request:
            validated_data['adresse_ip'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        return super().create(validated_data)

    def get_client_ip(self, request):
        """Obtenir l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class StatistiquesSerializer(serializers.Serializer):
    """Serializer pour les statistiques du dashboard"""
    total_notifications = serializers.IntegerField()
    notifications_non_lues = serializers.IntegerField()
    total_incidents = serializers.IntegerField()
    incidents_ouverts = serializers.IntegerField()
    incidents_critiques = serializers.IntegerField()
    regles_actives = serializers.IntegerField()
    actions_aujourd_hui = serializers.IntegerField()
