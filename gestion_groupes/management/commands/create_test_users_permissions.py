# gestion_groupes/management/commands/create_test_users_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from gestion_groupes.models import ProfilUtilisateur, GroupeEtendu, HistoriqueGroupes


class Command(BaseCommand):
    help = 'Crée des utilisateurs de test avec les permissions configurées selon la politique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprime les utilisateurs de test existants avant de les recréer',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='password123',
            help='Mot de passe pour tous les utilisateurs de test (défaut: password123)',
        )

    def handle(self, *args, **options):
        password = options['password']
        reset = options['reset']
        
        self.stdout.write('👥 Création d\'utilisateurs de test avec permissions\n')
        
        # Configuration des utilisateurs de test
        test_users = {
            'RH': [
                {
                    'username': 'marie.rh',
                    'first_name': 'Marie',
                    'last_name': 'Dupont',
                    'email': 'marie.dupont@transport.fr',
                    'service': 'Ressources Humaines',
                    'poste': 'Responsable RH',
                    'telephone': '05.56.12.34.56'
                },
                {
                    'username': 'sophie.rh',
                    'first_name': 'Sophie',
                    'last_name': 'Martin',
                    'email': 'sophie.martin@transport.fr',
                    'service': 'Ressources Humaines',
                    'poste': 'Assistante RH',
                    'telephone': '05.56.12.34.57'
                }
            ],
            'Exploitation': [
                {
                    'username': 'jean.exploitation',
                    'first_name': 'Jean',
                    'last_name': 'Lefort',
                    'email': 'jean.lefort@transport.fr',
                    'service': 'Exploitation',
                    'poste': 'Chef d\'exploitation',
                    'telephone': '05.56.23.45.67'
                },
                {
                    'username': 'claire.exploitation',
                    'first_name': 'Claire',
                    'last_name': 'Dubois',
                    'email': 'claire.dubois@transport.fr',
                    'service': 'Exploitation',
                    'poste': 'Superviseur terrain',
                    'telephone': '05.56.23.45.68'
                }
            ],
            'Direction': [
                {
                    'username': 'pierre.direction',
                    'first_name': 'Pierre',
                    'last_name': 'Directeur',
                    'email': 'pierre.directeur@transport.fr',
                    'service': 'Direction',
                    'poste': 'Directeur Général',
                    'telephone': '05.56.01.02.03'
                },
                {
                    'username': 'isabelle.direction',
                    'first_name': 'Isabelle',
                    'last_name': 'Adjointe',
                    'email': 'isabelle.adjointe@transport.fr',
                    'service': 'Direction',
                    'poste': 'Directrice Adjointe',
                    'telephone': '05.56.01.02.04'
                }
            ]
        }
        
        created_users = 0
        updated_users = 0
        
        for group_name, users_data in test_users.items():
            self.stdout.write(f'📋 Création des utilisateurs pour le groupe {group_name}')
            
            # Vérifier que le groupe existe
            try:
                group = Group.objects.get(name=group_name)
                self.stdout.write(f'   ✅ Groupe {group_name} trouvé')
            except Group.DoesNotExist:
                self.stdout.write(f'   ❌ Groupe {group_name} non trouvé - créez-le d\'abord avec setup_groups')
                continue
            
            for user_data in users_data:
                username = user_data['username']
                
                try:
                    # Reset si demandé
                    if reset and User.objects.filter(username=username).exists():
                        User.objects.get(username=username).delete()
                        self.stdout.write(f'   🗑️  Utilisateur {username} supprimé')
                    
                    # Créer ou récupérer l'utilisateur
                    user, user_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': user_data['first_name'],
                            'last_name': user_data['last_name'],
                            'email': user_data['email'],
                            'is_active': True,
                            'is_staff': group_name in ['RH', 'Direction']  # Staff pour RH et Direction
                        }
                    )
                    
                    if user_created:
                        user.set_password(password)
                        user.save()
                        created_users += 1
                        self.stdout.write(f'   ✅ Utilisateur {username} créé')
                    else:
                        updated_users += 1
                        self.stdout.write(f'   ℹ️  Utilisateur {username} existe déjà')
                    
                    # Créer ou mettre à jour le profil
                    profil, profil_created = ProfilUtilisateur.objects.get_or_create(
                        user=user,
                        defaults={
                            'service': user_data['service'],
                            'poste': user_data['poste'],
                            'telephone': user_data.get('telephone', ''),
                            'actif': True,
                        }
                    )
                    
                    if not profil_created:
                        # Mettre à jour le profil existant
                        profil.service = user_data['service']
                        profil.poste = user_data['poste']
                        profil.telephone = user_data.get('telephone', '')
                        profil.actif = True
                        profil.save()
                    
                    # Ajouter l'utilisateur au groupe
                    if not user.groups.filter(name=group_name).exists():
                        user.groups.add(group)
                        self.stdout.write(f'     👥 Ajouté au groupe {group_name}')
                        
                        # Enregistrer dans l'historique si possible
                        try:
                            HistoriqueGroupes.objects.create(
                                group=group,
                                action='add_user',
                                utilisateur_cible=user,
                                details=f'Ajout automatique de {user.username} au groupe {group_name} (utilisateur de test)'
                            )
                        except Exception as e:
                            self.stdout.write(f'     ⚠️  Impossible d\'enregistrer l\'historique: {e}')
                
                except Exception as e:
                    self.stdout.write(f'   ❌ Erreur lors de la création de {username}: {e}')
                    continue
        
        # Créer un super utilisateur de test
        self.create_super_user(password, reset)
        
        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📊 RÉSUMÉ DE LA CRÉATION')
        self.stdout.write(f'   ✅ Utilisateurs créés: {created_users}')
        self.stdout.write(f'   ℹ️  Utilisateurs mis à jour: {updated_users}')
        
        # Afficher les informations de connexion
        self.stdout.write('\n🔐 INFORMATIONS DE CONNEXION')
        self.stdout.write(f'   Mot de passe pour tous les utilisateurs: {password}')
        self.stdout.write('\n📝 UTILISATEURS CRÉÉS:')
        
        for group_name, users_data in test_users.items():
            self.stdout.write(f'\n   👥 Groupe {group_name}:')
            for user_data in users_data:
                self.stdout.write(f'     • {user_data["username"]} - {user_data["first_name"]} {user_data["last_name"]}')
                self.stdout.write(f'       {user_data["poste"]} - {user_data["email"]}')
        
        # Vérifications de sécurité
        self.stdout.write('\n🛡️  VÉRIFICATIONS DE SÉCURITÉ')
        self.stdout.write('   ⚠️  Ces utilisateurs sont destinés aux TESTS uniquement')
        self.stdout.write('   ⚠️  Changez les mots de passe en production')
        self.stdout.write('   ⚠️  Supprimez ces comptes avant la mise en production')
        
        # Commandes utiles
        self.stdout.write('\n💡 COMMANDES UTILES')
        self.stdout.write('   Vérifier les permissions:')
        self.stdout.write('     python manage.py verify_permissions')
        self.stdout.write('   Vérifier un utilisateur spécifique:')
        self.stdout.write('     python manage.py verify_permissions --user marie.rh')
        self.stdout.write('   Supprimer tous les utilisateurs de test:')
        self.stdout.write('     python manage.py delete_test_users')

    def create_super_user(self, password, reset):
        """Crée un super utilisateur de test"""
        super_username = 'admin.test'
        
        try:
            if reset and User.objects.filter(username=super_username).exists():
                User.objects.get(username=super_username).delete()
                self.stdout.write(f'   🗑️  Super utilisateur {super_username} supprimé')
            
            if not User.objects.filter(username=super_username).exists():
                super_user = User.objects.create_superuser(
                    username=super_username,
                    email='admin.test@transport.fr',
                    password=password,
                    first_name='Admin',
                    last_name='Test'
                )
                
                # Créer le profil
                ProfilUtilisateur.objects.get_or_create(
                    user=super_user,
                    defaults={
                        'service': 'Administration',
                        'poste': 'Administrateur système',
                        'telephone': '05.56.00.00.00',
                        'actif': True,
                    }
                )
                
                self.stdout.write(f'   ✅ Super utilisateur {super_username} créé')
            else:
                self.stdout.write(f'   ℹ️  Super utilisateur {super_username} existe déjà')
        
        except Exception as e:
            self.stdout.write(f'   ❌ Erreur lors de la création du super utilisateur: {e}')
