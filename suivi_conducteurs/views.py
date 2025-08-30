# suivi_conducteurs/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.core.exceptions import ValidationError
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
    from django.db.models import Count
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
    evaluateurs = Evaluateur.objects.all().select_related('service')
    types_evaluation = TypologieEvaluation.objects.all()
    
    context = {
        'conducteurs': conducteurs,
        'evaluateurs': evaluateurs,
        'types_evaluation': types_evaluation,
    }
    return render(request, 'suivi_conducteurs/create_evaluation.html', context)


@require_http_methods(["GET"])
def load_criteres_htmx(request):
    """Charge les critères actifs pour un type d'évaluation donné via HTMX"""
    # HTMX envoie la valeur du select avec le nom 'type_evaluation'
    type_evaluation_id = request.GET.get('type_evaluation')
    
    print(f"DEBUG: Tous les paramètres GET = {dict(request.GET)}")  # Debug complet
    print(f"DEBUG: type_evaluation reçu = {type_evaluation_id}")  # Debug
    
    if not type_evaluation_id or type_evaluation_id == '':
        print("DEBUG: Aucun type_evaluation fourni ou vide")  # Debug
        return HttpResponse('')
    
    try:
        type_evaluation = TypologieEvaluation.objects.get(id=type_evaluation_id)
        print(f"DEBUG: Type d'évaluation trouvé = {type_evaluation.nom}")  # Debug
        
        criteres = CritereEvaluation.objects.filter(
            type_evaluation=type_evaluation,
            actif=True
        ).order_by('nom')
        
        print(f"DEBUG: Nombre de critères actifs trouvés = {criteres.count()}")  # Debug
        for critere in criteres:
            print(f"DEBUG: Critère {critere.nom} - Min: {critere.valeur_mini}, Max: {critere.valeur_maxi}, Actif: {critere.actif}")
        
        context = {
            'criteres': criteres,
            'type_evaluation': type_evaluation,
        }
        return render(request, 'suivi_conducteurs/partials/criteres_form.html', context)
    
    except TypologieEvaluation.DoesNotExist:
        print("DEBUG: TypologieEvaluation non trouvée")  # Debug
        return HttpResponse('')
    except Exception as e:
        print(f"DEBUG: Erreur = {e}")  # Debug
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
    stats = {
        'moyenne': sum(notes_values) / len(notes_values) if notes_values else 0,
        'total_criteres': len(notes),
        'notes_attribuees': len(notes_values),
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
    """Liste des évaluations avec filtres"""
    evaluations = Evaluation.objects.select_related(
        'conducteur', 'evaluateur', 'type_evaluation'
    ).order_by('-date_evaluation')
    
    # Filtres
    conducteur_filter = request.GET.get('conducteur')
    type_filter = request.GET.get('type_evaluation')
    
    if conducteur_filter:
        evaluations = evaluations.filter(conducteur__id=conducteur_filter)
    
    if type_filter:
        evaluations = evaluations.filter(type_evaluation__id=type_filter)
    
    context = {
        'evaluations': evaluations,
        'conducteurs': Conducteur.objects.filter(salactif=True),
        'types_evaluation': TypologieEvaluation.objects.all(),
    }
    return render(request, 'suivi_conducteurs/evaluation_list.html', context)
