from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

class Site(models.Model):
    """Site auquel est rattaché un conducteur"""
    nom_commune = models.CharField(max_length=255, verbose_name="Commune")
    code_postal = models.CharField(
            max_length = 5,
            verbose_name = "Code postal",
            validators = [
                RegexValidator(regex=r'^\d{5}$', message = "Un code postal est long de 5 caractères")
                ]
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        if self.nom_commune:
            self.nom_commune = self.nom_commune.strip()
        if self.code_postal:
            self.code_postal = self.code_postal.strip()
            if not self.code_postal.isdigit():
                raise ValidationError({'code_postal': 'Le code postal ne doit contenir que des chiffres'})
            if len(self.code_postal) != 5:
                raise ValidationError({'code_postal': 'Le code postal doit contenir exactement 5 chiffres'})

    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        ordering = ['nom_commune']

    def __str__(self):
        return f"{self.nom_commune}"

class Societe(models.Model):
    """Société à laquelle un conducteur est rattaché"""
    socid = models.PositiveIntegerField(unique=True)
    socnom = models.CharField(max_length=255, verbose_name="Nom société")
    socactif = models.BooleanField(default=True, verbose_name="Active")
    soccode = models.CharField(max_length=255, verbose_name="Code société")
    soccp = models.CharField(
            max_length = 5,
            verbose_name = "Code postal",
            validators = [
                RegexValidator(regex=r'^\d{5}$', message = "Un code postal est long de 5 caractères")
                ]
    )
    socvillib1 = models.CharField(max_length=255, verbose_name="Ville")
    date_creation = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.socnom:
            self.socnom = self.socnom.strip()
        if self.soccode:
            self.soccode = self.soccode.strip()
     
    class Meta:
        verbose_name = "Société"
        verbose_name_plural = "Sociétés"
        ordering = ['socnom']
        indexes = [models.Index(fields=['socnom']),]

    def __str__(self):
        return f"{self.socnom}"

class Service(models.Model):
    """Service auquel est rattaché l'évaluateur"""
    nom = models.CharField(max_length=255, verbose_name="Nom du service")
    abreviation = models.CharField(max_length=10, verbose_name="Abréviation")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom}"

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if self.abreviation:
            self.abreviation = self.abreviation.strip()

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['nom']
        
class Conducteur(models.Model):
    """Caractériques d'un conducteur"""
    salnom = models.CharField(max_length=255, verbose_name="nom")
    salnom2 = models.CharField(max_length=255, verbose_name="prénom")
    salsocid = models.ForeignKey(Societe, to_field='socid', on_delete=models.CASCADE, verbose_name="Société")
    salactif = models.BooleanField(default=True, verbose_name="Conducteur actif")
    site = models.ForeignKey(Site, on_delete=models.CASCADE, verbose_name="Site")
    interim_p = models.BooleanField(default=True, verbose_name="Intérim")
    sous_traitant_p = models.BooleanField(default=True, verbose_name="Sous-traitant")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")
    date_creation = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.salnom:
            self.salnom = self.salnom.strip()
        if self.salnom2:
            self.salnom2 = self.salnom2.strip()
        
    def __str__(self):
        return f"{self.salnom}"

    @property
    def nom_complet(self):
        return f"{self.salnom} {self.salnom2}"

    def get_last_evaluation_score(self):
        """Retourne le score de la dernière évaluation de ce conducteur"""
        derniere_evaluation = self.evaluation_set.order_by('-date_evaluation').first()
        if derniere_evaluation:
            return derniere_evaluation.calculate_score()
        return None

    class Meta:
        verbose_name = "Conducteur"
        verbose_name_plural = "Conducteurs"
        ordering = ['salnom','salnom2']

class Evaluateur(models.Model):
    """Utilisateur effectuant l'évaluation d'un conducteur"""
    nom = models.CharField(max_length=255, verbose_name="nom")
    prenom = models.CharField(max_length=255, verbose_name="prénom")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Service")

    def __str__(self):
            return f"{self.service.nom} {self.nom} {self.prenom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if self.prenom:
            self.prenom = self.prenom.strip()

    class Meta:
        verbose_name = "Évaluateur"
        verbose_name_plural = "Évaluateurs"
        ordering = ['nom', 'prenom']            
            

class TypologieEvaluation(models.Model):
    """ Types d'évaluation : avant le recrutement, évaluation de la conduite, évaluation du comportement"""
    nom = models.CharField(max_length=255, verbose_name="Nom")
    abreviation = models.CharField(max_length=10, verbose_name="Abréviation")
    description = models.TextField(verbose_name="Description")

    def __str__(self):
        return f"{self.nom}"

    class Meta:
        verbose_name="Type d'évaluation"
        verbose_name_plural = "Types d'évaluation"
    

class CritereEvaluation(models.Model):
    """Critères d'évaluation d'un conducteur"""
    nom = models.CharField(max_length=255)
    type_evaluation = models.ForeignKey(TypologieEvaluation, on_delete=models.CASCADE)
    valeur_mini = models.PositiveIntegerField()
    valeur_maxi = models.PositiveIntegerField()
    actif = models.BooleanField(default=True, help_text="Critère actuellement utilisé")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.valeur_mini}-{self.valeur_maxi})"

    def clean(self):
        if self.nom:
            self.nom = self.nom.strip()
        if not self.nom:
            raise ValidationError({'nom': "Un nom de critère est requis."})
        if self.valeur_mini is not None and self.valeur_maxi is not None:
            if self.valeur_mini >= self.valeur_maxi:
                raise ValidationError('La valeur minimale doit être inférieure à la valeur maximale.')

    class Meta:
        verbose_name = "Critère d'évaluation"
        verbose_name_plural = "Critères d'évaluation"
        ordering = ['nom']

class Evaluation(models.Model):
    """Session de notation regroupant toutes les notes d'un conducteur par un évaluateur à une date donnée"""
    date_evaluation = models.DateField(verbose_name="Date d'évaluation")
    evaluateur = models.ForeignKey(Evaluateur, on_delete=models.CASCADE, verbose_name="Évaluateur")
    conducteur = models.ForeignKey(Conducteur, on_delete=models.CASCADE, verbose_name="Conducteur")
    type_evaluation = models.ForeignKey(TypologieEvaluation, on_delete=models.CASCADE, verbose_name="Type d'évaluation")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.date_evaluation} - {self.conducteur} par {self.evaluateur} ({self.type_evaluation})"

    def clean(self):
        if not self.date_evaluation:
            raise ValidationError({'date_evaluation': "Une date d'évaluation est requise."})
        
        # Validation : vérifier que toutes les notes correspondent au type d'évaluation
        if self.pk:  # Si l'objet existe déjà (modification)
            notes_incompatibles = self.notes.exclude(critere__type_evaluation=self.type_evaluation)
            if notes_incompatibles.exists():
                raise ValidationError({
                    'type_evaluation': "Impossible de changer le type d'évaluation : des notes existent déjà pour d'autres types."
                })

    def calculate_score(self):
        """
        Calcule le score de l'évaluation en pourcentage
        Score = 100 * (somme des notes / somme des valeurs maximales)
        """
        # Récupérer toutes les notes de l'évaluation avec valeur non nulle
        notes = self.notes.filter(
            valeur__isnull=False,
            critere__actif=True
        ).select_related('critere')
    
        if not notes.exists():
            return None
    
        total_notes = 0
        total_max = 0
    
        for note in notes:
            total_notes += note.valeur
            total_max += note.critere.valeur_maxi
    
        if total_max == 0:
            return None
    
        score = (total_notes / total_max) * 100
        return round(score, 1)

    def get_completion_status(self):
        """Retourne le statut de completion de l'évaluation"""
        criteres_actifs = CritereEvaluation.objects.filter(
            type_evaluation=self.type_evaluation,
            actif=True
        ).count()
        
        notes_completes = self.notes.filter(valeur__isnull=False).count()
        
        if criteres_actifs == 0:
            return "Aucun critère actif"
        
        if notes_completes == criteres_actifs:
            return f"✅ Complet ({notes_completes}/{criteres_actifs})"
        else:
            return f"⚠️ Incomplet ({notes_completes}/{criteres_actifs})"

            
    class Meta:
        verbose_name = "Évaluation"
        verbose_name_plural = "Évaluations"
        unique_together = ['conducteur', 'date_evaluation', 'evaluateur', 'type_evaluation']
        ordering = ['-date_evaluation']
        indexes = [
            models.Index(fields=['date_evaluation']),
            models.Index(fields=['conducteur']),
            models.Index(fields=['type_evaluation']),
        ]
        
class Note(models.Model):
    """Note individuelle pour un critère spécifique dans une session d'évaluation"""
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, help_text="Session d'évaluation", related_name='notes')
    critere = models.ForeignKey(CritereEvaluation, on_delete=models.CASCADE, help_text="Critère évalué")
    valeur = models.PositiveIntegerField(null=True, blank=True, help_text="Note attribuée")
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.evaluation.conducteur} - {self.critere.nom}: {self.valeur or 'Non noté'}"

    def clean(self):
        # Validation de la valeur selon les bornes du critère
        if self.valeur is not None:
            if self.valeur < self.critere.valeur_mini or self.valeur > self.critere.valeur_maxi:
                raise ValidationError({
                    'valeur': f'La note doit être comprise entre {self.critere.valeur_mini} et {self.critere.valeur_maxi}.'
                })
        
        # Validation de cohérence : le critère doit correspondre au type d'évaluation
        if self.evaluation_id and self.critere_id:
            if self.critere.type_evaluation != self.evaluation.type_evaluation:
                raise ValidationError({
                    'critere': f'Le critère doit correspondre au type d\'évaluation "{self.evaluation.type_evaluation}".'
                })

    @property
    def date_evaluation(self):
        return self.evaluation.date_evaluation

    @property
    def evaluateur(self):
        return self.evaluation.evaluateur

    @property
    def conducteur(self):
        return self.evaluation.conducteur

    @property
    def type_evaluation(self):
        return self.evaluation.type_evaluation  # Plus simple maintenant !
    
    class Meta:
        verbose_name = "Note"
        verbose_name_plural = "Notes"
        unique_together = ['evaluation', 'critere']
        ordering = ['critere__nom']
        indexes = [
            models.Index(fields=['evaluation', 'critere']),
        ]
