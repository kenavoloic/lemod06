# gestion_groupes/management/commands/show_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Affiche toutes les permissions disponibles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            type=str,
            help='Filtrer par application (ex: suivi_conducteurs)',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Filtrer par modèle (ex: conducteur)',
        )

    def handle(self, *args, **options):
        app_filter = options.get('app')
        model_filter = options.get('model')
        
        permissions = Permission.objects.select_related('content_type').order_by(
            'content_type__app_label', 'content_type__model', 'codename'
        )
        
        if app_filter:
            permissions = permissions.filter(content_type__app_label=app_filter)
            
        if model_filter:
            permissions = permissions.filter(content_type__model=model_filter)
        
        current_app = None
        current_model = None
        
        for perm in permissions:
            # Afficher l'en-tête d'application si elle change
            if current_app != perm.content_type.app_label:
                current_app = perm.content_type.app_label
                self.stdout.write(f'\n📱 Application: {current_app}')
                current_model = None
            
            # Afficher l'en-tête du modèle s'il change
            if current_model != perm.content_type.model:
                current_model = perm.content_type.model
                self.stdout.write(f'  📋 Modèle: {current_model}')
            
            # Afficher la permission
            self.stdout.write(f'    • {perm.codename} - {perm.name}')
            self.stdout.write(f'      Identifiant: {current_app}.{perm.codename}')
