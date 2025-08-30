# gestion_groupes/signals.py
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import Group, User


@receiver(post_save, sender='auth.User')
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Créer automatiquement un profil utilisateur lors de la création d'un user"""
    from .models import ProfilUtilisateur
    
    if created:
        ProfilUtilisateur.objects.get_or_create(
            user=instance,
            defaults={
                'actif': instance.is_active,
                'service': 'Non défini',
                'poste': 'Non défini',
            }
        )
    else:
        # Mettre à jour le profil si il existe
        try:
            profil = instance.profil
            profil.actif = instance.is_active
            profil.save()
        except ProfilUtilisateur.DoesNotExist:
            # Créer le profil s'il n'existe pas
            ProfilUtilisateur.objects.create(
                user=instance,
                actif=instance.is_active,
                service='Non défini',
                poste='Non défini',
            )


@receiver(post_save, sender='auth.Group')
def create_or_update_group_extended(sender, instance, created, **kwargs):
    """Créer automatiquement une extension de groupe"""
    from .models import GroupeEtendu
    
    if created:
        GroupeEtendu.objects.get_or_create(
            group=instance,
            defaults={
                'description': f'Groupe {instance.name}',
                'couleur': '#007bff',
                'niveau_acces': 1,
                'actif': True,
            }
        )


@receiver(m2m_changed, sender=Group.user_set.through)
def track_user_group_changes(sender, instance, action, pk_set, **kwargs):
    """Suivre les changements d'affectation des utilisateurs aux groupes"""
    from .models import HistoriqueGroupes
    
    if action == "post_add":
        for user_pk in pk_set:
            try:
                user = User.objects.get(pk=user_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='add_user',
                    utilisateur_cible=user,
                    details=f'Ajout de {user.username} au groupe {instance.name}'
                )
            except User.DoesNotExist:
                pass
    
    elif action == "post_remove":
        for user_pk in pk_set:
            try:
                user = User.objects.get(pk=user_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='remove_user',
                    utilisateur_cible=user,
                    details=f'Retrait de {user.username} du groupe {instance.name}'
                )
            except User.DoesNotExist:
                pass


@receiver(m2m_changed, sender=Group.permissions.through)
def track_group_permission_changes(sender, instance, action, pk_set, **kwargs):
    """Suivre les changements de permissions des groupes"""
    from django.contrib.auth.models import Permission
    from .models import HistoriqueGroupes
    
    if action == "post_add":
        for perm_pk in pk_set:
            try:
                permission = Permission.objects.get(pk=perm_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='add_permission',
                    permission_cible=permission,
                    details=f'Ajout de la permission {permission.name} au groupe {instance.name}'
                )
            except Permission.DoesNotExist:
                pass
    
    elif action == "post_remove":
        for perm_pk in pk_set:
            try:
                permission = Permission.objects.get(pk=perm_pk)
                HistoriqueGroupes.objects.create(
                    group=instance,
                    action='remove_permission',
                    permission_cible=permission,
                    details=f'Retrait de la permission {permission.name} du groupe {instance.name}'
                )
            except Permission.DoesNotExist:
                pass


@receiver(post_delete, sender='auth.Group')
def track_group_deletion(sender, instance, **kwargs):
    """Suivre la suppression des groupes"""
    # Note: On ne peut pas créer d'HistoriqueGroupes car la FK vers Group sera cassée
    # Alternative : logger l'événement
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'Suppression du groupe {instance.name} (ID: {instance.id})')
