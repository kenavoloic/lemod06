# suivi_conducteurs/views.py - Version corrigée complète
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Avg, Sum, Count, Q
from datetime import date
import json

from .models import (
    Conducteur, Evaluateur, TypologieEvaluation, 
    CritereEvaluation, Evaluation, Note, Societe, Site, Service
)
from .forms import EvaluationForm


@login_required
def dashboard(request):
    """Page d'accueil du module de suivi des conducteurs"""
    from datetime import date, timedelta
    
    # Statistiques rapides
    total_conducteurs = Conducteur.objects.filter(salactif=True).count() if request.user.has_perm('suivi_conducteurs.view_conducteur') else 0
    total_evaluations = Evaluation.objects.count() if request.user.has_perm('suivi_conducteurs.view_evaluation') else 0
    evaluations_ce_mois = Evaluation.objects.filter(
        date_evaluation__gte=date.today().replace(day=1)
    ).count() if request.user.has_perm('suivi_conducteurs.view_evaluation') else 0
    
    # Évaluations récentes (si permission)
    evaluations_recentes = []
    if request.user.has_perm('suivi_conducteurs.view_evaluation'):
        evaluations_recentes = Evaluation.objects.select_related(
            'conducteur', 'evaluateur', 'type_evaluation'
        ).order_by('-date_evaluation')[:5]
    
    context = {
        'total_conducteurs': total_conducteurs,
        'total_evaluations': total_evaluations,
        'evaluations_ce_mois': evaluations_ce_mois,
        'evaluations_recentes': evaluations_recentes,
        'user': request.user,
    }
    return render(request, 'suivi_conducteurs/dashboard.html', context)


@login_required
def create_evaluation(request):
    """Vue principale pour créer une évaluation"""
    conducteurs = Conducteur.objects.filter(salactif=True).select_related('salsocid', 'site')
    types_evaluation = TypologieEvaluation.objects.all()
    #evaluateurs = Evaluateur.objects.all().select_related('service')
    # evaluateurs = Evaluateur.objects.filter(
    #     service__nom__in=['Ressources Humaines', 'Exploitation']
    # ).select_related('service').order_by('service__nom', 'nom', 'prenom')

    # Filtrer les évaluateurs pour ne garder que ceux des groupes RH et Exploitation
    evaluateurs = Evaluateur.objects.filter(
        user__groups__name__in=['RH', 'Exploitation']
    ).select_related('service', 'user').prefetch_related('user__groups__groupe_etendu').distinct()

    evaluateur_connecte = None
    if hasattr(request.user, 'evaluateur'):
        evaluateur_connecte = request.user.evaluateur
        

    context = {
        'conducteurs': conducteurs,
        'evaluateurs': evaluateurs,
        'types_evaluation': types_evaluation,
        'evaluateur_connecte': evaluateur_connecte,
        'services_autorises': ['Ressources Humaines', 'Exploitation'],
    }
    return render(request, 'suivi_conducteurs/create_evaluation.html', context)


@require_http_methods(["GET"])
def load_criteres_htmx(request):
    """Charge les critères actifs pour un type d'évaluation donné via HTMX"""
    type_evaluation_id = request.GET.get('type_evaluation')
    
    print(f"DEBUG: Tous les paramètres GET = {dict(request.GET)}")
    print(f"DEBUG: type_evaluation reçu = {type_evaluation_id}")
    
    if not type_evaluation_id or type_evaluation_id == '':
        print("DEBUG: Aucun type_evaluation fourni ou vide")
        return HttpResponse('')
    
    try:
        type_evaluation = TypologieEvaluation.objects.get(id=type_evaluation_id)
        print(f"DEBUG: Type d'évaluation trouvé = {type_evaluation.nom}")
        
        criteres = CritereEvaluation.objects.filter(
            type_evaluation=type_evaluation,
            actif=True
        ).order_by('nom')
        
        print(f"DEBUG: Nombre de critères actifs trouvés = {criteres.count()}")
        for critere in criteres:
            print(f"DEBUG: Critère {critere.nom} - Min: {critere.valeur_mini}, Max: {critere.valeur_maxi}, Actif: {critere.actif}")
        
        context = {
            'criteres': criteres,
            'type_evaluation': type_evaluation,
        }
        return render(request, 'suivi_conducteurs/partials/criteres_form.html', context)
    
    except TypologieEvaluation.DoesNotExist:
        print("DEBUG: TypologieEvaluation non trouvée")
        return HttpResponse('')
    except Exception as e:
        print(f"DEBUG: Erreur = {e}")
        return HttpResponse('')


@require_http_methods(["POST"])
def validate_field_htmx(request):
    """Validation en temps réel d'un champ via HTMX"""
    field_name = request.POST.get('field_name')
    field_value = request.POST.get('field_value')
    critere_id = request.POST.get('critere_id')
    
    if not all([field_name, field_value, critere_id]):
        return JsonResponse({'valid': False, 'error': 'Données manquantes'})
    
    try:
        critere = CritereEvaluation.objects.get(id=critere_id)
        
        # Validation de la note
        try:
            note_value = int(field_value)
            if note_value < critere.valeur_mini or note_value > critere.valeur_maxi:
                return JsonResponse({
                    'valid': False, 
                    'error': f'Note entre {critere.valeur_mini} et {critere.valeur_maxi}'
                })
            return JsonResponse({'valid': True})
        except ValueError:
            return JsonResponse({'valid': False, 'error': 'Nombre requis'})
    
    except CritereEvaluation.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Critère invalide'})


@require_http_methods(["POST"])
def submit_evaluation(request):
    """Soumission finale de l'évaluation avec validation serveur complète"""
    
    # Récupération des données du formulaire
    conducteur_id = request.POST.get('conducteur')
    evaluateur_id = request.POST.get('evaluateur')
    type_evaluation_id = request.POST.get('type_evaluation')
    date_evaluation = request.POST.get('date_evaluation')
    
    if not all([conducteur_id, evaluateur_id, type_evaluation_id, date_evaluation]):
        messages.error(request, "Tous les champs obligatoires doivent être remplis.")
        return redirect('suivi_conducteurs:create_evaluation')
    
    try:
        # Validation des objets liés
        conducteur = get_object_or_404(Conducteur, id=conducteur_id)
        evaluateur = get_object_or_404(Evaluateur, id=evaluateur_id)
        type_evaluation = get_object_or_404(TypologieEvaluation, id=type_evaluation_id)
        
        # Récupération des critères actifs
        criteres_actifs = CritereEvaluation.objects.filter(
            type_evaluation=type_evaluation,
            actif=True
        )
        
        # Validation des notes
        notes_data = {}
        for critere in criteres_actifs:
            note_key = f'note_{critere.id}'
            note_value = request.POST.get(note_key)
            
            if not note_value:
                messages.error(request, f"La note pour le critère {critere.nom} est obligatoire.")
                return redirect('suivi_conducteurs:create_evaluation')
            
            try:
                note_value = int(note_value)
                if note_value < critere.valeur_mini or note_value > critere.valeur_maxi:
                    messages.error(
                        request, 
                        f"La note pour {critere.nom} doit être entre {critere.valeur_mini} et {critere.valeur_maxi}."
                    )
                    return redirect('suivi_conducteurs:create_evaluation')
                notes_data[critere.id] = note_value
            except ValueError:
                messages.error(request, f"La note pour {critere.nom} doit être un nombre.")
                return redirect('suivi_conducteurs:create_evaluation')
        
        # Création de l'évaluation avec transaction
        with transaction.atomic():
            # Vérification de l'unicité
            if Evaluation.objects.filter(
                conducteur=conducteur,
                evaluateur=evaluateur,
                type_evaluation=type_evaluation,
                date_evaluation=date_evaluation
            ).exists():
                messages.error(
                    request, 
                    "Une évaluation existe déjà pour ce conducteur, évaluateur, type et date."
                )
                return redirect('suivi_conducteurs:create_evaluation')
            
            # Création de l'évaluation
            evaluation = Evaluation.objects.create(
                conducteur=conducteur,
                evaluateur=evaluateur,
                type_evaluation=type_evaluation,
                date_evaluation=date_evaluation
            )
            
            # Création des notes
            for critere_id, note_value in notes_data.items():
                critere = CritereEvaluation.objects.get(id=critere_id)
                Note.objects.create(
                    evaluation=evaluation,
                    critere=critere,
                    valeur=note_value
                )
            
            messages.success(
                request, 
                f"Évaluation créée avec succès pour {conducteur.nom_complet}"
            )
            return redirect('suivi_conducteurs:evaluation_detail', pk=evaluation.id)
    
    except ValidationError as e:
        messages.error(request, f"Erreur de validation : {e}")
        return redirect('suivi_conducteurs:create_evaluation')
    except Exception as e:
        messages.error(request, f"Erreur inattendue : {e}")
        return redirect('suivi_conducteurs:create_evaluation')


@login_required
@permission_required('suivi_conducteurs.view_evaluation', raise_exception=True)
def evaluation_detail(request, pk):
    """Affichage détaillé d'une évaluation"""
    evaluation = get_object_or_404(
        Evaluation.objects.select_related(
            'conducteur', 'evaluateur', 'type_evaluation'
        ).prefetch_related('notes__critere'),
        pk=pk
    )
    
    notes = evaluation.notes.all().order_by('critere__nom')
    
    # Calcul de statistiques
    notes_values = [note.valeur for note in notes if note.valeur is not None]
    
    # Calcul du score en utilisant la méthode du modèle
    score_percentage = evaluation.calculate_score()
    
    stats = {
        'moyenne': sum(notes_values) / len(notes_values) if notes_values else 0,
        'total_criteres': len(notes),
        'notes_attribuees': len(notes_values),
        'score_percentage': score_percentage,
    }
    
    context = {
        'evaluation': evaluation,
        'notes': notes,
        'stats': stats,
    }
    return render(request, 'suivi_conducteurs/evaluation_detail.html', context)


@login_required
@permission_required('suivi_conducteurs.view_evaluation', raise_exception=True)
def evaluation_list(request):
    """Liste des évaluations avec filtres et scores"""
    # Requête de base avec les relations nécessaires
    evaluations = Evaluation.objects.select_related(
        'conducteur', 'evaluateur', 'type_evaluation', 'conducteur__salsocid', 'conducteur__site'
    ).prefetch_related(
        'notes__critere'
    ).order_by('-date_evaluation')
    
    # Récupérer les filtres
    conducteur_filter = request.GET.get('conducteur')
    type_filter = request.GET.get('type_evaluation')
    
    # Convertir en entier si présent
    conducteur_filter_id = None
    type_filter_id = None
    
    if conducteur_filter:
        try:
            conducteur_filter_id = int(conducteur_filter)
            evaluations = evaluations.filter(conducteur__id=conducteur_filter_id)
        except (ValueError, TypeError):
            pass
    
    if type_filter:
        try:
            type_filter_id = int(type_filter)
            evaluations = evaluations.filter(type_evaluation__id=type_filter_id)
        except (ValueError, TypeError):
            pass
    
    # Ajouter le score pour chaque évaluation
    evaluations_with_scores = []
    for evaluation in evaluations:
        # Calculer le score de cette évaluation en utilisant la méthode du modèle
        score = evaluation.calculate_score()
        evaluations_with_scores.append({
            'evaluation': evaluation,
            'score': score
        })
    
    context = {
        'evaluations_with_scores': evaluations_with_scores,
        'conducteurs': Conducteur.objects.filter(salactif=True),
        'types_evaluation': TypologieEvaluation.objects.all(),
        'selected_conducteur_id': conducteur_filter_id,
        'selected_type_id': type_filter_id,
    }
    return render(request, 'suivi_conducteurs/evaluation_list.html', context)

# suivi_conducteurs/views.py - Ajout des vues pour les conducteurs

# Ajouter ces vues à votre fichier views.py existant

@login_required
@permission_required('suivi_conducteurs.view_conducteur', raise_exception=True)
def conducteur_list(request):
    """Liste des conducteurs avec filtres"""
    # Récupération des paramètres de filtre
    search = request.GET.get('search', '')
    societe_filter = request.GET.get('societe', '')
    site_filter = request.GET.get('site', '')
    statut_filter = request.GET.get('statut', '')
    
    # Requête de base avec les relations nécessaires
    conducteurs = Conducteur.objects.select_related(
        'salsocid', 'site'
    ).prefetch_related(
        'evaluation_set__notes__critere'
    ).order_by('salnom', 'salnom2')
    
    # Application des filtres
    if search:
        from django.db.models import Q
        conducteurs = conducteurs.filter(
            Q(salnom__icontains=search) |
            Q(salnom2__icontains=search) |
            Q(salsocid__socnom__icontains=search)
        )
    
    if societe_filter:
        try:
            societe_id = int(societe_filter)
            conducteurs = conducteurs.filter(salsocid__socid=societe_id)
        except (ValueError, TypeError):
            pass
    
    if site_filter:
        try:
            site_id = int(site_filter)
            conducteurs = conducteurs.filter(site__id=site_id)
        except (ValueError, TypeError):
            pass
    
    if statut_filter == 'actif':
        conducteurs = conducteurs.filter(salactif=True)
    elif statut_filter == 'inactif':
        conducteurs = conducteurs.filter(salactif=False)
    elif statut_filter == 'interim':
        conducteurs = conducteurs.filter(interim_p=True)
    elif statut_filter == 'sous_traitant':
        conducteurs = conducteurs.filter(sous_traitant_p=True)
    
    # Ajouter des statistiques pour chaque conducteur
    conducteurs_with_stats = []
    for conducteur in conducteurs:
        # Dernière évaluation
        derniere_eval = conducteur.evaluation_set.order_by('-date_evaluation').first()
        
        # Score de la dernière évaluation
        dernier_score = None
        if derniere_eval:
            dernier_score = derniere_eval.calculate_score()
        
        # Nombre total d'évaluations
        nb_evaluations = conducteur.evaluation_set.count()
        
        conducteurs_with_stats.append({
            'conducteur': conducteur,
            'derniere_evaluation': derniere_eval,
            'dernier_score': dernier_score,
            'nb_evaluations': nb_evaluations,
        })
    
    # Données pour les filtres
    societes = Societe.objects.filter(socactif=True).order_by('socnom')
    sites = Site.objects.all().order_by('nom_commune')
    
    context = {
        'conducteurs_with_stats': conducteurs_with_stats,
        'societes': societes,
        'sites': sites,
        'search': search,
        'societe_filter': societe_filter,
        'site_filter': site_filter,
        'statut_filter': statut_filter,
        'total_count': len(conducteurs_with_stats),
    }
    return render(request, 'suivi_conducteurs/conducteur_list.html', context)


@login_required
@permission_required('suivi_conducteurs.view_conducteur', raise_exception=True)
def conducteur_detail(request, pk):
    """Détail d'un conducteur avec ses évaluations"""
    conducteur = get_object_or_404(
        Conducteur.objects.select_related('salsocid', 'site'),
        pk=pk
    )
    
    # Évaluations du conducteur
    evaluations = conducteur.evaluation_set.select_related(
        'evaluateur', 'type_evaluation'
    ).prefetch_related('notes__critere').order_by('-date_evaluation')
    
    # Ajouter le score pour chaque évaluation
    evaluations_with_scores = []
    for evaluation in evaluations:
        score = evaluation.calculate_score()
        evaluations_with_scores.append({
            'evaluation': evaluation,
            'score': score
        })
    
    # Statistiques du conducteur
    stats = {
        'nb_evaluations': evaluations.count(),
        'derniere_evaluation': evaluations.first(),
        'moyenne_scores': None,
        'evaluations_par_type': {},
    }
    
    # Calcul de la moyenne des scores
    scores = [item['score'] for item in evaluations_with_scores if item['score'] is not None]
    if scores:
        stats['moyenne_scores'] = sum(scores) / len(scores)
    
    # Évaluations par type
    from collections import defaultdict
    evals_par_type = defaultdict(list)
    for item in evaluations_with_scores:
        type_nom = item['evaluation'].type_evaluation.nom
        evals_par_type[type_nom].append(item)
    stats['evaluations_par_type'] = dict(evals_par_type)
    
    context = {
        'conducteur': conducteur,
        'evaluations_with_scores': evaluations_with_scores,
        'stats': stats,
    }
    return render(request, 'suivi_conducteurs/conducteur_detail.html', context)


@login_required
@permission_required('suivi_conducteurs.view_societe', raise_exception=True)
def societe_list(request):
    """Liste des sociétés"""
    search = request.GET.get('search', '')
    statut_filter = request.GET.get('statut', '')
    
    societes = Societe.objects.all().order_by('socnom')
    
    if search:
        from django.db.models import Q
        societes = societes.filter(
            Q(socnom__icontains=search) |
            Q(soccode__icontains=search) |
            Q(socvillib1__icontains=search)
        )
    
    if statut_filter == 'actif':
        societes = societes.filter(socactif=True)
    elif statut_filter == 'inactif':
        societes = societes.filter(socactif=False)
    
    # Ajouter le nombre de conducteurs par société
    societes_with_stats = []
    for societe in societes:
        nb_conducteurs = Conducteur.objects.filter(salsocid=societe).count()
        nb_conducteurs_actifs = Conducteur.objects.filter(salsocid=societe, salactif=True).count()
        
        societes_with_stats.append({
            'societe': societe,
            'nb_conducteurs': nb_conducteurs,
            'nb_conducteurs_actifs': nb_conducteurs_actifs,
        })
    
    context = {
        'societes_with_stats': societes_with_stats,
        'search': search,
        'statut_filter': statut_filter,
        'total_count': len(societes_with_stats),
    }
    return render(request, 'suivi_conducteurs/societe_list.html', context)


# @login_required
# @permission_required('suivi_conducteurs.view_site', raise_exception=True)
# def site_list(request):
#     """Liste des sites"""
#     search = request.GET.get('search', '')
    
#     sites = Site.objects.all().order_by('nom_commune')
    
#     if search:
#         from django.db.models import Q
#         sites = sites.filter(
#             Q(nom_commune__icontains=search) |
#             Q(code_postal__icontains=search)
#         )
    
#     # Ajouter le nombre de conducteurs par site
#     sites_with_stats = []
#     for site in sites:
#         nb_conducteurs = Conducteur.objects.filter(site=site).count()
#         nb_conducteurs_actifs = Conducteur.objects.filter(site=site, salactif=True).count()
        
#         sites_with_stats.append({
#             'site': site,
#             'nb_conducteurs': nb_conducteurs,
#             'nb_conducteurs_actifs': nb_conducteurs_actifs,
#         })
    
#     context = {
#         'sites_with_stats': sites_with_stats,
#         'search': search,
#         'total_count': len(sites_with_stats),
#     }
#     return render(request, 'suivi_conducteurs/site_list.html', context)

@login_required
@permission_required('suivi_conducteurs.view_site', raise_exception=True) 
def site_list(request):
    """Version optimisée de la liste des sites avec annotations"""
    
    # Récupérer les filtres
    search = request.GET.get('search', '').strip()
    code_postal_filter = request.GET.get('code_postal', '').strip()
    
    # Requête de base avec annotations pour les statistiques
    sites_query = Site.objects.annotate(
        nb_conducteurs=Count('conducteur', distinct=True),
        nb_conducteurs_actifs=Count(
            'conducteur', 
            filter=Q(conducteur__salactif=True),
            distinct=True
        ),
        nb_permanents=Count(
            'conducteur',
            filter=Q(
                conducteur__salactif=True,
                conducteur__interim_p=False,
                conducteur__sous_traitant_p=False
            ),
            distinct=True
        ),
        nb_interims=Count(
            'conducteur',
            filter=Q(
                conducteur__salactif=True,
                conducteur__interim_p=True
            ),
            distinct=True
        ),
        nb_sous_traitants=Count(
            'conducteur',
            filter=Q(
                conducteur__salactif=True,
                conducteur__sous_traitant_p=True
            ),
            distinct=True
        ),
        nb_societes=Count(
            'conducteur__salsocid',
            filter=Q(conducteur__salsocid__socactif=True),
            distinct=True
        )
    ).order_by('nom_commune')
    
    # Appliquer les filtres
    if search:
        sites_query = sites_query.filter(
            Q(nom_commune__icontains=search) | 
            Q(code_postal__icontains=search)
        )
    
    if code_postal_filter:
        sites_query = sites_query.filter(code_postal=code_postal_filter)
    
    # Récupérer les sites avec leurs statistiques
    sites_with_annotations = sites_query.prefetch_related(
        'conducteur_set__salsocid'
    )
    
    # Enrichir avec les listes de sociétés
    sites_with_stats = []
    for site in sites_with_annotations:
        # Récupérer les sociétés distinctes pour ce site
        societes_sur_site = Societe.objects.filter(
            conducteur__site=site,
            socactif=True
        ).distinct().order_by('socnom')[:10]
        
        sites_with_stats.append({
            'site': site,
            'nb_conducteurs': site.nb_conducteurs,
            'nb_conducteurs_actifs': site.nb_conducteurs_actifs,
            'nb_permanents': site.nb_permanents,
            'nb_interims': site.nb_interims,
            'nb_sous_traitants': site.nb_sous_traitants,
            'nb_societes': site.nb_societes,
            'societes_list': list(societes_sur_site)
        })
    
    # Codes postaux pour le filtre
    codes_postaux_disponibles = Site.objects.values_list(
        'code_postal', flat=True
    ).distinct().order_by('code_postal')
    
    context = {
        'sites_with_stats': sites_with_stats,
        'total_count': len(sites_with_stats),
        'codes_postaux_disponibles': codes_postaux_disponibles,
        'search': search,
        'code_postal_filter': code_postal_filter,
    }
    
    return render(request, 'suivi_conducteurs/site_list.html', context)

def statistiques_view(request):
    """Vue des statistiques globales"""
    # Statistiques de base
    stats = {
        'total_conducteurs': Conducteur.objects.filter(salactif=True).count(),
        'total_evaluations': Evaluation.objects.count(),
        'total_societes': Societe.objects.filter(socactif=True).count(),
        'total_sites': Site.objects.count(),
    }
    
    # Statistiques des conducteurs par catégorie
    conducteurs_stats = {
        'total_actifs': Conducteur.objects.filter(salactif=True).count(),
        'total_inactifs': Conducteur.objects.filter(salactif=False).count(),
        'interim': Conducteur.objects.filter(salactif=True, interim_p=True).count(),
        'sous_traitants': Conducteur.objects.filter(salactif=True, sous_traitant_p=True).count(),
        'permanents': Conducteur.objects.filter(salactif=True, interim_p=False, sous_traitant_p=False).count(),
    }
    
    # Conducteurs par site
    conducteurs_par_site = []
    for site in Site.objects.all():
        count_actifs = Conducteur.objects.filter(site=site, salactif=True).count()
        count_total = Conducteur.objects.filter(site=site).count()
        if count_total > 0:
            conducteurs_par_site.append({
                'site': site,
                'actifs': count_actifs,
                'total': count_total,
                'inactifs': count_total - count_actifs
            })
    
    # Conducteurs par société
    conducteurs_par_societe = []
    for societe in Societe.objects.filter(socactif=True):
        count_actifs = Conducteur.objects.filter(salsocid=societe, salactif=True).count()
        count_total = Conducteur.objects.filter(salsocid=societe).count()
        count_interim = Conducteur.objects.filter(salsocid=societe, salactif=True, interim_p=True).count()
        count_sous_traitants = Conducteur.objects.filter(salsocid=societe, salactif=True, sous_traitant_p=True).count()
        if count_total > 0:
            conducteurs_par_societe.append({
                'societe': societe,
                'actifs': count_actifs,
                'total': count_total,
                'inactifs': count_total - count_actifs,
                'interim': count_interim,
                'sous_traitants': count_sous_traitants,
                'permanents': count_actifs - count_interim - count_sous_traitants
            })
    
    # Évaluations par mois (derniers 12 mois)
    from datetime import date, timedelta
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    
    fin_periode = date.today()
    debut_periode = fin_periode - timedelta(days=365)
    
    evaluations_par_mois = Evaluation.objects.filter(
        date_evaluation__gte=debut_periode
    ).annotate(
        mois=TruncMonth('date_evaluation')
    ).values('mois').annotate(
        count=Count('id')
    ).order_by('mois')
    
    # Scores moyens par type d'évaluation
    scores_par_type = {}
    for type_eval in TypologieEvaluation.objects.all():
        evaluations = Evaluation.objects.filter(type_evaluation=type_eval)
        scores = []
        for eval in evaluations:
            score = eval.calculate_score()
            if score is not None:
                scores.append(score)
        
        if scores:
            scores_par_type[type_eval.nom] = {
                'moyenne': sum(scores) / len(scores),
                'count': len(scores),
                'total_evaluations': evaluations.count()
            }
    
    context = {
        'stats': stats,
        'conducteurs_stats': conducteurs_stats,
        'conducteurs_par_site': conducteurs_par_site,
        'conducteurs_par_societe': conducteurs_par_societe,
        'evaluations_par_mois': list(evaluations_par_mois),
        'scores_par_type': scores_par_type,
    }
    return render(request, 'suivi_conducteurs/statistiques.html', context)

# Vue pour les statistiques (placeholder)
# @login_required
# @permission_required('suivi_conducteurs.view_evaluation', raise_exception=True)
# def statistiques_view(request):
#     """Vue des statistiques globales"""
#     # Statistiques de base
#     stats = {
#         'total_conducteurs': Conducteur.objects.filter(salactif=True).count(),
#         'total_evaluations': Evaluation.objects.count(),
#         'total_societes': Societe.objects.filter(socactif=True).count(),
#         'total_sites': Site.objects.count(),
#     }
    
#     # Évaluations par mois (derniers 12 mois)
#     from datetime import date, timedelta
#     from django.db.models import Count
#     from django.db.models.functions import TruncMonth
    
#     fin_periode = date.today()
#     debut_periode = fin_periode - timedelta(days=365)
    
#     evaluations_par_mois = Evaluation.objects.filter(
#         date_evaluation__gte=debut_periode
#     ).annotate(
#         mois=TruncMonth('date_evaluation')
#     ).values('mois').annotate(
#         count=Count('id')
#     ).order_by('mois')
    
#     # Scores moyens par type d'évaluation
#     from django.db.models import Avg
#     scores_par_type = {}
#     for type_eval in TypologieEvaluation.objects.all():
#         evaluations = Evaluation.objects.filter(type_evaluation=type_eval)
#         scores = []
#         for eval in evaluations:
#             score = eval.calculate_score()
#             if score is not None:
#                 scores.append(score)
        
#         if scores:
#             scores_par_type[type_eval.nom] = {
#                 'moyenne': sum(scores) / len(scores),
#                 'count': len(scores),
#                 'total_evaluations': evaluations.count()
#             }
    
#     context = {
#         'stats': stats,
#         'evaluations_par_mois': list(evaluations_par_mois),
#         'scores_par_type': scores_par_type,
#     }
#     return render(request, 'suivi_conducteurs/statistiques.html', context)
