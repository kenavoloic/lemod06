# gestion_groupes/views.py (VERSION NETTOYÉE)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta

from .models import ProfilUtilisateur, GroupeEtendu, HistoriqueGroupes


# LoginRequiredMiddleware protège automatiquement cette vue
def dashboard_groupes(request):
    """Dashboard principal de la gestion des groupes"""
    
    # Statistiques générales
    total_users = User.objects.count()
    total_groups = Group.objects.count()
    users_actifs = User.objects.filter(is_active=True).count()
    users_staff = User.objects.filter(is_staff=True).count()
    
    # Statistiques par groupe
    groupes_stats = []
    for group in Group.objects.all():
        try:
            groupe_etendu = group.groupe_etendu
            groupes_stats.append({
                'group': group,
                'groupe_etendu': groupe_etendu,
                'utilisateurs_count': group.user_set.count(),
                'permissions_count': group.permissions.count(),
            })
        except GroupeEtendu.DoesNotExist:
            groupes_stats.append({
                'group': group,
                'groupe_etendu': None,
                'utilisateurs_count': group.user_set.count(),
                'permissions_count': group.permissions.count(),
            })
    
    # Activité récente
    activites_recentes = HistoriqueGroupes.objects.select_related(
        'group', 'utilisateur_modifieur', 'utilisateur_cible'
    ).order_by('-date_action')[:10]
    
    # Utilisateurs récemment créés
    utilisateurs_recents = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
    ).order_by('-date_joined')[:5]
    
    context = {
        'total_users': total_users,
        'total_groups': total_groups,
        'users_actifs': users_actifs,
        'users_staff': users_staff,
        'groupes_stats': groupes_stats,
        'activites_recentes': activites_recentes,
        'utilisateurs_recents': utilisateurs_recents,
    }
    return render(request, 'gestion_groupes/dashboard.html', context)


# Seule la permission spécifique est requise, pas @login_required
@permission_required('auth.view_user', raise_exception=True)
def liste_utilisateurs(request):
    """Liste des utilisateurs avec filtres"""
    
    # Récupération des paramètres de filtre
    search = request.GET.get('search', '')
    group_filter = request.GET.get('group', '')
    actif_filter = request.GET.get('actif', '')
    staff_filter = request.GET.get('staff', '')
    
    # Construction de la requête
    users = User.objects.select_related('profil').prefetch_related('groups')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if group_filter:
        users = users.filter(groups__id=group_filter)
    
    if actif_filter == '1':
        users = users.filter(is_active=True)
    elif actif_filter == '0':
        users = users.filter(is_active=False)
    
    if staff_filter == '1':
        users = users.filter(is_staff=True)
    elif staff_filter == '0':
        users = users.filter(is_staff=False)
    
    users = users.order_by('last_name', 'first_name')
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    groupes = Group.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'groupes': groupes,
        'search': search,
        'group_filter': group_filter,
        'actif_filter': actif_filter,
        'staff_filter': staff_filter,
    }
    return render(request, 'gestion_groupes/liste_utilisateurs.html', context)


@permission_required('auth.view_group', raise_exception=True)
def liste_groupes(request):
    """Liste des groupes avec leurs informations étendues"""
    
    search = request.GET.get('search', '')
    niveau_filter = request.GET.get('niveau', '')
    actif_filter = request.GET.get('actif', '')
    
    groupes = Group.objects.select_related('groupe_etendu').annotate(
        users_count=Count('user'),
        permissions_count=Count('permissions')
    )
    
    if search:
        groupes = groupes.filter(name__icontains=search)
    
    if niveau_filter:
        groupes = groupes.filter(groupe_etendu__niveau_acces=niveau_filter)
    
    if actif_filter == '1':
        groupes = groupes.filter(groupe_etendu__actif=True)
    elif actif_filter == '0':
        groupes = groupes.filter(groupe_etendu__actif=False)
    
    groupes = groupes.order_by('-groupe_etendu__niveau_acces', 'name')
    
    # Pagination
    paginator = Paginator(groupes, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'niveau_filter': niveau_filter,
        'actif_filter': actif_filter,
    }
    return render(request, 'gestion_groupes/liste_groupes.html', context)


@permission_required('auth.view_user', raise_exception=True)
def detail_utilisateur(request, user_id):
    """Détail d'un utilisateur avec son profil et ses groupes"""
    
    user = get_object_or_404(User, id=user_id)
    
    try:
        profil = user.profil
    except ProfilUtilisateur.DoesNotExist:
        profil = None
    
    # Historique des modifications de groupes pour cet utilisateur
    historique = HistoriqueGroupes.objects.filter(
        utilisateur_cible=user
    ).select_related('group', 'utilisateur_modifieur').order_by('-date_action')[:10]
    
    context = {
        'user': user,
        'profil': profil,
        'historique': historique,
    }
    return render(request, 'gestion_groupes/detail_utilisateur.html', context)


@permission_required('auth.view_group', raise_exception=True)
def detail_groupe(request, group_id):
    """Détail d'un groupe avec ses utilisateurs et permissions"""
    
    group = get_object_or_404(Group, id=group_id)
    
    try:
        groupe_etendu = group.groupe_etendu
    except GroupeEtendu.DoesNotExist:
        groupe_etendu = None
    
    # Utilisateurs du groupe
    utilisateurs = group.user_set.select_related('profil').order_by('last_name', 'first_name')
    
    # Permissions du groupe
    permissions = group.permissions.select_related('content_type').order_by('content_type__app_label', 'name')
    
    # Historique du groupe
    historique = group.historique.select_related(
        'utilisateur_modifieur', 'utilisateur_cible', 'permission_cible'
    ).order_by('-date_action')[:15]
    
    context = {
        'group': group,
        'groupe_etendu': groupe_etendu,
        'utilisateurs': utilisateurs,
        'permissions': permissions,
        'historique': historique,
    }
    return render(request, 'gestion_groupes/detail_groupe.html', context)


@permission_required('auth.view_group', raise_exception=True)
def historique_complet(request):
    """Historique complet des modifications des groupes"""
    
    # Filtres
    group_filter = request.GET.get('group', '')
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    
    historique = HistoriqueGroupes.objects.select_related(
        'group', 'utilisateur_modifieur', 'utilisateur_cible', 'permission_cible'
    )
    
    if group_filter:
        historique = historique.filter(group__id=group_filter)
    
    if action_filter:
        historique = historique.filter(action=action_filter)
    
    if user_filter:
        historique = historique.filter(
            Q(utilisateur_modifieur__id=user_filter) |
            Q(utilisateur_cible__id=user_filter)
        )
    
    historique = historique.order_by('-date_action')
    
    # Pagination
    paginator = Paginator(historique, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Données pour les filtres
    groupes = Group.objects.all().order_by('name')
    actions = HistoriqueGroupes.ACTION_CHOICES
    utilisateurs = User.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    context = {
        'page_obj': page_obj,
        'groupes': groupes,
        'actions': actions,
        'utilisateurs': utilisateurs,
        'group_filter': group_filter,
        'action_filter': action_filter,
        'user_filter': user_filter,
    }
    return render(request, 'gestion_groupes/historique.html', context)


# Pas de décorateur nécessaire pour une API simple
def api_stats_groupes(request):
    """API pour les statistiques des groupes (pour graphiques)"""
    
    stats = []
    for group in Group.objects.all():
        try:
            groupe_etendu = group.groupe_etendu
            stats.append({
                'name': group.name,
                'users': group.user_set.count(),
                'permissions': group.permissions.count(),
                'niveau': groupe_etendu.niveau_acces,
                'couleur': groupe_etendu.couleur,
                'actif': groupe_etendu.actif,
            })
        except GroupeEtendu.DoesNotExist:
            stats.append({
                'name': group.name,
                'users': group.user_set.count(),
                'permissions': group.permissions.count(),
                'niveau': 1,
                'couleur': '#6c757d',
                'actif': True,
            })
    
    return JsonResponse({'stats': stats})
