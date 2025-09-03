# urls.py
from django.urls import path
from . import views

# Nom de l'application pour les namespaces
app_name = 'suivi_conducteurs'

urlpatterns = [
    # URLs de test temporaires
    # path('test/', views.test_view, name='test'),
    # path('dashboard-no-auth/', views.dashboard_no_auth, name='dashboard_no_auth'),
     
    # Page d'accueil (optionnel)
    path('', views.dashboard, name='dashboard'),
    
    # Évaluations
    path('evaluations/', views.evaluation_list, name='evaluation_list'),
    path('evaluations/create/', views.create_evaluation, name='create_evaluation'),
    path('evaluations/submit/', views.submit_evaluation, name='submit_evaluation'),
    path('evaluations/<int:pk>/', views.evaluation_detail, name='evaluation_detail'),

    # Conducteurs - NOUVELLES ROUTES
    path('conducteurs/', views.conducteur_list, name='conducteur_list'),
    path('conducteurs/<int:pk>/', views.conducteur_detail, name='conducteur_detail'),
    
    # Sociétés - NOUVELLES ROUTES
    path('societes/', views.societe_list, name='societe_list'),
    
    # Sites - NOUVELLES ROUTES  
    path('sites/', views.site_list, name='site_list'),
    
    # Statistiques - NOUVELLE ROUTE
    path('statistiques/', views.statistiques_view, name='statistiques'),
    
    # HTMX endpoints
    path('evaluations/load-criteres/', views.load_criteres_htmx, name='load_criteres_htmx'),
    path('evaluations/validate-field/', views.validate_field_htmx, name='validate_field_htmx'),
    #path('debug/', views.debug_data, name='debug_data'),
    #path('test-htmx/', views.test_htmx, name='test_htmx'),
]
