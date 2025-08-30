from django.contrib import admin
from django.db import models
from django.forms import TextInput, Textarea
from .models import (
    Site, Societe, Service, Conducteur, Evaluateur, 
    TypologieEvaluation, CritereEvaluation, Evaluation, Note
)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['nom_commune', 'code_postal', 'date_creation']
    list_filter = ['code_postal', 'date_creation']
    search_fields = ['nom_commune', 'code_postal']
    ordering = ['nom_commune']
    readonly_fields = ['date_creation']
    
    fieldsets = (
        (None, {
            'fields': ('nom_commune', 'code_postal')
        }),
        ('Informations système', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Societe)
class SocieteAdmin(admin.ModelAdmin):
    list_display = ['socnom', 'soccode', 'soccp', 'socvillib1', 'socactif', 'date_creation']
    list_filter = ['socactif', 'soccp', 'date_creation']
    search_fields = ['socnom', 'soccode', 'socvillib1']
    ordering = ['socnom']
    readonly_fields = ['date_creation']
    list_editable = ['socactif']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('socid', 'socnom', 'soccode', 'socactif')
        }),
        ('Adresse', {
            'fields': ('soccp', 'socvillib1')
        }),
        ('Informations système', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nom', 'abreviation', 'date_creation']
    search_fields = ['nom', 'abreviation']
    ordering = ['nom']
    readonly_fields = ['date_creation']


@admin.register(Conducteur)
class ConducteurAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'salsocid', 'site', 'salactif', 'nombre_evaluations', 'score_derniere_evaluation']
    list_filter = ['salactif', 'interim_p', 'sous_traitant_p', 'site', 'salsocid', 'date_creation']
    search_fields = ['salnom', 'salnom2', 'salsocid__socnom']
    ordering = ['salnom', 'salnom2']
    readonly_fields = ['date_creation', 'nombre_evaluations', 'score_derniere_evaluation']
    list_editable = ['salactif']
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('salnom', 'salnom2', 'date_naissance')
        }),
        ('Affectation', {
            'fields': ('salsocid', 'site')
        }),
        ('Statuts', {
            'fields': ('salactif', 'interim_p', 'sous_traitant_p')
        }),
        ('Statistiques', {
            'fields': ('nombre_evaluations', 'score_derniere_evaluation'),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'salsocid', 'site'
        ).prefetch_related('evaluation_set__notes__critere')

    def nom_complet(self, obj):
        return obj.nom_complet
    nom_complet.short_description = 'Nom complet'

    def nombre_evaluations(self, obj):
        """Compte le nombre d'évaluations pour ce conducteur"""
        return obj.evaluation_set.count()
    nombre_evaluations.short_description = 'Nb évaluations'
    nombre_evaluations.admin_order_field = 'evaluation_count'

    def score_derniere_evaluation(self, obj):
        """Calcule le score de la dernière évaluation"""
        derniere_eval = obj.evaluation_set.order_by('-date_evaluation').first()
        
        if not derniere_eval:
            return "Aucune évaluation"
        
        # Récupérer tous les critères actifs pour ce type d'évaluation
        criteres_actifs = CritereEvaluation.objects.filter(
            type_evaluation=derniere_eval.type_evaluation,
            actif=True
        )
        
        if not criteres_actifs:
            return "Aucun critère actif"
        
        # Vérifier qu'il y a autant de notes que de critères actifs
        notes_avec_valeur = derniere_eval.notes.filter(
            valeur__isnull=False,
            critere__actif=True,
            critere__type_evaluation=derniere_eval.type_evaluation
        )
        
        nb_criteres_actifs = criteres_actifs.count()
        nb_notes = notes_avec_valeur.count()
        
        if nb_notes == 0:
            return "Pas de notes"
        
        if nb_notes < nb_criteres_actifs:
            return f"Incomplet ({nb_notes}/{nb_criteres_actifs})"
        
        # Calcul du score : 100 * (somme notes / somme valeurs maxi)
        somme_notes = 0
        somme_maxi = 0
        
        for note in notes_avec_valeur:
            somme_notes += note.valeur
            somme_maxi += note.critere.valeur_maxi
        
        if somme_maxi == 0:
            return "Division par zéro"
        
        score = 100.0 * (somme_notes / somme_maxi)
        return f"{score:.1f}%"
    
    score_derniere_evaluation.short_description = 'Score dernière éval.'


@admin.register(Evaluateur)
class EvaluateurAdmin(admin.ModelAdmin):
    list_display = ['nom_complet', 'service']
    list_filter = ['service']
    search_fields = ['nom', 'prenom', 'service__nom']
    ordering = ['nom', 'prenom']
    
    def nom_complet(self, obj):
        return obj.nom_complet
    nom_complet.short_description = 'Nom complet'


@admin.register(TypologieEvaluation)
class TypologieEvaluationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'abreviation']
    search_fields = ['nom', 'abreviation']
    ordering = ['nom']
    
    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 60})},
    }


@admin.register(CritereEvaluation)
class CritereEvaluationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_evaluation', 'valeur_mini', 'valeur_maxi', 'actif', 'date_creation']
    list_filter = ['type_evaluation', 'actif', 'date_creation']
    search_fields = ['nom', 'type_evaluation__nom']
    ordering = ['type_evaluation', 'nom']
    readonly_fields = ['date_creation']
    list_editable = ['actif']
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'type_evaluation')
        }),
        ('Valeurs', {
            'fields': ('valeur_mini', 'valeur_maxi')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
        ('Informations système', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    fields = ['critere', 'valeur', 'range_info']
    readonly_fields = ['critere', 'range_info']
    can_delete = False
    
    def get_queryset(self, request):
        """Filtre les critères selon le type d'évaluation"""
        qs = super().get_queryset(request)
        return qs.select_related('critere', 'critere__type_evaluation').order_by('critere__nom')

    def range_info(self, obj):
        """Affiche la plage de valeurs autorisées"""
        if obj.critere:
            return f"({obj.critere.valeur_mini} - {obj.critere.valeur_maxi})"
        return ""
    range_info.short_description = "Plage"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtre les critères disponibles selon le type d'évaluation de l'évaluation parente"""
        if db_field.name == "critere":
            # Récupérer l'ID de l'évaluation depuis l'URL
            evaluation_id = request.resolver_match.kwargs.get('object_id')
            if evaluation_id:
                try:
                    evaluation = Evaluation.objects.get(pk=evaluation_id)
                    # Filtrer par type d'évaluation ET critères actifs
                    kwargs["queryset"] = CritereEvaluation.objects.filter(
                        type_evaluation=evaluation.type_evaluation,
                        actif=True
                    ).order_by('nom')
                except Evaluation.DoesNotExist:
                    kwargs["queryset"] = CritereEvaluation.objects.none()
            else:
                # Si pas d'évaluation définie, montrer seulement les critères actifs
                kwargs["queryset"] = CritereEvaluation.objects.filter(actif=True).order_by('nom')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['date_evaluation', 'conducteur', 'evaluateur', 'type_evaluation', 'nombre_notes', 'completude']
    list_filter = ['type_evaluation', 'date_evaluation', 'evaluateur__service', 'date_creation']
    search_fields = ['conducteur__salnom', 'conducteur__salnom2', 'evaluateur__nom', 'evaluateur__prenom']
    ordering = ['-date_evaluation']
    readonly_fields = ['date_creation', 'nombre_notes', 'completude']
    inlines = [NoteInline]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('date_evaluation', 'type_evaluation')
        }),
        ('Participants', {
            'fields': ('conducteur', 'evaluateur')
        }),
        ('Statistiques', {
            'fields': ('nombre_notes', 'completude'),
            'classes': ('collapse',)
        }),
        ('Informations système', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    def nombre_notes(self, obj):
        if obj.pk:
            return obj.notes.count()
        return 0
    nombre_notes.short_description = 'Nombre de notes'

    def completude(self, obj):
        """Vérifie si toutes les notes sont présentes pour les critères actifs"""
        if not obj.pk:
            return "Nouvelle évaluation"
        
        # Compter les critères actifs pour ce type d'évaluation
        criteres_actifs = CritereEvaluation.objects.filter(
            type_evaluation=obj.type_evaluation,
            actif=True
        ).count()
        
        # Compter les notes avec valeur
        notes_completes = obj.notes.filter(valeur__isnull=False).count()
        
        if criteres_actifs == 0:
            return "Aucun critère actif"
        
        if notes_completes == criteres_actifs:
            return f"✅ Complet ({notes_completes}/{criteres_actifs})"
        else:
            return f"⚠️ Incomplet ({notes_completes}/{criteres_actifs})"
    
    completude.short_description = 'Complétude'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'conducteur', 'evaluateur', 'type_evaluation', 'evaluateur__service'
        )


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['conducteur', 'critere', 'valeur', 'date_evaluation', 'evaluateur']
    list_filter = ['evaluation__type_evaluation', 'evaluation__date_evaluation', 'critere__type_evaluation']
    search_fields = [
        'evaluation__conducteur__salnom', 
        'evaluation__conducteur__salnom2',
        'critere__nom',
        'evaluation__evaluateur__nom'
    ]
    ordering = ['-evaluation__date_evaluation', 'critere__nom']
    readonly_fields = ['date_creation', 'conducteur', 'date_evaluation', 'evaluateur', 'type_evaluation']
    
    fieldsets = (
        ('Évaluation', {
            'fields': ('evaluation', 'conducteur', 'date_evaluation', 'evaluateur', 'type_evaluation')
        }),
        ('Note', {
            'fields': ('critere', 'valeur')
        }),
        ('Informations système', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )

    def conducteur(self, obj):
        return obj.conducteur
    conducteur.short_description = 'Conducteur'

    def date_evaluation(self, obj):
        return obj.date_evaluation
    date_evaluation.short_description = 'Date évaluation'

    def evaluateur(self, obj):
        return obj.evaluateur
    evaluateur.short_description = 'Évaluateur'

    def type_evaluation(self, obj):
        return obj.type_evaluation
    type_evaluation.short_description = 'Type évaluation'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'evaluation__conducteur', 
            'evaluation__evaluateur', 
            'evaluation__type_evaluation',
            'critere'
        )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtre les critères selon le type d'évaluation"""
        if db_field.name == "critere":
            kwargs["queryset"] = CritereEvaluation.objects.filter(actif=True).select_related('type_evaluation')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Configuration globale de l'admin
admin.site.site_header = "Administration - Système d'évaluation des conducteurs"
admin.site.site_title = "Admin Évaluation"
admin.site.index_title = "Bienvenue dans l'administration"

# Ajout du CSS personnalisé
class Media:
    css = {
        'all': ('admin/css/custom_admin.css',)
    }

# Application du Media à tous les admins
for admin_class in [SiteAdmin, SocieteAdmin, ServiceAdmin, ConducteurAdmin, 
                   EvaluateurAdmin, TypologieEvaluationAdmin, CritereEvaluationAdmin, 
                   EvaluationAdmin, NoteAdmin]:
    if not hasattr(admin_class, 'Media'):
        admin_class.Media = Media
