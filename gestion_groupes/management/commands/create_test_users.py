# gestion_groupes/management/commands/create_test_users.py  
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from gestion_groupes.models import ProfilUtilisateur


class Command(BaseCommand):
    help = 'Crée des utilisateurs de test pour chaque groupe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=2,
            help='Nombre d\'utilisateurs par groupe (défaut: 2)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write('👥 Création d\'utilisateurs de test...')

        # Utilisateurs par groupe
        users_data = {
            'Direction': [
                {'username': 'dir1', 'first_name': 'Pierre', 'last_name': 'Directeur', 'email': 'pierre.directeur@transport.fr', 'poste': 'Directeur Général'},
                {'username': 'dir2', 'first_name': 'Marie', 'last_name': 'Adjointe', 'email': 'marie.adjointe@transport.fr', 'poste': 'Directrice Adjointe'},
            ],
            'RH': [
                {'username': 'rh1', 'first_name': 'Sophie', 'last_name': 'Martin', 'email': 'sophie.martin@transport.fr', 'poste': 'Responsable RH'},
                {'username': 'rh2', 'first_name': 'Thomas', 'last_name': 'Dubois', 'email': 'thomas.dubois@transport.fr', 'poste': 'Assistant RH'},
            ],
            'Exploitation': [
                {'username': 'exp1', 'first_name': 'Jean', 'last_name': 'Exploitation', 'email': 'jean.exploitation@transport.fr', 'poste': 'Chef d\'exploitation'},
                {'username': 'exp2', 'first_name': 'Claire', 'last_name': 'Terrain', 'email': 'claire.terrain@transport.fr', 'poste': 'Superviseur terrain'},
            ]
        }

        for groupe_name, users_list in users_data.items():
            try:
                group = Group.objects.get(name=groupe_name)
                
                for i, user_data in enumerate(users_list[:count]):
                    username = user_data['username']
                    
                    # Créer l'utilisateur s'il n'existe pas
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': user_data['first_name'],
                            'last_name': user_data['last_name'],
                            'email': user_data['email'],
                            'is_staff': True,
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        user.set_password('password123')  # Mot de passe par défaut
                        user.save()
                        
                        # Créer le profil
                        ProfilUtilisateur.objects.get_or_create(
                            user=user,
                            defaults={
                                'service': groupe_name,
                                'poste': user_data['poste'],
                                'telephone': f'05.56.{i+10:02d}.{i+20:02d}.{i+30:02d}',
                                'actif': True,
                            }
                        )
                        
                        # Ajouter au groupe
                        group.user_set.add(user)
                        
                        self.stdout.write(f'✅ Utilisateur créé: {username} -> {groupe_name}')
                    else:
                        self.stdout.write(f'ℹ️  Utilisateur existe: {username}')
                        
            except Group.DoesNotExist:
                self.stdout.write(f'❌ Groupe non trouvé: {groupe_name}')

        self.stdout.write(self.style.SUCCESS('✨ Utilisateurs de test créés!'))
        self.stdout.write('🔐 Mot de passe par défaut: password123')

