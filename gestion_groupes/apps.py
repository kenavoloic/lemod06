from django.apps import AppConfig


class GestionGroupesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_groupes'
    verbose_name = 'Gestion des Groupes'
    
    def ready(self):
        """Méthode appelée quand l'application est prête"""
        import gestion_groupes.signals




