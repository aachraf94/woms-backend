from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import DocumentPuits, RapportQuotidien, ArchiveDocument


@receiver(post_save, sender=DocumentPuits)
def document_post_save(sender, instance, created, **kwargs):
    """Signal exécuté après la sauvegarde d'un document."""
    if created:
        # Actions à effectuer lors de la création d'un nouveau document
        # Par exemple, notifier les utilisateurs concernés
        pass
    
    # Vérifier si le document a été approuvé
    if instance.est_approuve and instance.statut == DocumentPuits.StatutDocument.APPROUVE:
        if not instance.date_approbation:
            instance.date_approbation = timezone.now()
            instance.save(update_fields=['date_approbation'])


@receiver(post_save, sender=RapportQuotidien)
def rapport_quotidien_post_save(sender, instance, created, **kwargs):
    """Signal exécuté après la sauvegarde d'un rapport quotidien."""
    if created:
        # Générer automatiquement le numéro de rapport s'il n'existe pas
        if not instance.numero_rapport:
            instance.numero_rapport = f"RQ-{instance.puits.id}-{instance.date_rapport.strftime('%Y%m%d')}"
            instance.save(update_fields=['numero_rapport'])


@receiver(pre_delete, sender=DocumentPuits)
def document_pre_delete(sender, instance, **kwargs):
    """Signal exécuté avant la suppression d'un document."""
    # Créer une archive avant suppression si ce n'est pas déjà fait
    if not hasattr(instance, 'archivedocument'):
        ArchiveDocument.objects.create(
            document_original=instance,
            raison_archivage=ArchiveDocument.RaisonArchivage.NETTOYAGE,
            description_archivage="Archivage automatique avant suppression",
            archive_par=instance.cree_par,
            peut_etre_restaure=False
        )
