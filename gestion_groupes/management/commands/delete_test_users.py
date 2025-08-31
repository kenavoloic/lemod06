# gestion_groupes/management/commands/delete_test_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Supprime tous les utilisateurs de test créés par create_test_users_permissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirme la suppression sans demander de confirmation',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans l\'exécuter',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        confirm = options['confirm']
        
        # Liste des utilisateurs de test
        test_usernames = [
            'marie.rh', 'sophie.rh',
            'jean.exploitation', 'claire.exploitation', 
            'pierre.direction', 'isabelle.direction',
            'admin.test'
        ]
        
        if dry_run:
            self.stdout.write('🔍 Mode simulation - Aucune suppression ne sera effectuée\n')
        
        self.stdout.write('🗑️  Suppression des utilisateurs de test\n')
        
        # Trouver les utilisateurs existants
        existing_users = []
        for username in test_usernames:
            try:
                user = User.objects.get(username=username)
                existing_users.append({
                    'user': user,
                    'username': username,
                    'full_name': f"{user.first_name} {user.last_name}",
                    'email': user.email,
                    'groups': [g.name for g in user.groups.all()],
                    'is_superuser': user.is_superuser,
                    'last_login': user.last_login
                })
            except User.DoesNotExist:
                pass
        
        if not existing_users:
            self.stdout.write('ℹ️  Aucun utilisateur de test trouvé')
            return
        
        # Afficher les utilisateurs trouvés
        self.stdout.write(f'📋 Utilisateurs de test trouvés ({len(existing_users)}):')
        for user_info in existing_users:
            groups_str = ', '.join(user_info['groups']) if user_info['groups'] else 'Aucun groupe'
            super_indicator = ' (SUPERUSER)' if user_info['is_superuser'] else ''
            last_login = user_info['last_login'].strftime('%d/%m/%Y %H:%M') if user_info['last_login'] else 'Jamais connecté'
            
            self.stdout.write(f'   • {user_info["username"]}{super_indicator}')
            self.stdout.write(f'     {user_info["full_name"]} - {user_info["email"]}')
            self.stdout.write(f'     Groupes: {groups_str}')
            self.stdout.write(f'     Dernière connexion: {last_login}')
        
        if dry_run:
            self.stdout.write(f'\n🔍 [SIMULATION] {len(existing_users)} utilisateurs seraient supprimés')
            return
        
        # Demander confirmation
        if not confirm:
            self.stdout.write(f'\n⚠️  Vous êtes sur le point de supprimer {len(existing_users)} utilisateurs de test')
            response = input('Êtes-vous sûr de vouloir continuer? (oui/non): ')
            
            if response.lower() not in ['oui', 'o', 'yes', 'y']:
                self.stdout.write('❌ Suppression annulée')
                return
        
        # Procéder à la suppression
        deleted_count = 0
        errors = []
        
        for user_info in existing_users:
            try:
                user = user_info['user']
                username = user.username
                
                # Informations avant suppression
                groups_before = [g.name for g in user.groups.all()]
                evaluations_count = 0
                
                # Compter les évaluations liées (si le modèle existe)
                try:
                    from suivi_conducteurs.models import Evaluation
                    evaluations_count = Evaluation.objects.filter(evaluateur__nom__icontains=user.last_name).count()
                except:
                    pass
                
                # Supprimer l'utilisateur
                user.delete()
                deleted_count += 1
                
                self.stdout.write(f'   ✅ {username} supprimé')
                if groups_before:
                    self.stdout.write(f'     Était membre de: {", ".join(groups_before)}')
                if evaluations_count > 0:
                    self.stdout.write(f'     ⚠️  Avait {evaluations_count} évaluations liées (vérifiez la cohérence des données)')
                
            except Exception as e:
                errors.append(f'{user_info["username"]}: {str(e)}')
                self.stdout.write(f'   ❌ Erreur lors de la suppression de {user_info["username"]}: {e}')
        
        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 RÉSUMÉ DE LA SUPPRESSION')
        self.stdout.write(f'   ✅ Utilisateurs supprimés: {deleted_count}')
        self.stdout.write(f'   ❌ Erreurs: {len(errors)}')
        
        if errors:
            self.stdout.write('\n❌ ERREURS RENCONTRÉES:')
            for error in errors:
                self.stdout.write(f'   • {error}')
        
        if deleted_count > 0:
            self.stdout.write('\n✅ Suppression terminée avec succès')
            self.stdout.write('\n💡 RECOMMANDATIONS:')
            self.stdout.write('   • Vérifiez la cohérence des données si des évaluations étaient liées')
            self.stdout.write('   • Exécutez "python manage.py verify_permissions" pour vérifier l\'état des groupes')
            self.stdout.write('   • Les groupes eux-mêmes n\'ont pas été supprimés')
        
        # Vérification finale
        remaining_test_users = []
        for username in test_usernames:
            if User.objects.filter(username=username).exists():
                remaining_test_users.append(username)
        
        if remaining_test_users:
            self.stdout.write(f'\n⚠️  Utilisateurs de test encore présents: {", ".join(remaining_test_users)}')
        else:
            self.stdout.write('\n🎯 Tous les utilisateurs de test ont été supprimés')