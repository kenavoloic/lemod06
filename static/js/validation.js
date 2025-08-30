// static/js/validation.js - Validation côté client

/**
 * Système de validation en temps réel pour les formulaires
 */
class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.validFields = new Set();
        this.requiredFields = new Set();
        this.validationRules = new Map();
        this.debounceTimers = new Map();
        
        if (this.form) {
            this.init();
        }
    }
    
    init() {
        this.setupEventListeners();
        this.discoverFields();
    }
    
    setupEventListeners() {
        // Validation en temps réel
        this.form.addEventListener('input', (e) => {
            this.debounceValidation(e.target, 300);
        });
        
        this.form.addEventListener('change', (e) => {
            this.validateField(e.target);
        });
        
        // Validation avant soumission
        this.form.addEventListener('submit', (e) => {
            if (!this.validateAllFields()) {
                e.preventDefault();
                this.showValidationError();
            }
        });
    }
    
    discoverFields() {
        // Découvrir automatiquement les champs requis
        const requiredInputs = this.form.querySelectorAll('[required]');
        requiredInputs.forEach(input => {
            this.requiredFields.add(input.id || input.name);
            this.addValidationRule(input.id || input.name, {
                required: true,
                validator: (value) => value && value.trim().length > 0,
                errorMessage: 'Ce champ est obligatoire'
            });
        });
    }
    
    addValidationRule(fieldName, rule) {
        this.validationRules.set(fieldName, rule);
    }
    
    validateField(field) {
        const fieldName = field.id || field.name;
        const rule = this.validationRules.get(fieldName);
        
        if (!rule) return true;
        
        const isValid = rule.validator(field.value);
        
        if (isValid) {
            this.validFields.add(fieldName);
            this.setFieldState(field, 'valid');
            this.showFieldFeedback(field, 'valid', 'Valide');
        } else {
            this.validFields.delete(fieldName);
            this.setFieldState(field, 'invalid');
            this.showFieldFeedback(field, 'invalid', rule.errorMessage);
        }
        
        this.updateSubmitButton();
        return isValid;
    }
    
    debounceValidation(field, delay) {
        const fieldName = field.id || field.name;
        
        if (this.debounceTimers.has(fieldName)) {
            clearTimeout(this.debounceTimers.get(fieldName));
        }
        
        const timer = setTimeout(() => {
            this.validateField(field);
            this.debounceTimers.delete(fieldName);
        }, delay);
        
        this.debounceTimers.set(fieldName, timer);
    }
    
    setFieldState(field, state) {
        field.classList.remove('is-valid', 'is-invalid', 'valid', 'invalid');
        field.classList.add(`is-${state}`, state);
    }
    
    showFieldFeedback(field, type, message) {
        let feedbackDiv = field.parentNode.querySelector('.validation-feedback');
        
        if (!feedbackDiv) {
            feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'validation-feedback';
            field.parentNode.appendChild(feedbackDiv);
        }
        
        const icon = type === 'valid' ? 'fa-check-circle' : 'fa-times-circle';
        const className = type === 'valid' ? 'text-success' : 'text-danger';
        
        feedbackDiv.className = `validation-feedback ${className}`;
        feedbackDiv.innerHTML = `<i class="fas ${icon} me-1"></i>${message}`;
    }
    
    validateAllFields() {
        let allValid = true;
        
        this.validationRules.forEach((rule, fieldName) => {
            const field = this.form.querySelector(`[id="${fieldName}"], [name="${fieldName}"]`);
            if (field && !this.validateField(field)) {
                allValid = false;
            }
        });
        
        return allValid;
    }
    
    updateSubmitButton() {
        const submitBtn = this.form.querySelector('button[type="submit"]');
        if (!submitBtn) return;
        
        const allValid = this.requiredFields.size > 0 && 
                        this.validFields.size === this.requiredFields.size;
        
        if (allValid) {
            submitBtn.disabled = false;
            submitBtn.classList.add('enabled');
        } else {
            submitBtn.disabled = true;
            submitBtn.classList.remove('enabled');
        }
    }
    
    showValidationError() {
        const invalidFields = [];
        
        this.requiredFields.forEach(fieldName => {
            if (!this.validFields.has(fieldName)) {
                invalidFields.push(fieldName);
            }
        });
        
        if (invalidFields.length > 0) {
            const firstInvalidField = this.form.querySelector(
                `[id="${invalidFields[0]}"], [name="${invalidFields[0]}"]`
            );
            
            if (firstInvalidField) {
                firstInvalidField.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                firstInvalidField.classList.add('shake');
                setTimeout(() => {
                    firstInvalidField.classList.remove('shake');
                }, 500);
            }
        }
        
        this.showNotification(
            'Veuillez corriger les champs en rouge avant de soumettre.',
            'error'
        );
    }
    
    showNotification(message, type = 'info') {
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
        
        const notification = document.createElement('div');
        const bgColor = type === 'error' ? 'alert-danger' : 
                       type === 'success' ? 'alert-success' : 'alert-info';
        
        notification.className = `alert ${bgColor} alert-dismissible fade show`;
        notification.innerHTML = `
            <i class="fas ${type === 'error' ? 'fa-exclamation-triangle' : 
                          type === 'success' ? 'fa-check' : 'fa-info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

/**
 * Validation spécifique pour les évaluations
 */
class EvaluationValidator extends FormValidator {
    constructor() {
        super('evaluation-form');
        this.initializeEvaluationRules();
    }
    
    initializeEvaluationRules() {
        // Règles spécifiques aux évaluations
        this.addValidationRule('conducteur', {
            required: true,
            validator: (value) => value && value.length > 0,
            errorMessage: 'Veuillez sélectionner un conducteur'
        });
        
        this.addValidationRule('evaluateur', {
            required: true,
            validator: (value) => value && value.length > 0,
            errorMessage: 'Veuillez sélectionner un évaluateur'
        });
        
        this.addValidationRule('type_evaluation', {
            required: true,
            validator: (value) => value && value.length > 0,
            errorMessage: 'Veuillez sélectionner un type d\'évaluation'
        });
        
        this.addValidationRule('date_evaluation', {
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
        
        const fieldId = field.id || `note_${critereId}`;
        
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
    
    showValidationFeedback(critereId, type, message) {
        const validationDiv = document.getElementById(`validation-${critereId}`);
        if (!validationDiv) return;
        
        const icon = type === 'valid' ? 'fa-check-circle' : 'fa-times-circle';
        const className = type === 'valid' ? 'text-success' : 'text-danger';
        
        validationDiv.innerHTML = `
            <span class="validation-feedback ${className}">
                <i class="fas ${icon}"></i> ${message}
            </span>
        `;
    }
    
    handleCriteresLoaded() {
        // Réinitialiser les champs de notes
        this.clearNoteFields();
        
        // Ajouter les nouveaux champs de notes
        const noteInputs = document.querySelectorAll('.note-input');
        noteInputs.forEach(input => {
            const fieldId = input.id;
            this.requiredFields.add(fieldId);
            
            // Validation des notes avec règles spécifiques
            this.addValidationRule(fieldId, {
                required: true,
                validator: (value) => {
                    if (!value) return false;
                    const numValue = parseInt(value);
                    const min = parseInt(input.min);
                    const max = parseInt(input.max);
                    return !isNaN(numValue) && numValue >= min && numValue <= max;
                },
                errorMessage: `Note entre ${input.min} et ${input.max} requise`
            });
            
            // Validation en temps réel pour les notes
            input.addEventListener('input', () => {
                this.validateNoteField(input);
            });
            
            // Validation initiale si le champ a déjà une valeur
            if (input.value) {
                this.validateNoteField(input);
            }
        });
        
        this.updateSubmitButton();
    }
    
    clearNoteFields() {
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
}

/**
 * Utilitaires de validation
 */
const ValidationUtils = {
    // Validation d'email
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    // Validation de téléphone français
    isValidFrenchPhone(phone) {
        const phoneRegex = /^(?:(?:\+33|0)[1-9])(?:[0-9]{8})$/;
        return phoneRegex.test(phone.replace(/[\s.-]/g, ''));
    },
    
    // Validation de mot de passe fort
    isStrongPassword(password) {
        return password.length >= 8 &&
               /[a-z]/.test(password) &&
               /[A-Z]/.test(password) &&
               /[0-9]/.test(password);
    },
    
    // Validation de date
    isValidDate(dateString) {
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    },
    
    // Validation de plage de dates
    isDateInRange(dateString, minDate, maxDate) {
        const date = new Date(dateString);
        const min = new Date(minDate);
        const max = new Date(maxDate);
        return date >= min && date <= max;
    }
};

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    // Auto-initialisation pour les formulaires d'évaluation
    if (document.getElementById('evaluation-form')) {
        window.evaluationValidator = new EvaluationValidator();
        
        // Gestion HTMX pour le chargement des critères
        document.body.addEventListener('htmx:afterRequest', (evt) => {
            if (evt.detail.target.id === 'criteres-container') {
                window.evaluationValidator.handleCriteresLoaded();
            }
        });
    }
    
    // Auto-initialisation pour les autres formulaires
    const forms = document.querySelectorAll('form[data-validate="true"]');
    forms.forEach(form => {
        new FormValidator(form.id);
    });
});

// Export pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { FormValidator, EvaluationValidator, ValidationUtils };
}