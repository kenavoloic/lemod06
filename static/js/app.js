// static/js/app.js - Point d'entrée centralisé pour l'application (Mode Clair Uniquement)

/**
 * Gestionnaire principal de l'application
 * Charge conditionnellement les modules selon le contexte de la page
 */
class AppManager {
    constructor() {
        this.modules = new Map();
        this.config = {
            autoHideAlerts: true,
            autoHideDelay: 5000,
            debugMode: false
        };
        
        this.init();
    }
    
    /**
     * Initialisation principale
     */
    init() {
        this.log('🚀 Initialisation de AppManager');
        
        // Configuration initiale
        this.setupGlobalEventListeners();
        this.setupAutoHideAlerts();
        
        // Chargement conditionnel des modules
        this.loadConditionalModules();
        
        // Finalisation
        this.setupGlobalShortcuts();
        this.markAsReady();
        
        this.log('✅ AppManager initialisé avec succès');
    }
    
    /**
     * Charge les modules selon le contexte de la page
     */
    loadConditionalModules() {
        const moduleMap = {
            'auth': {
                selectors: ['.login-body', '.profile-page', '.password-change-page'],
                module: () => window.AuthManager ? new window.AuthManager() : null
            },
            'dashboard': {
                selectors: ['.dashboard-container', '[class*="dashboard"]'],
                module: () => window.DashboardManager ? new window.DashboardManager() : null
            },
            'evaluation': {
                selectors: ['#evaluation-form', '.evaluation-container'],
                module: () => window.EvaluationValidator ? new window.EvaluationValidator() : null
            },
            'validation': {
                selectors: ['form[data-validate="true"]'],
                module: () => window.FormValidator ? new window.FormValidator() : null
            }
        };
        
        Object.entries(moduleMap).forEach(([name, config]) => {
            if (this.shouldLoadModule(config.selectors)) {
                this.loadModule(name, config.module);
            }
        });
    }
    
    /**
     * Vérifie si un module doit être chargé
     */
    shouldLoadModule(selectors) {
        return selectors.some(selector => document.querySelector(selector) !== null);
    }
    
    /**
     * Charge un module spécifique
     */
    loadModule(name, moduleFactory) {
        try {
            const moduleInstance = moduleFactory();
            if (moduleInstance) {
                this.modules.set(name, moduleInstance);
                this.log(`📦 Module ${name} chargé`);
            } else {
                this.log(`⚠️ Classe non disponible pour le module ${name}`);
            }
        } catch (error) {
            this.log(`❌ Erreur lors du chargement du module ${name}:`, error);
        }
    }
    
    /**
     * Configuration des événements globaux
     */
    setupGlobalEventListeners() {
        // Gestion des actions data-action
        document.addEventListener('click', (e) => {
            const action = e.target.closest('[data-action]')?.dataset.action;
            if (action) {
                e.preventDefault();
                this.handleGlobalAction(action, e.target);
            }
        });
        
        // Gestion des formulaires avec attribut data-loading
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.hasAttribute('data-loading')) {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    this.setButtonLoading(submitBtn, true);
                }
            }
        });
        
        // Gestion des erreurs JavaScript globales
        window.addEventListener('error', (e) => {
            this.handleGlobalError(e);
        });
        
        // Gestion des erreurs de promesses non capturées
        window.addEventListener('unhandledrejection', (e) => {
            this.handlePromiseRejection(e);
        });
    }
    
    /**
     * Gestion des actions globales via data-action
     */
    handleGlobalAction(action, element) {
        const actions = {
            'show-stats': () => this.showNotImplemented('Statistiques'),
            'show-preferences': () => this.showNotImplemented('Préférences'),
            'show-all-notifications': () => this.showNotImplemented('Notifications'),
            'list-conducteurs': () => this.showNotImplemented('Liste des conducteurs'),
            'add-conducteur': () => this.showNotImplemented('Nouveau conducteur'),
            'list-societes': () => this.showNotImplemented('Liste des sociétés'),
            'list-sites': () => this.showNotImplemented('Liste des sites'),
        };
        
        if (actions[action]) {
            actions[action]();
        } else {
            this.log(`⚠️ Action non définie: ${action}`);
        }
    }
    
    /**
     * Configuration de l'auto-masquage des alertes
     */
    setupAutoHideAlerts() {
        if (!this.config.autoHideAlerts) return;
        
        const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
        alerts.forEach(alert => {
            const delay = parseInt(alert.dataset.autoDismiss) || this.config.autoHideDelay;
            setTimeout(() => {
                if (alert.parentElement && window.bootstrap?.Alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, delay);
        });
    }
    
    /**
     * Configuration des raccourcis clavier globaux
     */
    setupGlobalShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Raccourcis avec Ctrl/Cmd
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        // Ctrl+R : Actualiser (laisser le comportement par défaut)
                        break;
                    case 'k':
                        e.preventDefault();
                        this.focusSearch();
                        break;
                    case '/':
                        e.preventDefault();
                        this.showShortcutsHelp();
                        break;
                }
            }
            
            // Raccourcis sans modificateur
            switch (e.key) {
                case 'Escape':
                    this.closeAllModals();
                    break;
            }
        });
    }
    
    /**
     * Affiche une notification
     */
    showNotification(message, type = 'info', duration = 5000) {
        // Utiliser la méthode d'AppUtils si disponible
        if (window.AppUtils?.showNotification) {
            window.AppUtils.showNotification(message, type, duration);
            return;
        }
        
        // Fallback simple
        const container = this.getOrCreateNotificationContainer();
        const notification = this.createNotificationElement(message, type);
        
        container.appendChild(notification);
        
        // Animation d'entrée
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });
        
        // Auto-suppression
        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);
    }
    
    /**
     * Crée ou récupère le conteneur de notifications
     */
    getOrCreateNotificationContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'messages-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    /**
     * Crée un élément de notification
     */
    createNotificationElement(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.style.transform = 'translateX(100%)';
        notification.style.opacity = '0';
        notification.style.transition = 'all 0.3s ease';
        
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-triangle',
            warning: 'fa-exclamation-circle',
            info: 'fa-info-circle'
        };
        
        notification.innerHTML = `
            <i class="fas ${icons[type] || icons.info} me-2"></i>
            <span class="message-content">${message}</span>
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
        `;
        
        return notification;
    }
    
    /**
     * Supprime une notification
     */
    removeNotification(notification) {
        if (notification && notification.parentElement) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }
    }
    
    /**
     * Met un bouton en état de chargement
     */
    setButtonLoading(button, loading = true) {
        if (!button) return;
        
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Chargement...';
            button.disabled = true;
            button.classList.add('btn-loading');
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
            button.disabled = false;
            button.classList.remove('btn-loading');
            delete button.dataset.originalText;
        }
    }
    
    /**
     * Focus sur le champ de recherche
     */
    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], .search-input, [placeholder*="recherche" i]');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }
    
    /**
     * Affiche l'aide des raccourcis
     */
    showShortcutsHelp() {
        const shortcuts = [
            { key: 'Ctrl+K', desc: 'Rechercher' },
            { key: 'Ctrl+/', desc: 'Afficher cette aide' },
            { key: 'Échap', desc: 'Fermer les modales' }
        ];
        
        const helpText = shortcuts
            .map(s => `<div class="d-flex justify-content-between"><kbd>${s.key}</kbd><span>${s.desc}</span></div>`)
            .join('');
        
        this.showNotification(
            `<div class="fw-bold mb-2">Raccourcis clavier :</div>${helpText}`,
            'info',
            8000
        );
    }
    
    /**
     * Ferme toutes les modales ouvertes
     */
    closeAllModals() {
        // Bootstrap modales
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const modalInstance = bootstrap.Modal.getInstance(modal);
            if (modalInstance) modalInstance.hide();
        });
        
        // Dropdowns
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(dropdown => {
            const toggle = dropdown.previousElementSibling;
            if (toggle) toggle.click();
        });
    }
    
    /**
     * Gestion des erreurs globales
     */
    handleGlobalError(event) {
        if (this.config.debugMode) {
            console.error('🚨 Erreur JavaScript:', event.error);
        }
        
        // En production, on pourrait envoyer l'erreur à un service de monitoring
        if (typeof window.gtag === 'function') {
            gtag('event', 'exception', {
                description: event.error?.message || 'Unknown error',
                fatal: false
            });
        }
    }
    
    /**
     * Gestion des promesses rejetées
     */
    handlePromiseRejection(event) {
        if (this.config.debugMode) {
            console.error('🚨 Promesse rejetée:', event.reason);
        }
        
        // Empêcher l'affichage de l'erreur dans la console en production
        if (!this.config.debugMode) {
            event.preventDefault();
        }
    }
    
    /**
     * Affiche un message pour les fonctionnalités non implémentées
     */
    showNotImplemented(feature) {
        this.showNotification(
            `La fonctionnalité "${feature}" sera bientôt disponible`,
            'info',
            3000
        );
    }
    
    /**
     * Marque l'application comme prête
     */
    markAsReady() {
        document.body.classList.add('app-ready');
        document.dispatchEvent(new CustomEvent('appReady', {
            detail: { modules: Array.from(this.modules.keys()) }
        }));
    }
    
    /**
     * Logging conditionnel
     */
    log(...args) {
        if (this.config.debugMode || window.location.hostname === 'localhost') {
            console.log('%c[AppManager]', 'color: #0d6efd; font-weight: bold;', ...args);
        }
    }
    
    /**
     * Récupère un module chargé
     */
    getModule(name) {
        return this.modules.get(name);
    }
    
    /**
     * Active/désactive le mode debug
     */
    setDebugMode(enabled) {
        this.config.debugMode = enabled;
        document.body.classList.toggle('debug-mode', enabled);
        this.log(`Mode debug ${enabled ? 'activé' : 'désactivé'}`);
    }
}

/**
 * Utilitaires globaux simplifiés
 * (En complément des utilitaires existants dans utils.js)
 */
class AppHelpers {
    /**
     * Debounce une fonction
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    /**
     * Throttle une fonction
     */
    static throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    /**
     * Attend qu'un élément soit disponible dans le DOM
     */
    static waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }
            
            const observer = new MutationObserver(() => {
                const element = document.querySelector(selector);
                if (element) {
                    observer.disconnect();
                    resolve(element);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Élément ${selector} non trouvé après ${timeout}ms`));
            }, timeout);
        });
    }
    
    /**
     * Copie du texte dans le presse-papiers
     */
    static async copyToClipboard(text) {
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                return true;
            } else {
                // Fallback pour les navigateurs plus anciens
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.opacity = '0';
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return true;
            }
        } catch (error) {
            console.error('Erreur lors de la copie:', error);
            return false;
        }
    }
    
    /**
     * Formate une date en français
     */
    static formatDate(date, format = 'dd/mm/yyyy') {
        const d = new Date(date);
        if (isNaN(d.getTime())) return 'Date invalide';
        
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
    }
    
    /**
     * Valide un email
     */
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    /**
     * Génère un ID unique
     */
    static generateId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
}

/**
 * Gestionnaire de notifications et utilitaires globaux
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

/**
 * Extensions pour améliorer l'expérience développeur
 */
class DevExtensions {
    static init() {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Commandes de console pour le développement
            window.app_debug = {
                modules: () => Array.from(window.app.modules.keys()),
                notification: (msg, type = 'info') => window.app.showNotification(msg, type),
                reload_css: () => DevExtensions.reloadCSS(),
                toggle_debug: () => window.app.setDebugMode(!window.app.config.debugMode),
                outline_all: () => document.body.classList.toggle('debug-outline'),
                grid_overlay: () => document.body.classList.toggle('debug-grid')
            };
            
            console.log('🛠️ Outils de développement disponibles dans window.app_debug');
        }
    }
    
    static reloadCSS() {
        const links = document.querySelectorAll('link[rel="stylesheet"]');
        links.forEach(link => {
            const href = link.href;
            link.href = href + (href.includes('?') ? '&' : '?') + 'v=' + Date.now();
        });
        console.log('🎨 CSS rechargé');
    }
}

/**
 * Initialisation automatique
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialiser l'application
    window.app = new AppManager();
    window.AppHelpers = AppHelpers;
    
    // Initialiser les extensions de développement
    DevExtensions.init();
    
    // Événement personnalisé pour signaler que l'app est prête
    document.addEventListener('appReady', (e) => {
        console.log('🎉 Application prête avec les modules:', e.detail.modules);
    });
    
    // Auto-masquage des alertes après 5 secondes
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            if (bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        });
    }, 5000);
    
    // Footer dynamique
    const currentTimeElement = document.getElementById('current-time');
    if (currentTimeElement) {
        const updateTime = () => {
            currentTimeElement.textContent = new Date().toLocaleTimeString('fr-FR');
        };
        updateTime();
        setInterval(updateTime, 1000);
    }
    
    // Gestion de l'icône du footer toggle
    const footerToggle = document.querySelector('[data-bs-target="#footer-details"]');
    const footerToggleIcon = document.getElementById('footer-toggle-icon');
    if (footerToggle && footerToggleIcon) {
        footerToggle.addEventListener('click', () => {
            setTimeout(() => {
                const isExpanded = document.getElementById('footer-details').classList.contains('show');
                footerToggleIcon.className = isExpanded ? 'fas fa-chevron-down' : 'fas fa-chevron-up';
            }, 150);
        });
    }
    
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

// Gestion des événements de performance
window.addEventListener('load', () => {
    if (window.app?.config.debugMode) {
        console.log('⚡ Page chargée en', performance.now().toFixed(2), 'ms');
    }
});

// Export global
window.AppUtils = AppUtils;
window.FilterManager = FilterManager;
window.PrintManager = PrintManager;

// Export pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AppManager, AppHelpers, DevExtensions, AppUtils, FilterManager, PrintManager };
}
