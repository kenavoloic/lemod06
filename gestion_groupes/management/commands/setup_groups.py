# gestion_groupes/management/commands/setup_groups.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from gestion_groupes.models import ProfilUtilisateur, GroupeEtendu


class Command(BaseCommand):
    help = 'Configure les groupes et permissions pour l\'application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime et recrée tous les groupes',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('🗑️  Suppression des groupes existants...')
            Group.objects.filter(name__in=['Direction', 'RH', 'Exploitation']).delete()

        self.stdout.write('🔧 Configuration des groupes et permissions...')

        # Configuration des groupes
        groupes_config = {
            'Direction': {
                'description': 'Groupe des membres de la direction avec tous les privilèges',
                'couleur': '#dc3545',
                'niveau_acces': 5,
                'permissions': ['all']  # Toutes les permissions
            },
            'RH': {
                'description': 'Ressources Humaines - Gestion des conducteurs et recrutement',
                'couleur': '#28a745',
                'niveau_acces': 3,
                'permissions': [
                    'suivi_conducteurs.add_conducteur',
                    'suivi_conducteurs.change_conducteur',
                    'suivi_conducteurs.view_conducteur',
                    'suivi_conducteurs.add_evaluation',
                    'suivi_conducteurs.change_evaluation',
                    'suivi_conducteurs.view_evaluation',
                    'suivi_conducteurs.add_note',
                    'suivi_conducteurs.change_note',
                    'suivi_conducteurs.view_note',
                    'auth.view_user',
                ]
            },
            'Exploitation': {
                'description': 'Exploitation - Évaluations de conduite et comportementales',
                'couleur': '#ffc107',
                'niveau_acces': 2,
                'permissions': [
                    'suivi_conducteurs.add_evaluation',
                    'suivi_conducteurs.change_evaluation', 
                    'suivi_conducteurs.view_evaluation',
                    'suivi_conducteurs.add_note',
                    'suivi_conducteurs.change_note',
                    'suivi_conducteurs.view_note',
                    'suivi_conducteurs.view_conducteur',
                    'suivi_conducteurs.change_conducteur',
                ]
            }
        }

        for nom_groupe, config in groupes_config.items():
            # Créer ou récupérer le groupe
            group, created = Group.objects.get_or_create(name=nom_groupe)
            
            if created:
                self.stdout.write(f'✅ Groupe "{nom_groupe}" créé')
            else:
                self.stdout.write(f'ℹ️  Groupe "{nom_groupe}" existe déjà')

            # Créer ou mettre à jour l'extension du groupe
            groupe_etendu, _ = GroupeEtendu.objects.get_or_create(
                group=group,
                defaults={
                    'description': config['description'],
                    'couleur': config['couleur'],
                    'niveau_acces': config['niveau_acces'],
                    'actif': True,
                }
            )

            # Ajouter les permissions
            if 'all' in config['permissions']:
                # Toutes les permissions pour la Direction
                all_permissions = Permission.objects.all()
                group.permissions.set(all_permissions)
                self.stdout.write(f'   📋 Toutes les permissions ajoutées ({all_permissions.count()})')
            else:
                # Permissions spécifiques
                permissions_ajoutees = 0
                for perm_str in config['permissions']:
                    try:
                        if '.' in perm_str:
                            app_label, codename = perm_str.split('.')
                            permission = Permission.objects.get(
                                content_type__app_label=app_label,
                                codename=codename
                            )
                        else:
                            permission = Permission.objects.get(codename=perm_str)
                        
                        group.permissions.add(permission)
                        permissions_ajoutees += 1
                    except Permission.DoesNotExist:
                        self.stdout.write(f'   ⚠️  Permission non trouvée: {perm_str}')

                self.stdout.write(f'   📋 {permissions_ajoutees} permissions ajoutées')

        self.stdout.write(self.style.SUCCESS('✨ Configuration des groupes terminée!'))
