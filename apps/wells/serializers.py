from rest_framework import serializers
from .models import Well, WellOperation, DailyReport, WellDocument

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
    
    class Meta(WellSerializer.Meta):
        fields = WellSerializer.Meta.fields + ['operations', 'daily_reports', 'documents']
