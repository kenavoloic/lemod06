// static/js/evaluation-validation.js
/**
 * Système de validation progressive pour les évaluations
 * Utilise HTMX pour les interactions serveur
 */

class EvaluationValidator {
    constructor() {
        this.validFields = new Set();
        this.requiredFields = new Set();
        this.validationRules = new Map();
        this.debounceTimers = new Map();
        
        this.initializeValidation();
        this.setupEventListeners();
    }
    
    initializeValidation() {
        // Définir les règles de validation pour les champs principaux
        this.validationRules.set('conducteur', {
            required: true,
            validator: (value) => value && value.length > 0,
            errorMessage: 'Veuillez sélectionner un conducteur'
        });
        
        this.validationRules.set('evaluateur', {
            required: true,
            validator: (value) => value && value.length > 0,
            errorMessage: 'Veuillez sélectionner un évaluateur'
        });
        
        this.validationRules.set('type_evaluation', {
            required: true,
            validator: (value) => value && value.length > 0,
            errorMessage: 'Veuillez sélectionner un type d\'évaluation'
        });
        
        this.validationRules.set('date_evaluation', {
            required: true,
            validator: (value) => {
                if (!value) return false;
                const date = new Date(value);
                const today = new Date();
                const maxDate = new Date();
                maxDate.setFullYear(today.getFullYear() + 1);
                return date >= new Date('2020-01-01') && date <= maxDate;
            },
            errorMessage: 'Date invalide'
        });
        
        // Ajouter les champs requis initiaux
        this.validationRules.forEach((rule, fieldName) => {
            if (rule.required) {
                this.requiredFields.add(fieldName);
            }
        });
    }
    
    setupEventListeners() {
        // Validation en temps réel pour les champs principaux
        document.addEventListener('change', (e) => {
            if (e.target.matches('#conducteur, #evaluateur, #type_evaluation, #date_evaluation')) {
                this.validateField(e.target);
            }
        });
        
        // Validation progressive des notes avec debouncing
        document.addEventListener('input', (e) => {
            if (e.target.classList.contains('note-input')) {
                this.debounceValidation(e.target, 300);
            }
        });
        
        // Écouter les réponses HTMX
        document.body.addEventListener('htmx:afterRequest', (evt) => {
            if (evt.detail.target.id === 'criteres-container') {
                this.handleCriteresLoaded();
            }
        });
        
        // Validation avant soumission
        document.getElementById('evaluation-form')?.addEventListener('submit', (e) => {
            if (!this.validateAllFields()) {
                e.preventDefault();
                this.showValidationError();
            }
        });
    }
    
    validateField(field) {
        const fieldName = field.id;
        const rule = this.validationRules.get(fieldName);
        
        if (!rule) return;
        
        const isValid = rule.validator(field.value);
        
        if (isValid) {
            this.validFields.add(fieldName);
            this.setFieldState(field, 'valid');
        } else {
            this.validFields.delete(fieldName);
            this.setFieldState(field, 'invalid', rule.errorMessage);
        }
        
        this.updateSubmitButton();
    }
    
    validateNoteField(field) {
        const critereId = field.dataset.critereId;
        const min = parseInt(field.min);
        const max = parseInt(field.max);
        const value = field.value;
        
        let isValid = false;
        let errorMessage = '';
        
        if (!value || value.trim() === '') {
            errorMessage = 'Note requise';
        } else {
            const numValue = parseInt(value);
            if (isNaN(numValue)) {
                errorMessage = 'Nombre requis';
            } else if (numValue < min || numValue > max) {
                errorMessage = `Entre ${min} et ${max}`;
            } else {
                isValid = true;
            }
        }
        
        const fieldId = `note_${critereId}`;
        
        if (isValid) {
            this.validFields.add(fieldId);
            this.setFieldState(field, 'valid');
            this.showValidationFeedback(critereId, 'valid', 'Valide');
        } else {
            this.validFields.delete(fieldId);
            this.setFieldState(field, 'invalid');
            this.showValidationFeedback(critereId, 'invalid', errorMessage);
        }
        
        this.updateSubmitButton();
    }
    
    debounceValidation(field, delay) {
        const fieldId = field.id;
        
        // Annuler le timer précédent
        if (this.debounceTimers.has(fieldId)) {
            clearTimeout(this.debounceTimers.get(fieldId));
        }
        
        // Programmer une nouvelle validation
        const timer = setTimeout(() => {
            this.validateNoteField(field);
            this.debounceTimers.delete(fieldId);
        }, delay);
        
        this.debounceTimers.set(fieldId, timer);
    }
    
    setFieldState(field, state, message = '') {
        field.classList.remove('valid', 'invalid');
        field.classList.add(state);
        
        // Animation subtile
        field.style.transform = 'scale(1.02)';
        setTimeout(() => {
            field.style.transform = 'scale(1)';
        }, 150);
    }
    
    showValidationFeedback(critereId, type, message) {
        const validationDiv = document.getElementById(`validation-${critereId}`);
        if (!validationDiv) return;
        
        const icon = type === 'valid' ? 'fa-check-circle' : 'fa-times-circle';
        const className = type === 'valid' ? 'valid' : 'invalid';
        
        validationDiv.innerHTML = `
            <span class="validation-feedback ${className}">
                <i class="fas ${icon}"></i> ${message}
            </span>
        `;
        
        // Animation d'apparition
        validationDiv.style.opacity = '0';
        validationDiv.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            validationDiv.style.transition = 'all 0.3s ease';
            validationDiv.style.opacity = '1';
            validationDiv.style.transform = 'translateY(0)';
        }, 50);
    }
    
    handleCriteresLoaded() {
        // Réinitialiser les champs de notes
        this.clearNoteFields();
        
        // Ajouter les nouveaux champs de notes
        const noteInputs = document.querySelectorAll('.note-input');
        noteInputs.forEach(input => {
            const fieldId = input.id;
            this.requiredFields.add(fieldId);
            
            // Validation initiale si le champ a déjà une valeur
            if (input.value) {
                this.validateNoteField(input);
            }
        });
        
        this.updateSubmitButton();
        this.animateCriteresAppearance();
    }
    
    clearNoteFields() {
        // Supprimer tous les champs de notes des sets de validation
        const noteFieldsToRemove = [];
        this.requiredFields.forEach(field => {
            if (field.startsWith('note_')) {
                noteFieldsToRemove.push(field);
            }
        });
        
        noteFieldsToRemove.forEach(field => {
            this.requiredFields.delete(field);
            this.validFields.delete(field);
        });
    }
    
    animateCriteresAppearance() {
        const criteriaCards = document.querySelectorAll('.criteria-card');
        criteriaCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.4s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    validateAllFields() {
        let allValid = true;
        
        // Valider les champs principaux
        this.validationRules.forEach((rule, fieldName) => {
            if (rule.required) {
                const field = document.getElementById(fieldName);
                if (field) {
                    this.validateField(field);
                    if (!this.validFields.has(fieldName)) {
                        allValid = false;
                    }
                }
            }
        });
        
        // Valider les champs de notes
        const noteInputs = document.querySelectorAll('.note-input');
        noteInputs.forEach(input => {
            this.validateNoteField(input);
            if (!this.validFields.has(input.id)) {
                allValid = false;
            }
        });
        
        return allValid;
    }
    
    updateSubmitButton() {
        const submitBtn = document.getElementById('submit-btn');
        if (!submitBtn) return;
        
        const allValid = this.requiredFields.size > 0 && 
                        this.validFields.size === this.requiredFields.size;
        
        if (allValid) {
            submitBtn.disabled = false;
            submitBtn.classList.add('enabled');
            submitBtn.title = 'Créer l\'évaluation';
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.remove('enabled');
            submitBtn.title = `${this.requiredFields.size - this.validFields.size} champ(s) à compléter`;
        }
        
        // Mettre à jour le texte du bouton avec le compteur
        const validCount = this.validFields.size;
        const totalCount = this.requiredFields.size;
        
        if (totalCount > 0) {
            const normalContent = submitBtn.querySelector('.normal-content');
            if (normalContent && !allValid) {
                normalContent.innerHTML = `
                    <i class="fas fa-save"></i> 
                    Créer l'évaluation (${validCount}/${totalCount})
                `;
            } else if (normalContent && allValid) {
                normalContent.innerHTML = `
                    <i class="fas fa-save"></i> 
                    Créer l'évaluation
                `;
            }
        }
    }
    
    showValidationError() {
        const invalidFields = [];
        
        this.requiredFields.forEach(fieldName => {
            if (!this.validFields.has(fieldName)) {
                invalidFields.push(fieldName);
            }
        });
        
        // Faire défiler vers le premier champ invalide
        if (invalidFields.length > 0) {
            const firstInvalidField = document.getElementById(invalidFields[0]);
            if (firstInvalidField) {
                firstInvalidField.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                // Flash du champ
                firstInvalidField.style.animation = 'shake 0.5s';
                setTimeout(() => {
                    firstInvalidField.style.animation = '';
                }, 500);
            }
        }
        
        // Afficher une notification
        this.showNotification(
            'Veuillez corriger les champs en rouge avant de soumettre.',
            'error'
        );
    }
    
    showNotification(message, type = 'info') {
        // Créer ou réutiliser le container de notifications
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        
        // Créer la notification
        const notification = document.createElement('div');
        const bgColor = type === 'error' ? 'bg-danger' : 
                       type === 'success' ? 'bg-success' : 'bg-info';
        
        notification.className = `alert ${bgColor} text-white alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas ${type === 'error' ? 'fa-exclamation-triangle' : 
                          type === 'success' ? 'fa-check' : 'fa-info-circle'}"></i>
            ${message}
            <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
        `;
        
        container.appendChild(notification);
        
        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    // Méthode pour sauvegarder les données en cours (optionnel)
    saveProgress() {
        const formData = new FormData(document.getElementById('evaluation-form'));
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        localStorage.setItem('evaluation-progress', JSON.stringify(data));
    }
    
    // Méthode pour restaurer les données sauvegardées (optionnel)
    restoreProgress() {
        const saved = localStorage.getItem('evaluation-progress');
        if (saved) {
            try {
                const data = JSON.parse(saved);
                Object.entries(data).forEach(([key, value]) => {
                    const field = document.getElementById(key) || 
                                 document.querySelector(`[name="${key}"]`);
                    if (field) {
                        field.value = value;
                        if (field.id && this.validationRules.has(field.id)) {
                            this.validateField(field);
                        }
                    }
                });
            } catch (e) {
                console.warn('Impossible de restaurer les données sauvegardées:', e);
            }
        }
    }
    
    // Nettoyer les données sauvegardées
    clearProgress() {
        localStorage.removeItem('evaluation-progress');
    }
}

// CSS pour les animations
const animationStyles = `
    <style>
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
            20%, 40%, 60%, 80% { transform: translateX(5px); }
        }
        
        .form-control, .form-select {
            transition: all 0.3s ease;
        }
        
        .form-control.valid, .form-select.valid {
            border-color: #198754;
            box-shadow: 0 0 0 0.2rem rgba(25, 135, 84, 0.25);
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 8 8'%3e%3cpath fill='%23198754' d='m2.3 6.73.13-.13L4.6 4.43a.75.75 0 0 1 1.06 0l2.17 2.17.13.13a.25.25 0 0 0 .35-.35L6.1 4.07a1.25 1.25 0 0 0-1.77 0L2.15 6.25a.25.25 0 0 0 .35.35z'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
        
        .form-control.invalid, .form-select.invalid {
            border-color: #dc3545;
            box-shadow: 0 0 0 0.2rem rgba(220, 53, 69, 0.25);
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 12' width='12' height='12' fill='none' stroke='%23dc3545'%3e%3ccircle cx='6' cy='6' r='4.5'/%3e%3cpath d='m5.8 4.6 1.4 1.4M7.2 5.4 5.8 6.8m-1.4-1.4 1.4 1.4'/%3e%3c/svg%3e");
            background-repeat: no-repeat;
            background-position: right calc(0.375em + 0.1875rem) center;
            background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
        }
        
        .validation-feedback {
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .validation-feedback.valid {
            color: #198754;
        }
        
        .validation-feedback.invalid {
            color: #dc3545;
        }
        
        .submit-btn {
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: scale(0.98);
        }
        
        .submit-btn.enabled {
            opacity: 1;
            cursor: pointer;
            transform: scale(1);
        }
        
        .submit-btn.enabled:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
        }
        
        .criteria-card {
            transition: all 0.3s ease;
        }
        
        .criteria-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .note-input:focus {
            box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9998;
            backdrop-filter: blur(2px);
        }
        
        .loading-spinner {
            text-align: center;
        }
        
        .loading-spinner i {
            font-size: 2rem;
            color: #0d6efd;
        }
    </style>
`;

// Injection des styles
document.head.insertAdjacentHTML('beforeend', animationStyles);

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si nous sommes sur la page de création d'évaluation
    if (document.getElementById('evaluation-form')) {
        const validator = new EvaluationValidator();
        
        // Restaurer les données sauvegardées si disponibles
        validator.restoreProgress();
        
        // Sauvegarder automatiquement toutes les 30 secondes
        setInterval(() => {
            validator.saveProgress();
        }, 30000);
        
        // Nettoyer les données sauvegardées lors de la soumission réussie
        document.getElementById('evaluation-form').addEventListener('submit', () => {
            if (validator.validateAllFields()) {
                validator.clearProgress();
                
                // Afficher un overlay de chargement
                const overlay = document.createElement('div');
                overlay.className = 'loading-overlay';
                overlay.innerHTML = `
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <div class="mt-2">Création de l'évaluation...</div>
                    </div>
                `;
                document.body.appendChild(overlay);
            }
        });
        
        // Gestion des raccourcis clavier
        document.addEventListener('keydown', (e) => {
            // Ctrl+S pour sauvegarder les données
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                validator.saveProgress();
                validator.showNotification('Données sauvegardées localement', 'success');
            }
            
            // Échap pour effacer les données sauvegardées
            if (e.key === 'Escape') {
                const confirmClear = confirm('Voulez-vous effacer les données sauvegardées ?');
                if (confirmClear) {
                    validator.clearProgress();
                    validator.showNotification('Données sauvegardées supprimées', 'info');
                }
            }
        });
        
        // Message d'aide contextuelle
        const helpTooltip = document.createElement('div');
        helpTooltip.className = 'alert alert-info mt-3';
        helpTooltip.innerHTML = `
            <i class="fas fa-lightbulb"></i>
            <strong>Aide :</strong> 
            Les champs deviennent verts quand ils sont correctement remplis. 
            Utilisez <kbd>Ctrl+S</kbd> pour sauvegarder vos données.
            Les données sont automatiquement sauvegardées toutes les 30 secondes.
        `;
        
        // Insérer l'aide après le titre
        const title = document.querySelector('h1');
        if (title) {
            title.insertAdjacentElement('afterend', helpTooltip);
        }
        
        console.log('EvaluationValidator initialisé avec succès');
    }
});
