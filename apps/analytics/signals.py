from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
import sys

from .models import (
    JeuDonneesAnalytiques, AnalyseEcart, InteractionAssistantIA,
    IndicateurPerformance, TableauBordKPI, AnalysePredictive,
    AlerteAnalytique
)

User = get_user_model()


@receiver(pre_save, sender=JeuDonneesAnalytiques)
def calculer_taille_donnees(sender, instance, **kwargs):
    """Calculer automatiquement la taille des données JSON."""
    if instance.donnees:
        # Calculer la taille en octets du JSON
        instance.taille_donnees = len(json.dumps(instance.donnees).encode('utf-8'))


@receiver(post_save, sender=AnalyseEcart)
def creer_alerte_ecart_critique(sender, instance, created, **kwargs):
    """Créer une alerte automatique pour les écarts critiques."""
    if created and instance.niveau_criticite == 'CRITIQUE':
        AlerteAnalytique.objects.create(
            puits=instance.phase.puits,
            type_alerte='ECART_IMPORTANT',
            niveau_urgence='URGENT',
            titre_alerte=f'Écart critique détecté - {instance.type_indicateur}',
            description=f'Un écart de {instance.pourcentage_ecart}% a été détecté sur {instance.type_indicateur} dans la phase {instance.phase.nom}.',
            valeur_declenchante=instance.valeur_reelle,
            seuil_reference=instance.valeur_planifiee,
            source_donnees=f'Analyse d\'écart - Phase {instance.phase.numero_phase}'
        )


@receiver(post_save, sender=TableauBordKPI)
def creer_alerte_kpi_critique(sender, instance, created, **kwargs):
    """Créer une alerte pour les KPIs critiques."""
    if instance.statut_kpi == 'CRITIQUE':
        # Vérifier s'il existe déjà une alerte active pour ce KPI
        alerte_existante = AlerteAnalytique.objects.filter(
            puits=instance.puits,
            type_alerte='PERFORMANCE_DEGRADEE',
            statut_alerte__in=['NOUVELLE', 'EN_COURS'],
            titre_alerte__icontains=instance.nom_kpi
        ).first()
        
        if not alerte_existante:
            AlerteAnalytique.objects.create(
                puits=instance.puits,
                type_alerte='PERFORMANCE_DEGRADEE',
                niveau_urgence='CRITIQUE',
                titre_alerte=f'Performance critique - {instance.nom_kpi}',
                description=f'Le KPI {instance.nom_kpi} a atteint un niveau critique avec {instance.pourcentage_atteinte}% d\'atteinte de l\'objectif.',
                valeur_declenchante=instance.valeur_actuelle,
                seuil_reference=instance.objectif_cible,
                source_donnees=f'Tableau de bord KPI - {instance.categorie_kpi}'
            )


@receiver(post_save, sender=AnalysePredictive)
def creer_alerte_prediction_critique(sender, instance, created, **kwargs):
    """Créer une alerte pour les prédictions critiques."""
    if created and instance.statut_prediction == 'VALIDEE':
        # Définir les seuils critiques selon le type de prédiction
        seuils_critiques = {
            'PRODUCTION': 0.5,  # 50% de baisse
            'DEFAILLANCE': 0.8,  # 80% de probabilité
            'MAINTENANCE': 0.7,   # 70% de probabilité
            'COUT': 1.5,         # 150% d'augmentation
        }
        
        seuil = seuils_critiques.get(instance.type_prediction)
        if seuil and instance.valeur_predite:
            # Logic pour déterminer si c'est critique (simplifié)
            is_critique = False
            if instance.type_prediction == 'PRODUCTION' and instance.valeur_predite < seuil:
                is_critique = True
            elif instance.type_prediction in ['DEFAILLANCE', 'MAINTENANCE'] and instance.valeur_predite > seuil:
                is_critique = True
            elif instance.type_prediction == 'COUT' and instance.valeur_predite > seuil:
                is_critique = True
            
            if is_critique:
                AlerteAnalytique.objects.create(
                    puits=instance.puits,
                    type_alerte='PREDICTION_CRITIQUE',
                    niveau_urgence='ATTENTION',
                    titre_alerte=f'Prédiction critique - {instance.nom_analyse}',
                    description=f'L\'analyse prédictive {instance.nom_analyse} indique une valeur critique de {instance.valeur_predite} pour {instance.date_prediction_pour}.',
                    valeur_declenchante=instance.valeur_predite,
                    seuil_reference=seuil,
                    source_donnees=f'Modèle prédictif - {instance.modele_utilise}'
                )


@receiver(post_save, sender=InteractionAssistantIA)
def mettre_a_jour_horodatage_reponse(sender, instance, **kwargs):
    """Mettre à jour l'horodatage de réponse quand le statut change."""
    if instance.statut == 'COMPLETE' and not instance.horodatage_reponse:
        instance.horodatage_reponse = timezone.now()
        if instance.horodatage_creation:
            instance.temps_traitement = instance.horodatage_reponse - instance.horodatage_creation
        instance.save()


@receiver(post_save, sender=AlerteAnalytique)
def notifier_alerte_urgente(sender, instance, created, **kwargs):
    """Notifier les utilisateurs concernés pour les alertes urgentes."""
    if created and instance.niveau_urgence in ['URGENT', 'CRITIQUE']:
        # Ici vous pourriez ajouter la logique de notification
        # Par exemple: envoyer un email, créer une notification push, etc.
        print(f"ALERTE {instance.niveau_urgence}: {instance.titre_alerte} - Puits: {instance.puits.nom}")
        
        # Assigner automatiquement à un responsable si défini
        if not instance.assigne_a:
            # Logique pour trouver un responsable approprié
            # Par exemple, le dernier utilisateur qui a travaillé sur ce puits
            try:
                dernier_analyste = AnalyseEcart.objects.filter(
                    phase__puits=instance.puits
                ).order_by('-date_analyse').first()
                
                if dernier_analyste and dernier_analyste.analyseur:
                    instance.assigne_a = dernier_analyste.analyseur
                    instance.save()
            except Exception as e:
                # Log l'erreur mais ne pas faire échouer la création
                print(f"Erreur lors de l'assignation automatique: {e}")
