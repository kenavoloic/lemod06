// static/js/utils.js - Utilitaires JavaScript

/**
 * Utilitaires généraux pour l'application
 */
const AppUtils = {
    /**
     * Affiche une notification toast
     */
    showNotification(message, type = 'info', duration = 5000) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        
        const toastId = 'toast-' + Date.now();
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        
        const colorMap = {
            success: 'text-bg-success',
            error: 'text-bg-danger',
            warning: 'text-bg-warning',
            info: 'text-bg-info'
        };
        
        const toastHtml = `
            <div id="${toastId}" class="toast ${colorMap[type]}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas ${iconMap[type]} me-2"></i>
                    <strong class="me-auto">Notification</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: duration });
        toast.show();
        
        // Nettoyage après disparition
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },

    /**
     * Confirme une action avec une boîte de dialogue
     */
    confirmAction(message, callback, options = {}) {
        const defaults = {
            title: 'Confirmation',
            confirmText: 'Confirmer',
            cancelText: 'Annuler',
            type: 'warning'
        };
        const config = { ...defaults, ...options };
        
        if (confirm(`${config.title}\n\n${message}`)) {
            callback();
        }
    },

    /**
     * Formate une date en français
     */
    formatDate(date, format = 'dd/mm/yyyy') {
        const d = new Date(date);
        const day = d.getDate().toString().padStart(2, '0');
        const month = (d.getMonth() + 1).toString().padStart(2, '0');
        const year = d.getFullYear();
        const hours = d.getHours().toString().padStart(2, '0');
        const minutes = d.getMinutes().toString().padStart(2, '0');
        
        return format
            .replace('dd', day)
            .replace('mm', month)
            .replace('yyyy', year)
            .replace('HH', hours)
            .replace('MM', minutes);
    },

    /**
     * Débounce une fonction
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    /**
     * Copie du texte dans le presse-papiers
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification('Copié dans le presse-papiers', 'success', 2000);
        } catch (err) {
            console.error('Erreur lors de la copie:', err);
            this.showNotification('Erreur lors de la copie', 'error');
        }
    },

    /**
     * Valide un formulaire
     */
    validateForm(formElement) {
        const inputs = formElement.querySelectorAll('[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });
        
        return isValid;
    },

    /**
     * Affiche un loader sur un bouton
     */
    setButtonLoading(button, loading = true) {
        const originalText = button.dataset.originalText || button.innerHTML;
        
        if (loading) {
            button.dataset.originalText = originalText;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Chargement...';
            button.disabled = true;
        } else {
            button.innerHTML = originalText;
            button.disabled = false;
            delete button.dataset.originalText;
        }
    },

    /**
     * Gère l'état de chargement d'une page
     */
    showPageLoading(show = true) {
        let overlay = document.getElementById('page-loading-overlay');
        
        if (show && !overlay) {
            overlay = document.createElement('div');
            overlay.id = 'page-loading-overlay';
            overlay.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
            overlay.style.cssText = `
                background: rgba(255, 255, 255, 0.9);
                z-index: 9998;
                backdrop-filter: blur(3px);
            `;
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Chargement...</span>
                    </div>
                    <div class="mt-2">Chargement...</div>
                </div>
            `;
            document.body.appendChild(overlay);
        } else if (!show && overlay) {
            overlay.remove();
        }
    },

    /**
     * Sauvegarde locale des données
     */
    saveToLocalStorage(key, data) {
        try {
            localStorage.setItem(key, JSON.stringify(data));
            return true;
        } catch (error) {
            console.error('Erreur sauvegarde localStorage:', error);
            return false;
        }
    },

    /**
     * Récupération des données locales
     */
    getFromLocalStorage(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (error) {
            console.error('Erreur lecture localStorage:', error);
            return defaultValue;
        }
    },

    /**
     * Suppression des données locales
     */
    removeFromLocalStorage(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Erreur suppression localStorage:', error);
            return false;
        }
    }
};

/**
 * Gestionnaire de thème sombre/clair
 */
const ThemeManager = {
    init() {
        const savedTheme = AppUtils.getFromLocalStorage('app-theme', 'light');
        this.setTheme(savedTheme);
        this.setupToggleButtons();
    },

    setTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        AppUtils.saveToLocalStorage('app-theme', theme);
        
        // Mettre à jour l'icône des boutons de basculement
        const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
        toggleButtons.forEach(button => {
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        });
    },

    toggle() {
        const currentTheme = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        
        AppUtils.showNotification(
            `Thème ${newTheme === 'dark' ? 'sombre' : 'clair'} activé`, 
            'info', 
            2000
        );
    },

    setupToggleButtons() {
        const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
        toggleButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle();
            });
        });
    }
};

/**
 * Gestionnaire de recherche/filtrage
 */
const FilterManager = {
    /**
     * Filtre les éléments d'une liste
     */
    filterElements(query, elements, searchProperties) {
        const normalizedQuery = query.toLowerCase().trim();
        
        elements.forEach(element => {
            let match = false;
            
            if (!normalizedQuery) {
                match = true;
            } else {
                searchProperties.forEach(prop => {
                    const text = element.dataset[prop] || element.textContent || '';
                    if (text.toLowerCase().includes(normalizedQuery)) {
                        match = true;
                    }
                });
            }
            
            element.style.display = match ? '' : 'none';
        });
    },

    /**
     * Configure une recherche en temps réel
     */
    setupLiveSearch(inputSelector, containerSelector, itemSelector, searchProperties) {
        const input = document.querySelector(inputSelector);
        const container = document.querySelector(containerSelector);
        
        if (!input || !container) return;
        
        const debouncedFilter = AppUtils.debounce((query) => {
            const elements = container.querySelectorAll(itemSelector);
            this.filterElements(query, elements, searchProperties);
        }, 300);
        
        input.addEventListener('input', (e) => {
            debouncedFilter(e.target.value);
        });
    }
};

/**
 * Gestionnaire d'impression
 */
const PrintManager = {
    /**
     * Imprime une section spécifique
     */
    printSection(sectionSelector) {
        const section = document.querySelector(sectionSelector);
        if (!section) {
            AppUtils.showNotification('Section à imprimer non trouvée', 'error');
            return;
        }
        
        const printWindow = window.open('', '_blank');
        const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"], style'))
            .map(el => el.outerHTML)
            .join('');
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Impression</title>
                ${styles}
                <style>
                    @media print {
                        body { margin: 0; }
                        .no-print { display: none !important; }
                    }
                </style>
            </head>
            <body>
                ${section.innerHTML}
            </body>
            </html>
        `);
        
        printWindow.document.close();
        printWindow.focus();
        
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 250);
    },

    /**
     * Prépare la page pour l'impression
     */
    preparePage() {
        // Masquer les éléments non imprimables
        const noPrintElements = document.querySelectorAll('.no-print');
        noPrintElements.forEach(el => el.style.display = 'none');
        
        // Optimiser la mise en page
        document.body.classList.add('print-mode');
    },

    /**
     * Restaure la page après impression
     */
    restorePage() {
        const noPrintElements = document.querySelectorAll('.no-print');
        noPrintElements.forEach(el => el.style.display = '');
        
        document.body.classList.remove('print-mode');
    }
};

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser le gestionnaire de thème
    ThemeManager.init();
    
    // Auto-masquage des alertes
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            if (bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
    
    // Gestion des boutons de chargement
    const loadingButtons = document.querySelectorAll('[data-loading]');
    loadingButtons.forEach(button => {
        button.addEventListener('click', () => {
            AppUtils.setButtonLoading(button, true);
            
            // Simuler une action async ou attendre la soumission du formulaire
            if (button.type === 'submit') {
                const form = button.closest('form');
                if (form) {
                    form.addEventListener('submit', () => {
                        setTimeout(() => {
                            AppUtils.setButtonLoading(button, false);
                        }, 3000);
                    });
                }
            }
        });
    });
    
    // Gestion de l'impression
    window.addEventListener('beforeprint', PrintManager.preparePage);
    window.addEventListener('afterprint', PrintManager.restorePage);
});

// Export global
window.AppUtils = AppUtils;
window.ThemeManager = ThemeManager;
window.FilterManager = FilterManager;
window.PrintManager = PrintManager;