from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta

from .models import ProfilUtilisateur, HistoriqueGroupes


def user_login(request):
    """Vue de connexion personnalisée"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Créer le profil s'il n'existe pas
                    from .models import ProfilUtilisateur
                    try:
                        profil = user.profil
                    except ProfilUtilisateur.DoesNotExist:
                        ProfilUtilisateur.objects.create(
                            user=user,
                            service='Non défini',
                            poste='Non défini',
                            actif=user.is_active,
                        )
                    #comme pour le logout : pas très informatif tant qu'esthétiquement
                    # il n'est pas amélioré
                    #messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
                    
                    # Redirection après connexion réussie
                    next_page = request.GET.get('next')
                    if next_page and next_page not in ['/login/', '/login']:
                        return redirect(next_page)
                    else:
                        return redirect('/dashboard/')  # Redirection vers dashboard
                else:
                    messages.error(request, "Votre compte est désactivé.")
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
        else:
            messages.error(request, "Erreur dans le formulaire de connexion.")
    else:
        # Si l'utilisateur est déjà connecté
        if request.user.is_authenticated:
            return redirect('/dashboard/')
        
        form = AuthenticationForm()
    
    context = {
        'form': form,
        'title': "Connexion - Suivi des Conducteurs",
    }
    return render(request, 'registration/login.html', context)


def user_logout(request):
    """Vue de déconnexion"""
    if request.user.is_authenticated:
        user_name = request.user.get_full_name() or request.user.username
        logout(request)
        # pas très informatif
        #messages.info(request, f"Au revoir {user_name} ! Vous avez été déconnecté.")
    return redirect('login')


def user_profile(request):
    """Vue du profil utilisateur"""
    user = request.user
    
    try:
        profil = user.profil
    except ProfilUtilisateur.DoesNotExist:
        # Créer le profil s'il n'existe pas
        profil = ProfilUtilisateur.objects.create(
            user=user,
            service='Non défini',
            poste='Non défini',
            actif=user.is_active,
        )
    
    # Historique des groupes de l'utilisateur
    historique_groupes = HistoriqueGroupes.objects.filter(
        utilisateur_cible=user
    ).select_related('group', 'utilisateur_modifieur').order_by('-date_action')[:10]
    
    # Statistiques utilisateur
    stats = {
        'groupes_count': user.groups.count(),
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    
    context = {
        'user': user,
        'profil': profil,
        'historique_groupes': historique_groupes,
        'stats': stats,
    }
    return render(request, 'registration/profile.html', context)


def change_password(request):
    """Vue de changement de mot de passe"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Maintenir la session
            #Pas très informatif, voir login et logout
            #messages.success(request, "Mot de passe modifié avec succès !")
            return redirect('user_profile')
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'title': "Changer le mot de passe",
    }
    return render(request, 'registration/change_password.html', context)


def dashboard_stats(request):
    """API pour les statistiques du dashboard utilisateur"""
    # Stats pour l'utilisateur connecté
    stats = {}
    
    # Si l'utilisateur peut voir les évaluations
    if request.user.has_perm('suivi_conducteurs.view_evaluation'):
        from suivi_conducteurs.models import Evaluation, TypologieEvaluation
        
        # Évaluations ce mois-ci
        current_month = timezone.now().replace(day=1)
        evaluations_ce_mois = Evaluation.objects.filter(
            date_evaluation__gte=current_month
        ).count()
        
        # Évaluations par type
        evaluations_par_type = {}
        for type_eval in TypologieEvaluation.objects.all():
            count = Evaluation.objects.filter(type_evaluation=type_eval).count()
            evaluations_par_type[type_eval.nom] = count
        
        stats['evaluations'] = {
            'ce_mois': evaluations_ce_mois,
            'total': Evaluation.objects.count(),
            'par_type': evaluations_par_type,
        }
    
    # Si l'utilisateur peut voir les conducteurs
    if request.user.has_perm('suivi_conducteurs.view_conducteur'):
        from suivi_conducteurs.models import Conducteur
        stats['conducteurs'] = {
            'total': Conducteur.objects.count(),
            'actifs': Conducteur.objects.filter(salactif=True).count(),
        }
    
    # Stats des groupes utilisateur
    stats['user'] = {
        'groupes': [g.name for g in request.user.groups.all()],
        'permissions_count': request.user.user_permissions.count() + 
                           sum(g.permissions.count() for g in request.user.groups.all()),
    }
    
    return JsonResponse(stats)


def access_denied(request, exception=None):
    """Vue pour les erreurs 403 - Accès refusé"""
    context = {
        'title': "Accès refusé",
        'message': "Vous n'avez pas les permissions nécessaires pour accéder à cette page.",
        'user': request.user if request.user.is_authenticated else None,
    }
    return render(request, 'registration/403.html', context, status=403)


def page_not_found(request, exception):
    """Vue pour les erreurs 404 - Page non trouvée"""
    context = {
        'title': "Page non trouvée",
        'message': "La page que vous recherchez n'existe pas.",
        'request_path': request.path,
    }
    return render(request, 'registration/404.html', context, status=404)


def server_error(request):
    """Vue pour les erreurs 500 - Erreur serveur"""
    context = {
        'title': "Erreur du serveur",
        'message': "Une erreur interne s'est produite. Veuillez réessayer plus tard.",
    }
    return render(request, 'registration/500.html', context, status=500)
