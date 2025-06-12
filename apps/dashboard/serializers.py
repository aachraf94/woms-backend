from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    VisualisationPuits,
    IndicateurClePerformance,
    TableauBordExecutif,
    AlerteTableauBord,
    RapportPerformanceDetaille
)


class VisualisationPuitsSerializer(serializers.ModelSerializer):
    nom_puits = serializers.ReadOnlyField()
    est_critique = serializers.ReadOnlyField()
    
    class Meta:
        model = VisualisationPuits
        fields = [
            'id', 'puits', 'nom_puits', 'code_couleur', 'statut_visuel',
            'icone_statut', 'taux_progression', 'efficacite_globale',
            'cout_total_realise', 'nombre_incidents_actifs',
            'nombre_alertes_non_lues', 'jours_depuis_derniere_activite',
            'est_critique', 'derniere_mise_a_jour', 'date_creation'
        ]
        read_only_fields = ['derniere_mise_a_jour', 'date_creation']


class IndicateurClePerformanceSerializer(serializers.ModelSerializer):
    nom_puits = serializers.ReadOnlyField()
    performance_globale = serializers.ReadOnlyField()
    est_dans_seuils = serializers.SerializerMethodField()
    
    class Meta:
        model = IndicateurClePerformance
        fields = [
            'id', 'puits', 'nom_puits', 'nom_indicateur', 'type_indicateur',
            'unite_mesure', 'variance_cout', 'variance_temps', 'taux_forage_moyen',
            'efficacite_operationnelle', 'disponibilite_equipement',
            'taux_reussite_operations', 'indice_securite', 'valeur_cible',
            'seuil_alerte', 'performance_globale', 'est_dans_seuils',
            'periode_debut', 'periode_fin', 'date_calcul', 'derniere_mise_a_jour'
        ]
        read_only_fields = ['date_calcul', 'derniere_mise_a_jour']
    
    def get_est_dans_seuils(self, obj):
        return obj.est_dans_seuils()


class TableauBordExecutifSerializer(serializers.ModelSerializer):
    taux_completion_projets = serializers.ReadOnlyField()
    performance_budgetaire = serializers.ReadOnlyField()
    cree_par_nom = serializers.CharField(source='cree_par.get_full_name', read_only=True)
    
    class Meta:
        model = TableauBordExecutif
        fields = [
            'id', 'nom_tableau', 'type_tableau', 'description',
            'total_puits', 'puits_actifs', 'puits_termines', 'puits_en_cours',
            'puits_en_maintenance', 'budget_total_alloue', 'cout_realise_cumule',
            'variance_budgetaire', 'taux_consommation_budget', 'delai_moyen_completion',
            'projets_en_retard', 'projets_en_avance', 'taux_respect_delais',
            'nombre_incidents_total', 'taux_incidents', 'score_securite_global',
            'taux_conformite_qualite', 'periode_debut', 'periode_fin',
            'taux_completion_projets', 'performance_budgetaire',
            'est_actif', 'cree_par', 'cree_par_nom', 'date_creation', 'derniere_mise_a_jour'
        ]
        read_only_fields = ['date_creation', 'derniere_mise_a_jour']


class AlerteTableauBordSerializer(serializers.ModelSerializer):
    nom_puits = serializers.ReadOnlyField()
    duree_ouverture = serializers.ReadOnlyField()
    est_critique_ou_urgente = serializers.ReadOnlyField()
    accusee_par_nom = serializers.CharField(source='accusee_par.get_full_name', read_only=True)
    traitee_par_nom = serializers.CharField(source='traitee_par.get_full_name', read_only=True)
    
    class Meta:
        model = AlerteTableauBord
        fields = [
            'id', 'puits', 'nom_puits', 'type_alerte', 'niveau_alerte',
            'statut_alerte', 'titre_alerte', 'description_detaillee',
            'actions_recommandees', 'valeur_seuil_defini', 'valeur_actuelle_mesuree',
            'unite_valeur', 'est_active', 'est_accusee_reception',
            'accusee_par', 'accusee_par_nom', 'traitee_par', 'traitee_par_nom',
            'duree_ouverture', 'est_critique_ou_urgente', 'date_creation',
            'date_accusation', 'date_debut_traitement', 'date_resolution', 'date_fermeture'
        ]
        read_only_fields = [
            'date_creation', 'date_accusation', 'date_debut_traitement',
            'date_resolution', 'date_fermeture'
        ]


class RapportPerformanceDetailleSerializer(serializers.ModelSerializer):
    duree_periode = serializers.ReadOnlyField()
    est_recent = serializers.ReadOnlyField()
    genere_par_nom = serializers.CharField(source='genere_par.get_full_name', read_only=True)
    valide_par_nom = serializers.CharField(source='valide_par.get_full_name', read_only=True)
    
    class Meta:
        model = RapportPerformanceDetaille
        fields = [
            'id', 'nom_rapport', 'type_rapport', 'statut_rapport',
            'periode_debut', 'periode_fin', 'duree_periode', 'donnees_rapport',
            'resume_executif', 'analyse_performance', 'recommandations_amelioration',
            'plan_action_propose', 'inclut_metriques_financieres',
            'inclut_metriques_operationnelles', 'inclut_metriques_securite',
            'inclut_analyses_tendances', 'genere_par', 'genere_par_nom',
            'valide_par', 'valide_par_nom', 'destinataires',
            'fichier_rapport_pdf', 'fichier_donnees_excel', 'est_recent',
            'date_generation', 'date_validation', 'date_publication'
        ]
        read_only_fields = [
            'date_generation', 'date_validation', 'date_publication'
        ]


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer pour le résumé global du dashboard."""
    total_puits = serializers.IntegerField()
    puits_actifs = serializers.IntegerField()
    puits_critiques = serializers.IntegerField()
    alertes_actives = serializers.IntegerField()
    alertes_critiques = serializers.IntegerField()
    performance_moyenne = serializers.DecimalField(max_digits=5, decimal_places=2)
    cout_total_realise = serializers.DecimalField(max_digits=15, decimal_places=2)
    derniere_mise_a_jour = serializers.DateTimeField()
