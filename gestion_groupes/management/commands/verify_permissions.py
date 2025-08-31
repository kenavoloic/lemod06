# gestion_groupes/management/commands/verify_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count


class Command(BaseCommand):
    help = 'Vérifie la configuration des permissions pour tous les groupes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--group',
            type=str,
            help='Vérifier un groupe spécifique',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Vérifier les permissions d\'un utilisateur spécifique',
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Affichage détaillé avec toutes les permissions',
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Exporter le rapport vers un fichier JSON',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔍 Vérification de la configuration des permissions\n')
        
        # Vérification spécifique d'un groupe
        if options.get('group'):
            self.verify_group(options['group'], options.get('detailed', False))
            return
        
        # Vérification spécifique d'un utilisateur
        if options.get('user'):
            self.verify_user(options['user'], options.get('detailed', False))
            return
        
        # Vérification complète
        report = self.generate_complete_report(options.get('detailed', False))
        
        # Export si demandé
        if options.get('export'):
            self.export_report(report, options['export'])

    def verify_group(self, group_name, detailed=False):
        """Vérifie les permissions d'un groupe spécifique"""
        try:
            group = Group.objects.get(name=group_name)
            self.stdout.write(f'📋 Groupe: {group.name}')
            
            # Permissions du groupe
            permissions = group.permissions.select_related('content_type').order_by(
                'content_type__app_label', 'content_type__model', 'codename'
            )
            
            # Statistiques
            total_permissions = permissions.count()
            suivi_permissions = permissions.filter(content_type__app_label='suivi_conducteurs').count()
            users_count = group.user_set.count()
            
            self.stdout.write(f'   👥 Utilisateurs: {users_count}')
            self.stdout.write(f'   🔐 Permissions totales: {total_permissions}')
            self.stdout.write(f'   📊 Permissions suivi_conducteurs: {suivi_permissions}')
            
            # Grouper par modèle
            permissions_by_model = {}
            for perm in permissions:
                model_name = perm.content_type.model
                if model_name not in permissions_by_model:
                    permissions_by_model[model_name] = []
                permissions_by_model[model_name].append(perm)
            
            # Affichage des permissions par modèle
            self.stdout.write('\n   📄 Permissions par modèle:')
            for model_name, model_permissions in permissions_by_model.items():
                crud_status = self.analyze_crud_permissions(model_permissions)
                self.stdout.write(f'     • {model_name}: {crud_status}')
                
                if detailed:
                    for perm in model_permissions:
                        self.stdout.write(f'       - {perm.codename} ({perm.name})')
            
            # Vérifier la conformité à la politique
            self.verify_group_policy_compliance(group_name, permissions)
            
        except Group.DoesNotExist:
            self.stdout.write(f'❌ Groupe "{group_name}" non trouvé')

    def verify_user(self, username, detailed=False):
        """Vérifie les permissions d'un utilisateur spécifique"""
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'👤 Utilisateur: {user.get_full_name() or user.username}')
            
            # Groupes de l'utilisateur
            groups = user.groups.all()
            self.stdout.write(f'   👥 Groupes: {", ".join([g.name for g in groups]) or "Aucun"}')
            
            # Permissions via les groupes
            group_permissions = Permission.objects.filter(group__user=user).distinct()
            
            # Permissions directes
            direct_permissions = user.user_permissions.all()
            
            # Toutes les permissions effectives
            all_permissions = Permission.objects.filter(
                models.Q(group__user=user) | models.Q(user=user)
            ).distinct()
            
            self.stdout.write(f'   🔐 Permissions via groupes: {group_permissions.count()}')
            self.stdout.write(f'   🔐 Permissions directes: {direct_permissions.count()}')
            self.stdout.write(f'   🔐 Total effectif: {all_permissions.count()}')
            
            # Permissions suivi_conducteurs
            suivi_permissions = all_permissions.filter(content_type__app_label='suivi_conducteurs')
            self.stdout.write(f'   📊 Permissions suivi_conducteurs: {suivi_permissions.count()}')
            
            if detailed:
                self.stdout.write('\n   📄 Détail des permissions:')
                current_app = None
                for perm in all_permissions.order_by('content_type__app_label', 'codename'):
                    if perm.content_type.app_label != current_app:
                        current_app = perm.content_type.app_label
                        self.stdout.write(f'     📱 {current_app}:')
                    self.stdout.write(f'       • {perm.codename}')
            
        except User.DoesNotExist:
            self.stdout.write(f'❌ Utilisateur "{username}" non trouvé')

    def generate_complete_report(self, detailed=False):
        """Génère un rapport complet de toutes les permissions"""
        report = {
            'groups': {},
            'summary': {},
            'compliance': {}
        }
        
        # Politique attendue
        expected_policy = {
            'RH': ['add', 'change', 'delete', 'view'],  # CRUD complet
            'Exploitation': ['view', 'change', 'add_evaluation', 'change_evaluation', 'delete_evaluation'],
            'Direction': ['view']  # Consultation uniquement
        }
        
        self.stdout.write('📊 RAPPORT COMPLET DES PERMISSIONS\n')
        self.stdout.write('='*60)
        
        # Analyser chaque groupe
        groups = Group.objects.all().order_by('name')
        for group in groups:
            self.stdout.write(f'\n📋 GROUPE: {group.name.upper()}')
            
            permissions = group.permissions.select_related('content_type').filter(
                content_type__app_label='suivi_conducteurs'
            ).order_by('content_type__model', 'codename')
            
            users_count = group.user_set.count()
            permissions_count = permissions.count()
            
            self.stdout.write(f'   👥 Utilisateurs: {users_count}')
            self.stdout.write(f'   🔐 Permissions: {permissions_count}')
            
            # Analyse par modèle
            models_analysis = {}
            for perm in permissions:
                model_name = perm.content_type.model
                if model_name not in models_analysis:
                    models_analysis[model_name] = {
                        'add': False, 'change': False, 'delete': False, 'view': False,
                        'permissions': []
                    }
                
                action = perm.codename.split('_')[0]  # add, change, delete, view
                if action in models_analysis[model_name]:
                    models_analysis[model_name][action] = True
                
                models_analysis[model_name]['permissions'].append(perm.codename)
            
            # Affichage de l'analyse
            if models_analysis:
                self.stdout.write('   📄 Analyse par modèle:')
                for model_name, analysis in models_analysis.items():
                    crud_icons = []
                    crud_icons.append('C' if analysis['add'] else '-')
                    crud_icons.append('R' if analysis['view'] else '-')
                    crud_icons.append('U' if analysis['change'] else '-')
                    crud_icons.append('D' if analysis['delete'] else '-')
                    
                    crud_status = ''.join(crud_icons)
                    self.stdout.write(f'     • {model_name:20} [{crud_status}]')
                    
                    if detailed:
                        for perm_code in analysis['permissions']:
                            self.stdout.write(f'       - {perm_code}')
            else:
                self.stdout.write('   ⚠️ Aucune permission suivi_conducteurs')
            
            # Stockage pour le rapport
            report['groups'][group.name] = {
                'users_count': users_count,
                'permissions_count': permissions_count,
                'models': models_analysis
            }
        
        # Résumé global
        self.stdout.write('\n' + '='*60)
        self.stdout.write('📈 RÉSUMÉ GLOBAL')
        
        total_groups = groups.count()
        total_users_in_groups = User.objects.filter(groups__isnull=False).distinct().count()
        total_users = User.objects.count()
        
        self.stdout.write(f'   👥 Groupes configurés: {total_groups}')
        self.stdout.write(f'   👤 Utilisateurs dans des groupes: {total_users_in_groups}/{total_users}')
        
        # Analyse de conformité
        self.stdout.write('\n🎯 CONFORMITÉ À LA POLITIQUE')
        for group_name in ['RH', 'Exploitation', 'Direction']:
            if group_name in report['groups']:
                compliance = self.check_policy_compliance(group_name, report['groups'][group_name])
                status_icon = '✅' if compliance['compliant'] else '⚠️'
                self.stdout.write(f'   {status_icon} {group_name}: {compliance["status"]}')
                
                if not compliance['compliant'] and compliance['issues']:
                    for issue in compliance['issues']:
                        self.stdout.write(f'     • {issue}')
            else:
                self.stdout.write(f'   ❌ {group_name}: Groupe manquant')
        
        return report

    def analyze_crud_permissions(self, permissions):
        """Analyse les permissions CRUD pour un ensemble de permissions"""
        crud = {'C': False, 'R': False, 'U': False, 'D': False}
        
        for perm in permissions:
            action = perm.codename.split('_')[0]
            if action == 'add':
                crud['C'] = True
            elif action == 'view':
                crud['R'] = True
            elif action == 'change':
                crud['U'] = True
            elif action == 'delete':
                crud['D'] = True
        
        # Construire la chaîne de status
        crud_chars = []
        for key, value in crud.items():
            crud_chars.append(key if value else '-')
        
        return f"[{''.join(crud_chars)}] ({len(permissions)} permissions)"

    def verify_group_policy_compliance(self, group_name, permissions):
        """Vérifie la conformité d'un groupe à la politique"""
        self.stdout.write('\n   🎯 Conformité à la politique:')
        
        # Définir les modèles critiques
        critical_models = [
            'conducteur', 'evaluateur', 'site', 'societe', 'service', 
            'critereevaluation', 'evaluation', 'typologieevaluation', 'note'
        ]
        
        # Analyser selon le groupe
        if group_name == 'RH':
            # RH doit avoir CRUD complet sur tout
            expected_permissions = set()
            for model in critical_models:
                for action in ['add', 'change', 'delete', 'view']:
                    expected_permissions.add(f'{action}_{model}')
            
            current_permissions = set(perm.codename for perm in permissions)
            missing = expected_permissions - current_permissions
            extra = current_permissions - expected_permissions
            
            if not missing and not extra:
                self.stdout.write('     ✅ Conformité parfaite')
            else:
                if missing:
                    self.stdout.write(f'     ⚠️ Permissions manquantes: {len(missing)}')
                if extra:
                    self.stdout.write(f'     ℹ️ Permissions supplémentaires: {len(extra)}')
        
        elif group_name == 'Exploitation':
            # Exploitation: consulte Conducteur, modifie conducteur, CRUD Evaluation
            required_patterns = [
                'view_conducteur', 'change_conducteur',
                'add_evaluation', 'change_evaluation', 'delete_evaluation', 'view_evaluation',
                'add_note', 'change_note', 'delete_note', 'view_note'
            ]
            
            current_codes = [perm.codename for perm in permissions]
            conformity_score = sum(1 for pattern in required_patterns if pattern in current_codes)
            
            self.stdout.write(f'     📊 Score de conformité: {conformity_score}/{len(required_patterns)}')
            
            if conformity_score == len(required_patterns):
                self.stdout.write('     ✅ Conformité aux exigences principales')
            else:
                missing = [p for p in required_patterns if p not in current_codes]
                self.stdout.write(f'     ⚠️ Permissions critiques manquantes: {", ".join(missing)}')
        
        elif group_name == 'Direction':
            # Direction: uniquement consultation
            non_view_permissions = [perm.codename for perm in permissions if not perm.codename.startswith('view_')]
            
            if not non_view_permissions:
                self.stdout.write('     ✅ Conformité: uniquement des permissions de consultation')
            else:
                self.stdout.write(f'     ⚠️ Permissions non conformes détectées: {len(non_view_permissions)}')
                for perm in non_view_permissions[:3]:  # Afficher les 3 premières
                    self.stdout.write(f'       • {perm}')

    def check_policy_compliance(self, group_name, group_data):
        """Vérifie la conformité d'un groupe et retourne un rapport"""
        compliance = {
            'compliant': True,
            'status': 'Conforme',
            'issues': []
        }
        
        models = group_data.get('models', {})
        
        if group_name == 'RH':
            # RH doit avoir CRUD complet
            expected_models = ['conducteur', 'evaluateur', 'site', 'societe', 'service', 
                             'critereevaluation', 'evaluation', 'typologieevaluation']
            
            for model in expected_models:
                if model not in models:
                    compliance['issues'].append(f'Modèle {model} manquant')
                    compliance['compliant'] = False
                else:
                    model_perms = models[model]
                    if not all([model_perms['add'], model_perms['change'], 
                              model_perms['delete'], model_perms['view']]):
                        compliance['issues'].append(f'CRUD incomplet pour {model}')
                        compliance['compliant'] = False
        
        elif group_name == 'Exploitation':
            # Vérifications spécifiques à l'exploitation
            if 'conducteur' in models:
                if not (models['conducteur']['view'] and models['conducteur']['change']):
                    compliance['issues'].append('Permissions conducteur insuffisantes')
                    compliance['compliant'] = False
            
            if 'evaluation' not in models:
                compliance['issues'].append('Aucune permission sur les évaluations')
                compliance['compliant'] = False
        
        elif group_name == 'Direction':
            # Direction doit avoir uniquement des permissions de consultation
            for model_name, model_perms in models.items():
                if model_perms['add'] or model_perms['change'] or model_perms['delete']:
                    compliance['issues'].append(f'Permissions non-consultation sur {model_name}')
                    compliance['compliant'] = False
        
        if not compliance['compliant']:
            compliance['status'] = f"Non conforme ({len(compliance['issues'])} problèmes)"
        
        return compliance

    def export_report(self, report, filename):
        """Exporte le rapport au format JSON"""
        import json
        from datetime import datetime
        
        # Ajouter des métadonnées
        report['metadata'] = {
            'generated_at': datetime.now().isoformat(),
            'total_groups': len(report['groups']),
            'command': 'verify_permissions'
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f'\n📁 Rapport exporté vers: {filename}')
            
        except Exception as e:
            self.stdout.write(f'❌ Erreur lors de l\'export: {e}')