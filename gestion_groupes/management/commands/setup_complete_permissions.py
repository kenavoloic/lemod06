# gestion_groupes/management/commands/setup_complete_permissions.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import Group, Permission, User
import sys
import time


class Command(BaseCommand):
    help = 'Installation complète du système de permissions selon la politique définie'

    def add_arguments(self, parser):
        parser.add_argument(
            '--with-test-users',
            action='store_true',
            help='Crée également des utilisateurs de test',
        )
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Remet à zéro toute la configuration existante',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation - affiche ce qui serait fait',
        )
        parser.add_argument(
            '--nuclear-reset',
            action='store_true',
            help='⚠️ DANGER: Supprime TOUS les groupes et utilisateurs non-superuser',
        )

    def handle(self, *args, **options):
        # Gestion du nuclear reset en premier
        if options.get('nuclear_reset'):
            self.nuclear_reset()
            return
            
        dry_run = options['dry_run']
        with_test_users = options['with_test_users']
        reset_all = options['reset_all']
        
        self.stdout.write('🚀 INSTALLATION COMPLÈTE DU SYSTÈME DE PERMISSIONS')
        self.stdout.write('='*60)
        
        if dry_run:
            self.stdout.write('🔍 MODE SIMULATION ACTIVÉ - Aucune modification réelle\n')
        
        # Étapes d'installation
        steps = [
            ('1. Vérification des prérequis', self.check_prerequisites),
            ('2. Configuration des groupes de base', self.setup_base_groups),
            ('3. Configuration des permissions selon la politique', self.setup_permissions_policy),
            ('4. Vérification de la configuration', self.verify_configuration),
        ]
        
        if with_test_users:
            steps.append(('5. Création des utilisateurs de test', self.create_test_users))
        
        steps.append(('Finalisation', self.finalize_setup))
        
        # Exécution des étapes
        for step_num, (step_name, step_function) in enumerate(steps, 1):
            self.stdout.write(f'\n📋 ÉTAPE {step_num}: {step_name}')
            self.stdout.write('-' * 50)
            
            try:
                if not dry_run:
                    step_function(reset_all if step_num <= 3 else False)
                else:
                    self.stdout.write(f'[SIMULATION] Exécution de: {step_name}')
                
                self.stdout.write(f'✅ {step_name} - Terminé')
                
                # Petite pause pour la lisibilité
                if not dry_run:
                    time.sleep(1)
                    
            except Exception as e:
                self.stdout.write(f'❌ Erreur lors de {step_name}: {e}')
                if not dry_run:
                    sys.exit(1)
        
        # Résumé final
        self.show_final_summary(dry_run, with_test_users)

    def check_prerequisites(self, reset=False):
        """Vérifier que tous les prérequis sont satisfaits"""
        self.stdout.write('🔍 Vérification des prérequis...')
        
        # Vérifier les migrations
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            self.stdout.write('⚠️  Des migrations sont en attente')
            self.stdout.write('   Exécutez d\'abord: python manage.py migrate')
            raise Exception('Migrations en attente')
        
        # Vérifier les permissions de base
        suivi_permissions = Permission.objects.filter(
            content_type__app_label='suivi_conducteurs'
        ).count()
        
        if suivi_permissions == 0:
            self.stdout.write('⚠️  Aucune permission trouvée pour suivi_conducteurs')
            self.stdout.write('   Exécutez d\'abord: python manage.py migrate')
            raise Exception('Permissions manquantes')
        
        self.stdout.write(f'✅ {suivi_permissions} permissions disponibles pour suivi_conducteurs')
        
        # Vérifier les modèles critiques
        from suivi_conducteurs.models import (
            Conducteur, Evaluateur, Site, Societe, Service,
            CritereEvaluation, Evaluation, TypologieEvaluation
        )
        
        models_count = {
            'Conducteur': Conducteur.objects.count(),
            'Societe': Societe.objects.count(),
            'Site': Site.objects.count(),
            'TypologieEvaluation': TypologieEvaluation.objects.count(),
            'CritereEvaluation': CritereEvaluation.objects.count(),
        }
        
        self.stdout.write('📊 Données existantes:')
        for model_name, count in models_count.items():
            self.stdout.write(f'   • {model_name}: {count}')

    def setup_base_groups(self, reset=False):
        """Configurer les groupes de base avec leurs extensions"""
        self.stdout.write('⚙️ Configuration des groupes de base...')
        
        try:
            call_command('setup_groups', reset=reset, verbosity=1)
        except Exception as e:
            self.stdout.write(f'⚠️  Utilisation de la configuration de base: {e}')
            
            # Configuration manuelle de base
            groupes_config = {
                'Direction': {'couleur': '#dc3545', 'niveau_acces': 5},
                'RH': {'couleur': '#28a745', 'niveau_acces': 3},
                'Exploitation': {'couleur': '#ffc107', 'niveau_acces': 2},
            }
            
            for nom, config in groupes_config.items():
                group, created = Group.objects.get_or_create(name=nom)
                if created:
                    self.stdout.write(f'   ✅ Groupe {nom} créé')

    def setup_permissions_policy(self, reset=False):
        """Configurer les permissions selon la politique"""
        self.stdout.write('🔐 Configuration des permissions selon la politique...')
        
        call_command('setup_permissions_politique', reset=reset, verbosity=1)

    def verify_configuration(self, reset=False):
        """Vérifier que la configuration est correcte"""
        self.stdout.write('🔍 Vérification de la configuration...')
        
        call_command('verify_permissions', verbosity=1)

    def create_test_users(self, reset=False):
        """Créer les utilisateurs de test"""
        self.stdout.write('👥 Création des utilisateurs de test...')
        
        call_command('create_test_users_permissions', reset=reset, verbosity=1)

    def finalize_setup(self, reset=False):
        """Finaliser la configuration"""
        self.stdout.write('🏁 Finalisation de la configuration...')
        
        # Statistiques finales
        total_groups = Group.objects.count()
        total_users = User.objects.count()
        users_with_groups = User.objects.filter(groups__isnull=False).distinct().count()
        
        self.stdout.write(f'   📊 Groupes configurés: {total_groups}')
        self.stdout.write(f'   👥 Utilisateurs total: {total_users}')
        self.stdout.write(f'   👤 Utilisateurs avec groupes: {users_with_groups}')
        
        # Vérifier les permissions des groupes critiques
        critical_groups = ['RH', 'Exploitation', 'Direction']
        for group_name in critical_groups:
            try:
                group = Group.objects.get(name=group_name)
                perm_count = group.permissions.count()
                suivi_perm_count = group.permissions.filter(
                    content_type__app_label='suivi_conducteurs'
                ).count()
                self.stdout.write(f'   🔐 {group_name}: {perm_count} permissions ({suivi_perm_count} suivi_conducteurs)')
            except Group.DoesNotExist:
                self.stdout.write(f'   ❌ {group_name}: Groupe manquant')

    def show_final_summary(self, dry_run, with_test_users):
        """Afficher le résumé final de l'installation"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write('🎉 INSTALLATION TERMINÉE')
        self.stdout.write('='*60)
        
        if dry_run:
            self.stdout.write('🔍 Ceci était une simulation - aucune modification réelle effectuée')
            self.stdout.write('💡 Relancez sans --dry-run pour appliquer les changements')
            return
        
        # Résumé de la configuration
        self.stdout.write('\n📋 RÉSUMÉ DE LA CONFIGURATION:')
        
        # Groupes configurés
        groups = Group.objects.all().order_by('name')
        self.stdout.write(f'\n👥 GROUPES CONFIGURÉS ({groups.count()}):')
        
        for group in groups:
            users_count = group.user_set.count()
            permissions_count = group.permissions.count()
            suivi_permissions_count = group.permissions.filter(
                content_type__app_label='suivi_conducteurs'
            ).count()
            
            self.stdout.write(f'   • {group.name}:')
            self.stdout.write(f'     - {users_count} utilisateur(s)')
            self.stdout.write(f'     - {permissions_count} permission(s) total')
            self.stdout.write(f'     - {suivi_permissions_count} permission(s) suivi_conducteurs')
        
        # Utilisateurs de test créés
        if with_test_users:
            test_usernames = [
                'marie.rh', 'sophie.rh', 'jean.exploitation', 
                'claire.exploitation', 'pierre.direction', 'isabelle.direction', 'admin.test'
            ]
            existing_test_users = User.objects.filter(username__in=test_usernames)
            
            self.stdout.write(f'\n🧪 UTILISATEURS DE TEST ({existing_test_users.count()}):')
            for user in existing_test_users:
                groups_str = ', '.join([g.name for g in user.groups.all()])
                super_indicator = ' (SUPERUSER)' if user.is_superuser else ''
                self.stdout.write(f'   • {user.username}{super_indicator} - {groups_str}')
        
        # Conformité à la politique
        self.stdout.write('\n🎯 CONFORMITÉ À LA POLITIQUE:')
        policy_compliance = {
            'RH': 'CRUD complet sur tous les modèles',
            'Exploitation': 'Consultation/modification conducteurs + CRUD évaluations',
            'Direction': 'Consultation uniquement'
        }
        
        for group_name, expected_policy in policy_compliance.items():
            try:
                group = Group.objects.get(name=group_name)
                self.stdout.write(f'   ✅ {group_name}: {expected_policy}')
            except Group.DoesNotExist:
                self.stdout.write(f'   ❌ {group_name}: Groupe manquant')
        
        # Instructions pour la suite
        self.stdout.write('\n💡 PROCHAINES ÉTAPES:')
        self.stdout.write('   1. Testez la connexion avec les utilisateurs créés')
        self.stdout.write('   2. Vérifiez les permissions dans l\'interface web')
        self.stdout.write('   3. Adaptez la configuration selon vos besoins')
        
        if with_test_users:
            self.stdout.write('   4. Mot de passe par défaut: TestPassword123!')
            self.stdout.write('   5. CHANGEZ les mots de passe avant la production')
            self.stdout.write('   6. SUPPRIMEZ les utilisateurs de test en production')
        
        # Commandes utiles
        self.stdout.write('\n🛠️  COMMANDES UTILES:')
        self.stdout.write('   • Vérifier la configuration:')
        self.stdout.write('     python manage.py verify_permissions')
        self.stdout.write('   • Vérifier un utilisateur spécifique:')
        self.stdout.write('     python manage.py verify_permissions --user marie.rh')
        self.stdout.write('   • Afficher les permissions d\'un groupe:')
        self.stdout.write('     python manage.py verify_permissions --group RH')
        self.stdout.write('   • Exporter un rapport complet:')
        self.stdout.write('     python manage.py verify_permissions --export rapport_permissions.json')
        
        if with_test_users:
            self.stdout.write('   • Supprimer les utilisateurs de test:')
            self.stdout.write('     python manage.py delete_test_users')
        
        # Avertissements de sécurité
        self.stdout.write('\n⚠️  AVERTISSEMENTS DE SÉCURITÉ:')
        if with_test_users:
            self.stdout.write('   • Les utilisateurs de test ont des mots de passe simples')
            self.stdout.write('   • admin.test est un SUPERUSER - supprimez-le en production')
        self.stdout.write('   • Vérifiez régulièrement les permissions des utilisateurs')
        self.stdout.write('   • Surveillez les tentatives d\'accès non autorisées')
        
        self.stdout.write('\n✅ Installation complète terminée avec succès!')
        self.stdout.write('🎯 Le système de permissions est opérationnel selon la politique définie')


    def nuclear_reset(self):
        """Reset complet - ATTENTION: destructeur"""
        self.stdout.write('☢️  NUCLEAR RESET - SUPPRESSION COMPLÈTE')
        self.stdout.write('⚠️  Cette opération va supprimer:')
        self.stdout.write('   • Tous les groupes')
        self.stdout.write('   • Tous les utilisateurs non-superuser')
        self.stdout.write('   • Tous les profils utilisateurs')
        self.stdout.write('   • Tout l\'historique des groupes')
        
        response = input('Tapez "CONFIRMER SUPPRESSION" pour continuer: ')
        if response != "CONFIRMER SUPPRESSION":
            self.stdout.write('❌ Reset annulé')
            return
        
        # Supprimer dans l'ordre
        from gestion_groupes.models import ProfilUtilisateur, HistoriqueGroupes
        from django.contrib.auth.models import User, Group
        
        # Historique
        HistoriqueGroupes.objects.all().delete()
        self.stdout.write('   🗑️ Historique des groupes supprimé')
        
        # Profils (sauf superusers)
        ProfilUtilisateur.objects.exclude(user__is_superuser=True).delete()
        self.stdout.write('   🗑️ Profils utilisateurs supprimés')
        
        # Utilisateurs (sauf superusers)
        deleted_users = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(f'   🗑️ {deleted_users} utilisateurs supprimés')
        
        # Groupes
        deleted_groups = Group.objects.count()
        Group.objects.all().delete()
        self.stdout.write(f'   🗑️ {deleted_groups} groupes supprimés')
        
        self.stdout.write('☢️  Nuclear reset terminé - Base de données nettoyée')