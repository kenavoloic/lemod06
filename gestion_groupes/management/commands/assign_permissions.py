# gestion_groupes/management/commands/assign_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Assigne des permissions spécifiques à un groupe'

    def add_arguments(self, parser):
        parser.add_argument('group_name', type=str, help='Nom du groupe')
        parser.add_argument('permissions', nargs='+', help='Liste des permissions (app.codename)')
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Retirer les permissions au lieu de les ajouter',
        )

    def handle(self, *args, **options):
        group_name = options['group_name']
        permissions_list = options['permissions']
        remove = options['remove']
        
        try:
            group = Group.objects.get(name=group_name)
            action = 'Retrait' if remove else 'Ajout'
            self.stdout.write(f'🔧 {action} de permissions pour le groupe "{group_name}"...')
            
            success_count = 0
            error_count = 0
            
            for perm_str in permissions_list:
                try:
                    if '.' in perm_str:
                        app_label, codename = perm_str.split('.')
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename
                        )
                    else:
                        permission = Permission.objects.get(codename=perm_str)
                    
                    if remove:
                        group.permissions.remove(permission)
                        self.stdout.write(f'  ➖ {perm_str} retirée')
                    else:
                        group.permissions.add(permission)
                        self.stdout.write(f'  ✅ {perm_str} ajoutée')
                    
                    success_count += 1
                    
                except Permission.DoesNotExist:
                    self.stdout.write(f'  ❌ Permission non trouvée: {perm_str}')
                    error_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✨ {action} terminé! {success_count} succès, {error_count} erreurs'
                )
            )
            
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Groupe "{group_name}" non trouvé'))
