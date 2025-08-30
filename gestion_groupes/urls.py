from django.urls import path
from . import views
from . import auth_views

app_name = 'gestion_groupes'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_groupes, name='dashboard'),
    
    # Utilisateurs
    path('utilisateurs/', views.liste_utilisateurs, name='liste_utilisateurs'),
    path('utilisateurs/<int:user_id>/', views.detail_utilisateur, name='detail_utilisateur'),
    
    # Groupes
    path('groupes/', views.liste_groupes, name='liste_groupes'),
    path('groupes/<int:group_id>/', views.detail_groupe, name='detail_groupe'),
    
    # Historique
    path('historique/', views.historique_complet, name='historique'),
    
    # API
    path('api/stats/', views.api_stats_groupes, name='api_stats'),
]
