from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    DocumentPuits, RapportQuotidien, RapportPlanification,
    ModeleDocument, ArchiveDocument
)

User = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    """Sérialiseur simple pour les utilisateurs."""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class DocumentPuitsSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les documents de puits."""
    cree_par = UserSimpleSerializer(read_only=True)
    modifie_par = UserSimpleSerializer(read_only=True)
    approuve_par = UserSimpleSerializer(read_only=True)
    extension_fichier = serializers.CharField(read_only=True)
    est_valide = serializers.BooleanField(read_only=True)
    puits_nom = serializers.CharField(source='puits.name', read_only=True)
    
    class Meta:
        model = DocumentPuits
        fields = [
            'id', 'nom_document', 'type_document', 'fichier', 'taille_fichier',
            'description', 'mots_cles', 'puits', 'puits_nom', 'phase', 'operation',
            'est_public', 'est_confidentiel', 'numero_version', 'version_precedente',
            'statut', 'est_approuve', 'approuve_par', 'date_approbation',
            'commentaires_approbation', 'date_creation', 'date_modification',
            'cree_par', 'modifie_par', 'date_validite_debut', 'date_validite_fin',
            'nombre_telechargements', 'extension_fichier', 'est_valide'
        ]
        read_only_fields = [
            'taille_fichier', 'date_creation', 'date_modification',
            'nombre_telechargements', 'cree_par', 'modifie_par'
        ]
    
    def create(self, validated_data):
        validated_data['cree_par'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        validated_data['modifie_par'] = self.context['request'].user
        return super().update(instance, validated_data)


class DocumentPuitsListSerializer(serializers.ModelSerializer):
    """Sérialiseur simplifié pour la liste des documents."""
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    extension_fichier = serializers.CharField(read_only=True)
    puits_nom = serializers.CharField(source='puits.name', read_only=True)
    
    class Meta:
        model = DocumentPuits
        fields = [
            'id', 'nom_document', 'type_document', 'statut',
            'puits_nom', 'date_creation', 'cree_par_nom',
            'extension_fichier', 'taille_fichier', 'est_public'
        ]


class RapportQuotidienSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les rapports quotidiens."""
    soumis_par = UserSimpleSerializer(read_only=True)
    valide_par = UserSimpleSerializer(read_only=True)
    puits_nom = serializers.CharField(source='puits.name', read_only=True)
    
    class Meta:
        model = RapportQuotidien
        fields = [
            'id', 'puits', 'puits_nom', 'phase', 'date_rapport', 'numero_rapport',
            'fichier_rapport', 'activites_realisees', 'objectifs_jour',
            'objectifs_lendemain', 'problemes_rencontres', 'solutions_appliquees',
            'avancement_pourcentage', 'heures_travaillees', 'nombre_personnel',
            'conditions_meteo', 'temperature_min', 'temperature_max', 'vitesse_vent',
            'statut_equipement', 'incidents_securite', 'mesures_securite_prises',
            'statut', 'valide_par', 'date_validation', 'commentaires_validation',
            'date_creation', 'date_modification', 'soumis_par'
        ]
        read_only_fields = [
            'numero_rapport', 'date_creation', 'date_modification', 'soumis_par'
        ]
    
    def create(self, validated_data):
        validated_data['soumis_par'] = self.context['request'].user
        return super().create(validated_data)


class RapportQuotidienListSerializer(serializers.ModelSerializer):
    """Sérialiseur simplifié pour la liste des rapports quotidiens."""
    puits_nom = serializers.CharField(source='puits.name', read_only=True)
    soumis_par_nom = serializers.CharField(source='soumis_par.get_full_name', read_only=True)
    
    class Meta:
        model = RapportQuotidien
        fields = [
            'id', 'numero_rapport', 'puits_nom', 'date_rapport',
            'statut', 'avancement_pourcentage', 'heures_travaillees',
            'soumis_par_nom', 'date_creation'
        ]


class RapportPlanificationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les rapports de planification."""
    cree_par = UserSimpleSerializer(read_only=True)
    approuve_par = UserSimpleSerializer(read_only=True)
    puits_nom = serializers.CharField(source='puits.name', read_only=True)
    duree_reelle_jours = serializers.IntegerField(read_only=True)
    est_en_retard = serializers.BooleanField(read_only=True)
    pourcentage_budget_consomme = serializers.DecimalField(
        max_digits=5, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = RapportPlanification
        fields = [
            'id', 'puits', 'puits_nom', 'phase', 'nom_projet', 'code_projet',
            'fichier_plan', 'date_debut_prevue', 'date_fin_prevue',
            'date_debut_reelle', 'date_fin_reelle', 'duree_prevue_jours',
            'budget_prevu', 'budget_consomme', 'devise', 'description_projet',
            'objectifs', 'livrables_attendus', 'risques_identifies',
            'mesures_mitigation', 'niveau_risque_global', 'ressources_humaines',
            'equipements_requis', 'materiaux_necessaires', 'jalons_principaux',
            'pourcentage_avancement', 'priorite', 'statut_planification',
            'approuve_par', 'date_approbation', 'commentaires_approbation',
            'date_creation', 'date_modification', 'cree_par',
            'duree_reelle_jours', 'est_en_retard', 'pourcentage_budget_consomme'
        ]
        read_only_fields = [
            'code_projet', 'date_creation', 'date_modification', 'cree_par'
        ]
    
    def create(self, validated_data):
        validated_data['cree_par'] = self.context['request'].user
        return super().create(validated_data)


class RapportPlanificationListSerializer(serializers.ModelSerializer):
    """Sérialiseur simplifié pour la liste des rapports de planification."""
    puits_nom = serializers.CharField(source='puits.name', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    
    class Meta:
        model = RapportPlanification
        fields = [
            'id', 'code_projet', 'nom_projet', 'puits_nom',
            'statut_planification', 'priorite', 'date_debut_prevue',
            'date_fin_prevue', 'pourcentage_avancement', 'cree_par_nom'
        ]


class ModeleDocumentSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les modèles de documents."""
    cree_par = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = ModeleDocument
        fields = [
            'id', 'nom_modele', 'code_modele', 'type_modele',
            'fichier_modele', 'description', 'instructions_utilisation',
            'champs_variables', 'champs_obligatoires', 'nombre_utilisations',
            'derniere_utilisation', 'version', 'est_actif', 'est_par_defaut',
            'est_public', 'utilisateurs_autorises', 'cree_par',
            'date_creation', 'date_modification'
        ]
        read_only_fields = [
            'code_modele', 'nombre_utilisations', 'derniere_utilisation',
            'date_creation', 'date_modification', 'cree_par'
        ]
    
    def create(self, validated_data):
        validated_data['cree_par'] = self.context['request'].user
        return super().create(validated_data)


class ArchiveDocumentSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les archives de documents."""
    archive_par = UserSimpleSerializer(read_only=True)
    document_nom = serializers.CharField(source='document_original.nom_document', read_only=True)
    peut_etre_supprime = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ArchiveDocument
        fields = [
            'id', 'document_original', 'document_nom', 'raison_archivage',
            'description_archivage', 'date_archivage', 'archive_par',
            'peut_etre_restaure', 'date_suppression_prevue', 'duree_retention_jours',
            'chemin_sauvegarde', 'taille_archive', 'checksum_archive',
            'peut_etre_supprime'
        ]
        read_only_fields = [
            'date_archivage', 'archive_par', 'taille_archive', 'checksum_archive'
        ]
    
    def create(self, validated_data):
        validated_data['archive_par'] = self.context['request'].user
        return super().create(validated_data)
