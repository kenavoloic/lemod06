# configurations/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# Import des vues d'authentification et d'erreur
from gestion_groupes import auth_views
#from suivi_conducteurs import views as suivi_views  # Import des vues de test
# Vue d'accueil simple

def home_redirect(request):
    """Redirection intelligente selon l'état de connexion"""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    else:
        return redirect('/login/')

def home_view(request):
    """Vue d'accueil simple sans middleware qui interfère"""
    if request.user.is_authenticated:
        return redirect('/dashboard/')
    else:
        # Page d'accueil simple pour utilisateurs non connectés
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Suivi des Conducteurs</title>
            <meta charset="utf-8">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body class="bg-light">
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-body text-center">
                                <h1 class="card-title">🚛 Suivi des Conducteurs</h1>
                                <p class="card-text">Système de gestion et d'évaluation des conducteurs</p>
                                <a href="/login/" class="btn btn-primary btn-lg">Se connecter</a>
                                <hr>
                                <small class="text-muted">
                                    <a href="/admin/">Interface d'administration</a>
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)    

urlpatterns = [
    path('admin/', admin.site.urls),

    # Page d'accueil publique avec redirection intelligente
    path('', home_redirect, name='home'),

    # URLs de test temporaires
    # path('test/', suivi_views.test_view, name='test'),
    # path('dashboard-no-auth/', suivi_views.dashboard_no_auth, name='dashboard_no_auth'),

    # URLs d'authentification avec imports corrects
    path('login/', auth_views.user_login, name='login'),
    path('logout/', auth_views.user_logout, name='user_logout'),
    path('profile/', auth_views.user_profile, name='user_profile'),
    path('change-password/', auth_views.change_password, name='change_password'),
    
    # URLs des applications
    #path('', include('suivi_conducteurs.urls')),
    #path('groupes/', include('gestion_groupes.urls')),
    # Dashboard protégé
    path('dashboard/', include('suivi_conducteurs.urls')),
    path('groupes/', include('gestion_groupes.urls')),    
    # API pour les stats
    path('api/dashboard-stats/', auth_views.dashboard_stats, name='dashboard_stats'),
]

# Servir les fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Gestionnaires d'erreurs personnalisés
handler403 = auth_views.access_denied
handler404 = auth_views.page_not_found
handler500 = auth_views.server_error
