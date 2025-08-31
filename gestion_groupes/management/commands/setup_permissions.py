# gestion_groupes/management/commands/setup_permissions_politique.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Configure les permissions selon la politique définie pour RH, Exploitation et Direction'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime toutes les permissions existantes des groupes avant de les reconfigurer',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans l\'exécuter',
        )
        parser.add_argument(
            '--show-available',
            action='store_true',
            help='Affiche toutes les permissions disponibles pour suivi_conducteurs',
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Vérifie que toutes les permissions nécessaires existent',
        )

    def handle(self, *args, **options):
        # Gestion des options spéciales d'abord
        if options.get('show_available'):
            self.show_available_permissions()
            return
        
        if options.get('verify'):
            self.verify_permissions_available()
            return
        
        # Configuration principale des permissions
        dry_run = options['dry_run']
        reset = options['reset']
        
        if dry_run:
            self.stdout.write('🔍 Mode simulation activé - Aucune modification ne sera effectuée')
        
        self.stdout.write('⚙️ Configuration des permissions selon la politique définie...\n')
        
        # Configuration des permissions par groupe
        permissions_config = {
            'RH': {
                'description': 'Ressources Humaines - Gestion complète des données',
                'permissions': [
                    # Conducteur - CRUD complet
                    'suivi_conducteurs.add_conducteur',
                    'suivi_conducteurs.change_conducteur',
                    'suivi_conducteurs.delete_conducteur',
                    'suivi_conducteurs.view_conducteur',
                    
                    # Evaluateur - CRUD complet
                    'suivi_conducteurs.add_evaluateur',
                    'suivi_conducteurs.change_evaluateur',
                    'suivi_conducteurs.delete_evaluateur',
                    'suivi_conducteurs.view_evaluateur',
                    
                    # Site - CRUD complet
                    'suivi_conducteurs.add_site',
                    'suivi_conducteurs.change_site',
                    'suivi_conducteurs.delete_site',
                    'suivi_conducteurs.view_site',
                    
                    # Societe - CRUD complet
                    'suivi_conducteurs.add_societe',
                    'suivi_conducteurs.change_societe',
                    'suivi_conducteurs.delete_societe',
                    'suivi_conducteurs.view_societe',
                    
                    # Service - CRUD complet
                    'suivi_conducteurs.add_service',
                    'suivi_conducteurs.change_service',
                    'suivi_conducteurs.delete_service',
                    'suivi_conducteurs.view_service',
                    
                    # CritereEvaluation - CRUD complet
                    'suivi_conducteurs.add_critereevaluation',
                    'suivi_conducteurs.change_critereevaluation',
                    'suivi_conducteurs.delete_critereevaluation',
                    'suivi_conducteurs.view_critereevaluation',
                    
                    # Evaluation - CRUD complet
                    'suivi_conducteurs.add_evaluation',
                    'suivi_conducteurs.change_evaluation',
                    'suivi_conducteurs.delete_evaluation',
                    'suivi_conducteurs.view_evaluation',
                    
                    # TypologieEvaluation - CRUD complet
                    'suivi_conducteurs.add_typologieevaluation',
                    'suivi_conducteurs.change_typologieevaluation',
                    'suivi_conducteurs.delete_typologieevaluation',
                    'suivi_conducteurs.view_typologieevaluation',
                    
                    # Note (implicite avec Evaluation)
                    'suivi_conducteurs.add_note',
                    'suivi_conducteurs.change_note',
                    'suivi_conducteurs.delete_note',
                    'suivi_conducteurs.view_note',
                ]
            },
            
            'Exploitation': {
                'description': 'Exploitation - Évaluations et consultation des conducteurs',
                'permissions': [
                    # Conducteur - Consultation et modification seulement
                    'suivi_conducteurs.view_conducteur',
                    'suivi_conducteurs.change_conducteur',
                    
                    # Evaluation - CRUD complet
                    'suivi_conducteurs.add_evaluation',
                    'suivi_conducteurs.change_evaluation',
                    'suivi_conducteurs.delete_evaluation',
                    'suivi_conducteurs.view_evaluation',
                    
                    # Note (nécessaire pour les évaluations)
                    'suivi_conducteurs.add_note',
                    'suivi_conducteurs.change_note',
                    'suivi_conducteurs.delete_note',
                    'suivi_conducteurs.view_note',
                    
                    # Permissions de lecture pour les données liées
                    'suivi_conducteurs.view_evaluateur',
                    'suivi_conducteurs.view_site',
                    'suivi_conducteurs.view_societe',
                    'suivi_conducteurs.view_service',
                    'suivi_conducteurs.view_critereevaluation',
                    'suivi_conducteurs.view_typologieevaluation',
                ]
            },
            
            'Direction': {
                'description': 'Direction - Consultation uniquement',
                'permissions': [
                    # Toutes les permissions de consultation
                    'suivi_conducteurs.view_conducteur',
                    'suivi_conducteurs.view_evaluateur',
                    'suivi_conducteurs.view_site',
                    'suivi_conducteurs.view_societe',
                    'suivi_conducteurs.view_service',
                    'suivi_conducteurs.view_critereevaluation',
                    'suivi_conducteurs.view_evaluation',
                    'suivi_conducteurs.view_typologieevaluation',
                    'suivi_conducteurs.view_note',
                ]
            }
        }
        
        # Traitement pour chaque groupe
        for nom_groupe, config in permissions_config.items():
            self.stdout.write(f'\n📋 Configuration du groupe "{nom_groupe}"')
            self.stdout.write(f'   {config["description"]}')
            
            if dry_run:
                self.stdout.write(f'   [SIMULATION] Permissions à configurer : {len(config["permissions"])}')
                for perm in config["permissions"]:
                    self.stdout.write(f'     - {perm}')
                continue
            
            try:
                # Récupérer ou créer le groupe
                group, created = Group.objects.get_or_create(name=nom_groupe)
                
                if created:
                    self.stdout.write(f'   ✅ Groupe "{nom_groupe}" créé')
                else:
                    self.stdout.write(f'   ℹ️  Groupe "{nom_groupe}" existe déjà')
                
                # Reset des permissions si demandé
                if reset:
                    group.permissions.clear()
                    self.stdout.write(f'   🗑️  Permissions existantes supprimées')
                
                # Ajouter les permissions
                permissions_ajoutees = 0
                permissions_non_trouvees = 0
                
                for perm_str in config['permissions']:
                    try:
                        app_label, codename = perm_str.split('.')
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                        
                        group.permissions.add(permission)
                        permissions_ajoutees += 1
                        self.stdout.write(f'     ✅ {perm_str}')
                        
                    except Permission.DoesNotExist:
                        self.stdout.write(f'     ❌ Permission non trouvée: {perm_str}')
                        permissions_non_trouvees += 1
                    except ValueError:
                        self.stdout.write(f'     ❌ Format invalide: {perm_str}')
                        permissions_non_trouvees += 1
                
                self.stdout.write(f'   📊 Résumé : {permissions_ajoutees} ajoutées, {permissions_non_trouvees} erreurs')
                
            except Exception as e:
                self.stdout.write(f'   ❌ Erreur lors de la configuration de {nom_groupe}: {str(e)}')
        
        # Résumé final
        self.stdout.write('\n' + '='*60)
        if not dry_run:
            self.stdout.write('✨ Configuration des permissions terminée!')
            
            # Afficher un résumé des groupes
            for nom_groupe in permissions_config.keys():
                try:
                    group = Group.objects.get(name=nom_groupe)
                    count = group.permissions.count()
                    self.stdout.write(f'   {nom_groupe}: {count} permissions')
                except Group.DoesNotExist:
                    self.stdout.write(f'   {nom_groupe}: Groupe non trouvé')
        else:
            self.stdout.write('🔍 Simulation terminée - Utilisez sans --dry-run pour appliquer les changements')
        
        # Instructions pour vérification
        self.stdout.write('\n💡 Pour vérifier la configuration :')
        self.stdout.write('   python manage.py verify_permissions')
        self.stdout.write('   python manage.py show_permissions --app suivi_conducteurs')


    def show_available_permissions(self):
        """Affiche toutes les permissions disponibles pour suivi_conducteurs"""
        self.stdout.write('\n📋 Permissions disponibles pour suivi_conducteurs:')
        
        try:
            content_types = ContentType.objects.filter(app_label='suivi_conducteurs')
            
            for ct in content_types:
                permissions = Permission.objects.filter(content_type=ct)
                self.stdout.write(f'\n   📄 Modèle: {ct.model}')
                for perm in permissions:
                    self.stdout.write(f'     • {perm.codename} - {perm.name}')
                    
        except Exception as e:
            self.stdout.write(f'❌ Erreur: {e}')
    
    def verify_permissions_available(self):
        """Vérifie que toutes les permissions nécessaires existent"""
        self.stdout.write('\n🔍 Vérification des permissions...')
        
        # Liste de toutes les permissions utilisées dans la politique
        required_permissions = {
            'add_conducteur', 'change_conducteur', 'delete_conducteur', 'view_conducteur',
            'add_evaluateur', 'change_evaluateur', 'delete_evaluateur', 'view_evaluateur',
            'add_site', 'change_site', 'delete_site', 'view_site',
            'add_societe', 'change_societe', 'delete_societe', 'view_societe',
            'add_service', 'change_service', 'delete_service', 'view_service',
            'add_critereevaluation', 'change_critereevaluation', 'delete_critereevaluation', 'view_critereevaluation',
            'add_evaluation', 'change_evaluation', 'delete_evaluation', 'view_evaluation',
            'add_typologieevaluation', 'change_typologieevaluation', 'delete_typologieevaluation', 'view_typologieevaluation',
            'add_note', 'change_note', 'delete_note', 'view_note',
        }
        
        missing_permissions = []
        
        for perm_codename in required_permissions:
            try:
                Permission.objects.get(
                    content_type__app_label='suivi_conducteurs',
                    codename=perm_codename
                )
            except Permission.DoesNotExist:
                missing_permissions.append(f'suivi_conducteurs.{perm_codename}')
        
        if missing_permissions:
            self.stdout.write('❌ Permissions manquantes:')
            for perm in missing_permissions:
                self.stdout.write(f'   • {perm}')
            self.stdout.write('\n💡 Exécutez "python manage.py migrate" pour créer les permissions manquantes')
        else:
            self.stdout.write('✅ Toutes les permissions requises sont disponibles')