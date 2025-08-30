# gestion_groupes/management/commands/cleanup_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from gestion_groupes.models import ProfilUtilisateur


class Command(BaseCommand):
    help = 'Nettoie et synchronise les profils utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Crée les profils manquants',
        )
        parser.add_argument(
            '--delete-orphaned',
            action='store_true',
            help='Supprime les profils orphelins',
        )

    def handle(self, *args, **options):
        create_missing = options['create_missing']
        delete_orphaned = options['delete_orphaned']
        
        self.stdout.write('🧹 Nettoyage des profils utilisateurs...')
        
        if create_missing:
            # Créer les profils manquants
            users_without_profile = User.objects.filter(profil__isnull=True)
            created_count = 0
            
            for user in users_without_profile:
                ProfilUtilisateur.objects.create(
                    user=user,
                    service='Non défini',
                    poste='Non défini',
                    actif=user.is_active,
                )
                created_count += 1
                self.stdout.write(f'  ✅ Profil créé pour {user.username}')
            
            self.stdout.write(f'📊 {created_count} profils créés')
        
        if delete_orphaned:
            # Supprimer les profils orphelins
            orphaned_profiles = ProfilUtilisateur.objects.filter(user__isnull=True)
            orphaned_count = orphaned_profiles.count()
            orphaned_profiles.delete()
            
            self.stdout.write(f'🗑️  {orphaned_count} profils orphelins supprimés')
        
        # Statistiques finales
        total_users = User.objects.count()
        total_profiles = ProfilUtilisateur.objects.count()
        
        self.stdout.write(f'📊 Statistiques finales:')
        self.stdout.write(f'  👥 Utilisateurs: {total_users}')
        self.stdout.write(f'  📋 Profils: {total_profiles}')
        
        if total_users == total_profiles:
            self.stdout.write(self.style.SUCCESS('✅ Tous les utilisateurs ont un profil'))
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️  {total_users - total_profiles} utilisateurs sans profil')
            )
