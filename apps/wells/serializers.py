from rest_framework import serializers
from .models import Well, WellOperation, DailyReport, WellDocument
from .region_models import Region, Forage, Phase, TypeOperation, Operation, Probleme, TypeIndicateur, Indicateur, Reservoir

class WellDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WellDocument
        fields = '__all__'
        read_only_fields = ['uploaded_by', 'uploaded_at', 'uploaded_by_name']
        
    def get_uploaded_by_name(self, obj):
        return obj.uploaded_by.get_full_name() if obj.uploaded_by else None

class DailyReportSerializer(serializers.ModelSerializer):
    submitted_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyReport
        fields = '__all__'
        read_only_fields = ['submitted_by', 'submitted_at', 'updated_at', 'submitted_by_name']
        
    def get_submitted_by_name(self, obj):
        return obj.submitted_by.get_full_name() if obj.submitted_by else None

class WellOperationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = WellOperation
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'created_by_name']
        
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

class WellSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    last_updated_by_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Well
        fields = '__all__'
        read_only_fields = ['created_by', 'creation_date', 'last_updated', 'last_updated_by', 
                           'created_by_name', 'last_updated_by_name', 'status_display']
        
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None
        
    def get_last_updated_by_name(self, obj):
        return obj.last_updated_by.get_full_name() if obj.last_updated_by else None
        
    def get_status_display(self, obj):
        return obj.get_status_display()

class WellDetailSerializer(WellSerializer):
    operations = WellOperationSerializer(many=True, read_only=True)
    daily_reports = DailyReportSerializer(many=True, read_only=True)
    documents = WellDocumentSerializer(many=True, read_only=True)
    forage = serializers.SerializerMethodField()
    region_details = serializers.SerializerMethodField()
    
    class Meta(WellSerializer.Meta):
        fields = WellSerializer.Meta.fields + ['operations', 'daily_reports', 'documents', 'forage', 'region_details']
    
    def get_forage(self, obj):
        try:
            return ForageSerializer(obj.forage).data
        except:
            return None
    
    def get_region_details(self, obj):
        if obj.region:
            return RegionSerializer(obj.region).data
        return None


# New serializers for the Java-inspired models
class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class ForageSerializer(serializers.ModelSerializer):
    puit_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Forage
        fields = '__all__'
        
    def get_puit_nom(self, obj):
        return obj.puit.nom if obj.puit else None

class TypeOperationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeOperation
        fields = '__all__'

class PhaseSerializer(serializers.ModelSerializer):
    forage_details = serializers.SerializerMethodField()
    operations = serializers.SerializerMethodField()
    
    class Meta:
        model = Phase
        fields = '__all__'
        
    def get_forage_details(self, obj):
        return ForageSerializer(obj.forage).data
        
    def get_operations(self, obj):
        return OperationSerializer(obj.operations.all(), many=True).data

class OperationSerializer(serializers.ModelSerializer):
    type_operation_details = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Operation
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at']
        
    def get_type_operation_details(self, obj):
        return TypeOperationSerializer(obj.type_operation).data
        
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None

class ProblemeSerializer(serializers.ModelSerializer):
    detecte_par_name = serializers.SerializerMethodField()
    assigne_a_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Probleme
        fields = '__all__'
        read_only_fields = ['detecte_par', 'date_detection']
        
    def get_detecte_par_name(self, obj):
        return obj.detecte_par.get_full_name() if obj.detecte_par else None
        
    def get_assigne_a_name(self, obj):
        return obj.assigne_a.get_full_name() if obj.assigne_a else None

class TypeIndicateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeIndicateur
        fields = '__all__'

class IndicateurSerializer(serializers.ModelSerializer):
    type_indicateur_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Indicateur
        fields = '__all__'
        
    def get_type_indicateur_details(self, obj):
        return TypeIndicateurSerializer(obj.type_indicateur).data

class ReservoirSerializer(serializers.ModelSerializer):
    puit_nom = serializers.SerializerMethodField()
    
    class Meta:
        model = Reservoir
        fields = '__all__'
        
    def get_puit_nom(self, obj):
        return obj.puit.nom if obj.puit else None
