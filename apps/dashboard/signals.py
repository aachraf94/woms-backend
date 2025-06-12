from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from apps.wells.models import Well
from .models import VisualisationPuits, AlerteTableauBord, IndicateurClePerformance


@receiver(post_save, sender=Well)
def creer_visualisation_puits(sender, instance, created, **kwargs):
    """Crée automatiquement une visualisation pour chaque nouveau puits."""
    if created:
        VisualisationPuits.objects.get_or_create(
            puits=instance,
            defaults={
                'statut_visuel': VisualisationPuits.StatutVisuel.ACTIF,
                'code_couleur': VisualisationPuits.CodeCouleur.VERT,
                'taux_progression': 0,
                'efficacite_globale': 100,
                'cout_total_realise': 0,
            }
        )


@receiver(post_save, sender=IndicateurClePerformance)
def verifier_seuils_indicateurs(sender, instance, created, **kwargs):
    """Vérifie les seuils et crée des alertes si nécessaire."""
    if instance.seuil_alerte and not instance.est_dans_seuils():
        # Créer une alerte automatique
        AlerteTableauBord.objects.get_or_create(
            puits=instance.puits,
            type_alerte=AlerteTableauBord.TypeAlerte.PERFORMANCE_FAIBLE,
            titre_alerte=f"Seuil dépassé: {instance.nom_indicateur}",
            defaults={
                'niveau_alerte': AlerteTableauBord.NiveauAlerte.ATTENTION,
                'description_detaillee': f"L'indicateur {instance.nom_indicateur} a dépassé le seuil d'alerte défini.",
                'valeur_seuil_defini': instance.seuil_alerte,
                'valeur_actuelle_mesuree': instance.performance_globale,
                'actions_recommandees': "Vérifier les causes de la baisse de performance et prendre les mesures correctives nécessaires.",
            }
        )


@receiver(post_save, sender=AlerteTableauBord)
def mettre_a_jour_compteurs_alertes(sender, instance, created, **kwargs):
    """Met à jour les compteurs d'alertes dans la visualisation."""
    try:
        visualisation = instance.puits.visualisation
        if created and instance.est_active:
            visualisation.nombre_alertes_non_lues += 1
        elif not instance.est_active:
            visualisation.nombre_alertes_non_lues = max(0, visualisation.nombre_alertes_non_lues - 1)
        
        # Mettre à jour le statut automatiquement
        visualisation.mettre_a_jour_statut()
        
    except VisualisationPuits.DoesNotExist:
        # Créer la visualisation si elle n'existe pas
        creer_visualisation_puits(Well, instance.puits, True)


@receiver(post_delete, sender=AlerteTableauBord)
def decrementer_compteur_alertes(sender, instance, **kwargs):
    """Décrémente le compteur d'alertes lors de la suppression."""
    try:
        visualisation = instance.puits.visualisation
        if instance.est_active:
            visualisation.nombre_alertes_non_lues = max(0, visualisation.nombre_alertes_non_lues - 1)
            visualisation.save()
    except VisualisationPuits.DoesNotExist:
        pass
