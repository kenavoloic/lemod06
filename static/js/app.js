// static/js/app.js - Point d'entrée centralisé pour l'application

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
            debugMode: false,
            theme: this.getStoredTheme()
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
        this.setupTheme();
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
            'toggle-theme': () => this.toggleTheme(),
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
     * Configuration du système de thème
     */
    setupTheme() {
        const theme = this.config.theme || 'light';
        this.applyTheme(theme);
        
        // Bouton de basculement du thème
        const themeToggle = document.querySelector('[data-theme-toggle]');
        if (themeToggle) {
            themeToggle.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleTheme();
            });
        }
    }
    
    /**
     * Applique un thème
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-bs-theme', theme);
        this.config.theme = theme;
        this.storeTheme(theme);
        
        // Mettre à jour l'icône du bouton de thème
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        this.log(`🎨 Thème appliqué: ${theme}`);
    }
    
    /**
     * Bascule entre thème clair et sombre
     */
    toggleTheme() {
        const currentTheme = this.config.theme;
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
        
        this.showNotification(
            `Thème ${newTheme === 'dark' ? 'sombre' : 'clair'} activé`,
            'info',
            2000
        );
    }
    
    /**
     * Récupère le thème stocké
     */
    getStoredTheme() {
        try {
            return localStorage.getItem('app-theme') || 'light';
        } catch {
            return 'light';
        }
    }
    
    /**
     * Stocke le thème
     */
    storeTheme(theme) {
        try {
            localStorage.setItem('app-theme', theme);
        } catch (error) {
            this.log('Impossible de stocker le thème:', error);
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
                    case 'd':
                        e.preventDefault();
                        this.toggleTheme();
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
            { key: 'Ctrl+D', desc: 'Basculer le thème' },
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
 * Extensions pour améliorer l'expérience développeur
 */
class DevExtensions {
    static init() {
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            // Commandes de console pour le développement
            window.app_debug = {
                modules: () => Array.from(window.app.modules.keys()),
                theme: (theme) => window.app.applyTheme(theme),
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
});

// Gestion des événements de performance
window.addEventListener('load', () => {
    if (window.app?.config.debugMode) {
        console.log('⚡ Page chargée en', performance.now().toFixed(2), 'ms');
    }
});

// Export pour utilisation dans d'autres scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AppManager, AppHelpers, DevExtensions };
}
