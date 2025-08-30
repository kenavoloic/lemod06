# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Evaluation, Conducteur, Evaluateur, TypologieEvaluation, CritereEvaluation


class EvaluationForm(forms.ModelForm):
    """Formulaire pour créer une évaluation"""
    
    class Meta:
        model = Evaluation
        fields = ['conducteur', 'evaluateur', 'type_evaluation', 'date_evaluation']
        widgets = {
            'conducteur': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'evaluateur': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'type_evaluation': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
                'hx-get': 'load-criteres/',
                'hx-target': '#criteres-container',
                'hx-trigger': 'change',
            }),
            'date_evaluation': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtre des conducteurs actifs seulement
        self.fields['conducteur'].queryset = Conducteur.objects.filter(
            salactif=True
        ).select_related('salsocid', 'site').order_by('salnom', 'salnom2')
        
        # Tous les évaluateurs
        self.fields['evaluateur'].queryset = Evaluateur.objects.select_related(
            'service'
        ).order_by('service__nom', 'nom', 'prenom')
        
        # Tous les types d'évaluation
        self.fields['type_evaluation'].queryset = TypologieEvaluation.objects.all()
        
        # Labels personnalisés
        self.fields['conducteur'].label = "Conducteur à évaluer"
        self.fields['evaluateur'].label = "Évaluateur"
        self.fields['type_evaluation'].label = "Type d'évaluation"
        self.fields['date_evaluation'].label = "Date d'évaluation"
    
    def clean(self):
        cleaned_data = super().clean()
        conducteur = cleaned_data.get('conducteur')
        evaluateur = cleaned_data.get('evaluateur')
        type_evaluation = cleaned_data.get('type_evaluation')
        date_evaluation = cleaned_data.get('date_evaluation')
        
        if all([conducteur, evaluateur, type_evaluation, date_evaluation]):
            # Vérification de l'unicité
            if Evaluation.objects.filter(
                conducteur=conducteur,
                evaluateur=evaluateur,
                type_evaluation=type_evaluation,
                date_evaluation=date_evaluation
            ).exists():
                raise ValidationError(
                    "Une évaluation existe déjà pour ce conducteur, "
                    "évaluateur, type et date."
                )
        
        return cleaned_data


class NoteFormField(forms.IntegerField):
    """Champ personnalisé pour les notes avec validation dynamique"""
    
    def __init__(self, critere, *args, **kwargs):
        self.critere = critere
        kwargs.setdefault('min_value', critere.valeur_mini)
        kwargs.setdefault('max_value', critere.valeur_maxi)
        kwargs.setdefault('required', True)
        kwargs.setdefault('widget', forms.NumberInput(attrs={
            'class': 'form-control note-input',
            'min': critere.valeur_mini,
            'max': critere.valeur_maxi,
            'data-critere-id': critere.id,
            'hx-post': 'validate-field/',
            'hx-trigger': 'input changed delay:500ms',
            'hx-vals': f'{{"critere_id": "{critere.id}", "field_name": "note"}}',
            'hx-target': f'#validation-{critere.id}',
        }))
        
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        super().validate(value)
        if value is not None:
            if value < self.critere.valeur_mini or value > self.critere.valeur_maxi:
                raise ValidationError(
                    f'La note doit être comprise entre {self.critere.valeur_mini} '
                    f'et {self.critere.valeur_maxi}.'
                )
