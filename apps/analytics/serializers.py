from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.wells.serializers import WellSerializer, PhaseSerializer, OperationSerializer
from .models import (
    JeuDonneesAnalytiques, AnalyseEcart, InteractionAssistantIA,
    IndicateurPerformance, AnalyseReservoir, TableauBordKPI,
    AnalysePredictive, AlerteAnalytique
)

User = get_user_model()


class JeuDonneesAnalytiquesSerializer(serializers.ModelSerializer):
    """Serializer pour JeuDonneesAnalytiques."""
    
    puits_nom = serializers.CharField(source='puits.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.username', read_only=True)
    taille_donnees_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = JeuDonneesAnalytiques
        fields = [
            'id', 'puits', 'puits_nom', 'type_donnees', 'nom_jeu_donnees',
            'donnees', 'taille_donnees', 'taille_donnees_mb', 'source_donnees',
            'date_creation', 'date_modification', 'cree_par', 'cree_par_nom'
        ]
        read_only_fields = ['date_creation', 'date_modification', 'taille_donnees_mb']
    
    def get_taille_donnees_mb(self, obj):
        """Calculer la taille en MB."""
        if obj.taille_donnees:
            return round(obj.taille_donnees / (1024 * 1024), 2)
        return None


class AnalyseEcartSerializer(serializers.ModelSerializer):
    """Serializer pour AnalyseEcart."""
    
    phase_nom = serializers.CharField(source='phase.nom', read_only=True)
    analyseur_nom = serializers.CharField(source='analyseur.username', read_only=True)
    
    class Meta:
        model = AnalyseEcart
        fields = [
            'id', 'phase', 'phase_nom', 'valeur_planifiee', 'valeur_reelle',
            'ecart_absolu', 'pourcentage_ecart', 'type_indicateur',
            'niveau_criticite', 'date_analyse', 'commentaire',
            'actions_correctives', 'analyseur', 'analyseur_nom'
        ]
        read_only_fields = ['ecart_absolu', 'pourcentage_ecart', 'niveau_criticite', 'date_analyse']


class InteractionAssistantIASerializer(serializers.ModelSerializer):
    """Serializer pour InteractionAssistantIA."""
    
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)
    puits_nom = serializers.CharField(source='puits_associe.nom', read_only=True)
    temps_traitement_secondes = serializers.SerializerMethodField()
    
    class Meta:
        model = InteractionAssistantIA
        fields = [
            'id', 'utilisateur', 'utilisateur_nom', 'requete', 'reponse',
            'type_requete', 'puits_associe', 'puits_nom', 'score_pertinence',
            'temps_traitement', 'temps_traitement_secondes', 'statut',
            'metadonnees', 'horodatage_creation', 'horodatage_reponse'
        ]
        read_only_fields = ['horodatage_creation', 'horodatage_reponse', 'temps_traitement_secondes']
    
    def get_temps_traitement_secondes(self, obj):
        """Convertir le temps de traitement en secondes."""
        if obj.temps_traitement:
            return obj.temps_traitement.total_seconds()
        return None


class IndicateurPerformanceSerializer(serializers.ModelSerializer):
    """Serializer pour IndicateurPerformance."""
    
    operation_nom = serializers.CharField(source='operation.nom', read_only=True)
    type_indicateur_nom = serializers.CharField(source='type_indicateur.nom', read_only=True)
    mesure_par_nom = serializers.CharField(source='mesure_par.username', read_only=True)
    
    class Meta:
        model = IndicateurPerformance
        fields = [
            'id', 'operation', 'operation_nom', 'type_indicateur', 'type_indicateur_nom',
            'valeur_prevue', 'valeur_reelle', 'ecart_performance',
            'pourcentage_realisation', 'date_mesure', 'date_prevue',
            'statut', 'commentaire', 'mesure_par', 'mesure_par_nom'
        ]
        read_only_fields = ['ecart_performance', 'pourcentage_realisation']


class AnalyseReservoirSerializer(serializers.ModelSerializer):
    """Serializer pour AnalyseReservoir."""
    
    puits_nom = serializers.CharField(source='puits.nom', read_only=True)
    analyste_nom = serializers.CharField(source='analyste.username', read_only=True)
    
    class Meta:
        model = AnalyseReservoir
        fields = [
            'id', 'reservoir', 'puits', 'puits_nom', 'nom_analyse',
            'nature_fluide', 'hauteur_utile', 'contact_fluide', 'net_pay',
            'debit_estime', 'pression_tete', 'temperature_reservoir',
            'porosite', 'permeabilite', 'statut_analyse', 'date_analyse',
            'analyste', 'analyste_nom', 'observations'
        ]
        read_only_fields = ['date_analyse']


class TableauBordKPISerializer(serializers.ModelSerializer):
    """Serializer pour TableauBordKPI."""
    
    puits_nom = serializers.CharField(source='puits.nom', read_only=True)
    calcule_par_nom = serializers.CharField(source='calcule_par.username', read_only=True)
    
    class Meta:
        model = TableauBordKPI
        fields = [
            'id', 'puits', 'puits_nom', 'nom_kpi', 'categorie_kpi',
            'valeur_actuelle', 'valeur_precedente', 'unite_mesure',
            'objectif_cible', 'seuil_alerte', 'pourcentage_atteinte',
            'evolution_pourcentage', 'statut_kpi', 'periode_reference',
            'date_calcul', 'calcule_par', 'calcule_par_nom'
        ]
        read_only_fields = ['pourcentage_atteinte', 'evolution_pourcentage', 'statut_kpi', 'date_calcul']


class AnalysePredictiveSerializer(serializers.ModelSerializer):
    """Serializer pour AnalysePredictive."""
    
    puits_nom = serializers.CharField(source='puits.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.username', read_only=True)
    
    class Meta:
        model = AnalysePredictive
        fields = [
            'id', 'puits', 'puits_nom', 'nom_analyse', 'type_prediction',
            'valeur_predite', 'valeur_min_predite', 'valeur_max_predite',
            'intervalle_confiance', 'date_prediction_pour', 'horizon_prediction_jours',
            'modele_utilise', 'version_modele', 'parametres_modele',
            'metriques_performance', 'donnees_entree', 'statut_prediction',
            'date_creation', 'cree_par', 'cree_par_nom', 'observations'
        ]
        read_only_fields = ['date_creation']


class AlerteAnalytiqueSerializer(serializers.ModelSerializer):
    """Serializer pour AlerteAnalytique."""
    
    puits_nom = serializers.CharField(source='puits.nom', read_only=True)
    assigne_a_nom = serializers.CharField(source='assigne_a.username', read_only=True)
    resolu_par_nom = serializers.CharField(source='resolu_par.username', read_only=True)
    
    class Meta:
        model = AlerteAnalytique
        fields = [
            'id', 'puits', 'puits_nom', 'type_alerte', 'niveau_urgence',
            'titre_alerte', 'description', 'valeur_declenchante',
            'seuil_reference', 'source_donnees', 'statut_alerte',
            'date_declenchement', 'date_resolution', 'assigne_a',
            'assigne_a_nom', 'resolu_par', 'resolu_par_nom', 'actions_prises'
        ]
        read_only_fields = ['date_declenchement']


# Serializers pour les statistiques et résumés
class StatistiquesAnalytiquesSerializer(serializers.Serializer):
    """Serializer pour les statistiques analytiques."""
    
    total_jeux_donnees = serializers.IntegerField()
    total_analyses_ecart = serializers.IntegerField()
    total_interactions_ia = serializers.IntegerField()
    total_alertes_actives = serializers.IntegerField()
    moyenne_score_pertinence_ia = serializers.DecimalField(max_digits=3, decimal_places=2)
    repartition_types_alertes = serializers.DictField()
    evolution_kpis = serializers.ListField()


class ResumePerformanceSerializer(serializers.Serializer):
    """Serializer pour le résumé de performance d'un puits."""
    
    puits_id = serializers.IntegerField()
    puits_nom = serializers.CharField()
    nombre_kpis = serializers.IntegerField()
    kpis_excellents = serializers.IntegerField()
    kpis_critiques = serializers.IntegerField()
    alertes_actives = serializers.IntegerField()
    derniere_analyse = serializers.DateTimeField()
    score_performance_global = serializers.DecimalField(max_digits=5, decimal_places=2)
