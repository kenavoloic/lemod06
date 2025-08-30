// static/js/auth.js - Fonctionnalités d'authentification

/**
 * Gestionnaire pour les pages d'authentification
 */
class AuthManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupLoginForm();
        this.setupPasswordChangeForm();
        this.setupProfilePage();
        this.setupPasswordStrengthIndicator();
    }
    
    /**
     * Configuration du formulaire de connexion
     */
    setupLoginForm() {
        const loginForm = document.getElementById('login-form') || 
                         document.querySelector('form[action*="login"]');
        
        if (!loginForm) return;
        
        // Toggle visibilité mot de passe
        const togglePasswordBtn = document.getElementById('togglePassword');
        const passwordField = loginForm.querySelector('input[type="password"]');
        
        if (togglePasswordBtn && passwordField) {
            togglePasswordBtn.addEventListener('click', () => {
                const type = passwordField.type === 'password' ? 'text' : 'password';
                passwordField.type = type;
                
                const icon = togglePasswordBtn.querySelector('i');
                icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
            });
        }
        
        // Auto-focus sur le champ username
        const usernameField = loginForm.querySelector('input[name="username"]');
        if (usernameField) {
            usernameField.focus();
        }
        
        // Validation en temps réel
        const fields = loginForm.querySelectorAll('input[required]');
        fields.forEach(field => {
            field.addEventListener('input', () => {
                this.validateField(field);
            });
            
            field.addEventListener('blur', () => {
                this.validateField(field);
            });
        });
        
        // Gestion de la soumission
        loginForm.addEventListener('submit', (e) => {
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                AppUtils.setButtonLoading(submitBtn, true);
                
                // Restaurer l'état du bouton en cas d'erreur
                setTimeout(() => {
                    AppUtils.setButtonLoading(submitBtn, false);
                }, 5000);
            }
        });
        
        // Remember me fonctionnalité (si disponible)
        const rememberMe = loginForm.querySelector('input[name="remember_me"]');
        if (rememberMe) {
            const savedUsername = localStorage.getItem('remembered_username');
            if (savedUsername && usernameField) {
                usernameField.value = savedUsername;
                rememberMe.checked = true;
            }
            
            loginForm.addEventListener('submit', () => {
                if (rememberMe.checked && usernameField) {
                    localStorage.setItem('remembered_username', usernameField.value);
                } else {
                    localStorage.removeItem('remembered_username');
                }
            });
        }
    }
    
    /**
     * Configuration du formulaire de changement de mot de passe
     */
    setupPasswordChangeForm() {
        const passwordForm = document.querySelector('form[action*="change-password"]') ||
                            document.querySelector('form').closest('.password-change-page');
        
        if (!passwordForm) return;
        
        const oldPasswordField = passwordForm.querySelector('input[name*="old_password"]');
        const newPassword1Field = passwordForm.querySelector('input[name*="new_password1"]');
        const newPassword2Field = passwordForm.querySelector('input[name*="new_password2"]');
        
        // Validation de l'ancien mot de passe
        if (oldPasswordField) {
            oldPasswordField.addEventListener('input', () => {
                this.validateField(oldPasswordField);
            });
        }
        
        // Validation du nouveau mot de passe
        if (newPassword1Field) {
            newPassword1Field.addEventListener('input', () => {
                this.validatePasswordStrength(newPassword1Field);
                if (newPassword2Field && newPassword2Field.value) {
                    this.validatePasswordMatch(newPassword1Field, newPassword2Field);
                }
            });
        }
        
        // Validation de la confirmation
        if (newPassword2Field) {
            newPassword2Field.addEventListener('input', () => {
                if (newPassword1Field) {
                    this.validatePasswordMatch(newPassword1Field, newPassword2Field);
                }
            });
        }
    }
    
    /**
     * Configuration de la page de profil
     */
    setupProfilePage() {
        const profilePage = document.querySelector('.profile-page') ||
                           document.querySelector('[class*="profile"]');
        
        if (!profilePage) return;
        
        // Animation d'apparition des sections
        const sections = profilePage.querySelectorAll('.profile-section');
        sections.forEach((section, index) => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                section.style.transition = 'all 0.6s ease';
                section.style.opacity = '1';
                section.style.transform = 'translateY(0)';
            }, index * 100);
        });
        
        // Copie d'informations
        const copyButtons = profilePage.querySelectorAll('[data-copy]');
        copyButtons.forEach(button => {
            button.addEventListener('click', () => {
                const textToCopy = button.dataset.copy || button.textContent;
                AppUtils.copyToClipboard(textToCopy);
            });
        });
        
        // Actions rapides du profil
        this.setupProfileActions();
    }
    
    /**
     * Actions rapides du profil
     */
    setupProfileActions() {
        // Bouton d'export des données
        const exportBtn = document.querySelector('[data-action="export-profile"]');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                this.exportProfileData();
            });
        }
        
        // Bouton de mise à jour du profil
        const updateBtn = document.querySelector('[data-action="update-profile"]');
        if (updateBtn) {
            updateBtn.addEventListener('click', () => {
                this.showUpdateProfileModal();
            });
        }
    }
    
    /**
     * Indicateur de force du mot de passe
     */
    setupPasswordStrengthIndicator() {
        const passwordFields = document.querySelectorAll('input[type="password"][name*="new_password1"]');
        
        passwordFields.forEach(field => {
            // Créer l'indicateur s'il n'existe pas
            let strengthIndicator = field.parentNode.querySelector('.password-strength');
            if (!strengthIndicator) {
                strengthIndicator = document.createElement('div');
                strengthIndicator.className = 'password-strength';
                strengthIndicator.innerHTML = `
                    <div class="password-strength-bar">
                        <div class="password-strength-fill"></div>
                    </div>
                    <small class="password-strength-text text-muted">Tapez votre mot de passe</small>
                `;
                field.parentNode.appendChild(strengthIndicator);
            }
            
            field.addEventListener('input', () => {
                this.updatePasswordStrengthIndicator(field, strengthIndicator);
            });
        });
    }
    
    /**
     * Met à jour l'indicateur de force du mot de passe
     */
    updatePasswordStrengthIndicator(field, indicator) {
        const password = field.value;
        const strength = this.calculatePasswordStrength(password);
        
        const bar = indicator.querySelector('.password-strength-bar');
        const text = indicator.querySelector('.password-strength-text');
        
        // Supprimer les anciennes classes
        bar.className = 'password-strength-bar';
        
        // Ajouter la nouvelle classe selon la force
        switch (strength.level) {
            case 'weak':
                bar.classList.add('password-strength-weak');
                text.textContent = 'Mot de passe faible';
                text.className = 'password-strength-text text-danger';
                break;
            case 'medium':
                bar.classList.add('password-strength-medium');
                text.textContent = 'Mot de passe moyen';
                text.className = 'password-strength-text text-warning';
                break;
            case 'good':
                bar.classList.add('password-strength-good');
                text.textContent = 'Bon mot de passe';
                text.className = 'password-strength-text text-info';
                break;
            case 'strong':
                bar.classList.add('password-strength-strong');
                text.textContent = 'Mot de passe fort';
                text.className = 'password-strength-text text-success';
                break;
            default:
                text.textContent = 'Tapez votre mot de passe';
                text.className = 'password-strength-text text-muted';
        }
        
        // Afficher les suggestions
        if (strength.suggestions.length > 0) {
            text.textContent += ' - ' + strength.suggestions.join(', ');
        }
    }
    
    /**
     * Calcule la force d'un mot de passe
     */
    calculatePasswordStrength(password) {
        if (!password) return { level: 'none', suggestions: [] };
        
        let score = 0;
        const suggestions = [];
        
        // Longueur
        if (password.length >= 8) score += 1;
        else suggestions.push('Au moins 8 caractères');
        
        if (password.length >= 12) score += 1;
        
        // Minuscules
        if (/[a-z]/.test(password)) score += 1;
        else suggestions.push('Lettres minuscules');
        
        // Majuscules
        if (/[A-Z]/.test(password)) score += 1;
        else suggestions.push('Lettres majuscules');
        
        // Chiffres
        if (/[0-9]/.test(password)) score += 1;
        else suggestions.push('Chiffres');
        
        // Caractères spéciaux
        if (/[^A-Za-z0-9]/.test(password)) score += 1;
        else suggestions.push('Caractères spéciaux');
        
        // Pas de répétitions
        if (!/(.)\1{2,}/.test(password)) score += 1;
        else suggestions.push('Éviter les répétitions');
        
        let level;
        if (score >= 6) level = 'strong';
        else if (score >= 4) level = 'good';
        else if (score >= 2) level = 'medium';
        else level = 'weak';
        
        return { level, suggestions };
    }
    
    /**
     * Valide un champ
     */
    validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        
        if (isRequired && !value) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            return false;
        }
        
        // Validations spécifiques par type
        let isValid = true;
        
        if (field.type === 'email') {
            isValid = this.isValidEmail(value);
        } else if (field.name && field.name.includes('password') && value.length > 0) {
            isValid = value.length >= 8;
        }
        
        if (isValid && value) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
        } else if (value || isRequired) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        }
        
        return isValid;
    }
    
    /**
     * Valide la force du mot de passe
     */
    validatePasswordStrength(field) {
        const strength = this.calculatePasswordStrength(field.value);
        const isValid = strength.level !== 'weak' && field.value.length >= 8;
        
        if (isValid) {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
        } else if (field.value) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
        }
        
        return isValid;
    }
    
    /**
     * Valide la correspondance des mots de passe
     */
    validatePasswordMatch(field1, field2) {
        const isMatch = field1.value === field2.value && field1.value.length > 0;
        
        if (isMatch) {
            field2.classList.add('is-valid');
            field2.classList.remove('is-invalid');
        } else if (field2.value) {
            field2.classList.add('is-invalid');
            field2.classList.remove('is-valid');
        }
        
        return isMatch;
    }
    
    /**
     * Valide un email
     */
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    /**
     * Exporte les données du profil
     */
    exportProfileData() {
        const profileData = {
            timestamp: new Date().toISOString(),
            user: {},
            groups: [],
            permissions: [],
            stats: {}
        };
        
        // Collecter les informations du profil
        const userInfo = document.querySelector('.profile-info');
        if (userInfo) {
            profileData.user.name = userInfo.querySelector('h2')?.textContent || '';
            profileData.user.email = userInfo.querySelector('.text-muted')?.textContent || '';
        }
        
        // Collecter les groupes
        const groupBadges = document.querySelectorAll('.profile-group-badge');
        groupBadges.forEach(badge => {
            profileData.groups.push(badge.textContent.trim());
        });
        
        // Collecter les statistiques
        const statsElements = document.querySelectorAll('.profile-stats');
        statsElements.forEach(stat => {
            const label = stat.querySelector('small')?.textContent || '';
            const value = stat.querySelector('h4')?.textContent || '';
            if (label && value) {
                profileData.stats[label] = value;
            }
        });
        
        // Télécharger le fichier
        const blob = new Blob([JSON.stringify(profileData, null, 2)], 
                             { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `profil-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        AppUtils.showNotification('Profil exporté avec succès', 'success');
    }
    
    /**
     * Affiche le modal de mise à jour du profil
     */
    showUpdateProfileModal() {
        // Cette fonction nécessiterait un modal Bootstrap
        // Pour l'instant, on redirige vers la page de profil
        AppUtils.showNotification('Fonctionnalité en développement', 'info');
    }
    
    /**
     * Gestion de l'auto-déconnexion
     */
    setupAutoLogout(timeoutMinutes = 30) {
        let timeoutId;
        let warningId;
        
        const resetTimer = () => {
            clearTimeout(timeoutId);
            clearTimeout(warningId);
            
            // Avertissement 5 minutes avant déconnexion
            warningId = setTimeout(() => {
                const remaining = 5;
                AppUtils.confirmAction(
                    `Votre session expirera dans ${remaining} minutes. Souhaitez-vous la prolonger ?`,
                    () => {
                        resetTimer(); // Prolonger la session
                    },
                    {
                        title: 'Session expirante',
                        confirmText: 'Prolonger',
                        cancelText: 'Me déconnecter',
                        type: 'warning'
                    }
                );
                
                // Auto-déconnexion après 5 minutes supplémentaires
                timeoutId = setTimeout(() => {
                    window.location.href = '/logout/';
                }, 5 * 60 * 1000);
                
            }, (timeoutMinutes - 5) * 60 * 1000);
        };
        
        // Événements qui réinitialisent le timer
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
        events.forEach(event => {
            document.addEventListener(event, resetTimer, { passive: true });
        });
        
        // Initialiser le timer
        resetTimer();
    }
}

/**
 * Utilitaires d'authentification
 */
const AuthUtils = {
    /**
     * Génère un mot de passe aléatoire
     */
    generatePassword(length = 12, includeSymbols = true) {
        const lowercase = 'abcdefghijklmnopqrstuvwxyz';
        const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
        const numbers = '0123456789';
        const symbols = includeSymbols ? '!@#$%^&*()_+-=[]{}|;:,.<>?' : '';
        
        const allChars = lowercase + uppercase + numbers + symbols;
        let password = '';
        
        // Garantir au moins un caractère de chaque type
        password += lowercase[Math.floor(Math.random() * lowercase.length)];
        password += uppercase[Math.floor(Math.random() * uppercase.length)];
        password += numbers[Math.floor(Math.random() * numbers.length)];
        if (includeSymbols) {
            password += symbols[Math.floor(Math.random() * symbols.length)];
        }
        
        // Compléter avec des caractères aléatoires
        for (let i = password.length; i < length; i++) {
            password += allChars[Math.floor(Math.random() * allChars.length)];
        }
        
        // Mélanger les caractères
        return password.split('').sort(() => Math.random() - 0.5).join('');
    },
    
    /**
     * Copie un mot de passe généré
     */
    async copyGeneratedPassword(length = 12, includeSymbols = true) {
        const password = this.generatePassword(length, includeSymbols);
        await AppUtils.copyToClipboard(password);
        AppUtils.showNotification(
            `Mot de passe généré et copié (${length} caractères)`, 
            'success'
        );
        return password;
    },
    
    /**
     * Vérifie si l'utilisateur est connecté
     */
    isAuthenticated() {
        return document.body.classList.contains('authenticated') ||
               document.querySelector('.navbar .dropdown-toggle') !== null ||
               document.querySelector('[href*="logout"]') !== null;
    },
    
    /**
     * Récupère les informations de l'utilisateur depuis la page
     */
    getCurrentUserInfo() {
        const userDropdown = document.querySelector('.navbar .dropdown-toggle');
        const profileInfo = document.querySelector('.profile-info');
        
        const info = {
            username: null,
            fullName: null,
            email: null,
            groups: []
        };
        
        if (userDropdown) {
            const text = userDropdown.textContent.trim();
            info.username = text.split(' ').pop(); // Dernier mot comme username
            info.fullName = text;
        }
        
        if (profileInfo) {
            info.fullName = profileInfo.querySelector('h2')?.textContent || info.fullName;
            info.email = profileInfo.querySelector('.text-muted')?.textContent || null;
        }
        
        // Collecter les groupes
        const groupBadges = document.querySelectorAll('.badge, .profile-group-badge');
        groupBadges.forEach(badge => {
            const groupName = badge.textContent.trim();
            if (groupName && !info.groups.includes(groupName)) {
                info.groups.push(groupName);
            }
        });
        
        return info;
    }
};

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
    
    // Activer l'auto-déconnexion seulement si connecté
    if (AuthUtils.isAuthenticated()) {
        // Auto-déconnexion après 30 minutes d'inactivité
        // authManager.setupAutoLogout(30);
    }
    
    // Bouton de génération de mot de passe
    const generatePasswordBtns = document.querySelectorAll('[data-generate-password]');
    generatePasswordBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const length = parseInt(btn.dataset.length) || 12;
            const includeSymbols = btn.dataset.symbols !== 'false';
            await AuthUtils.copyGeneratedPassword(length, includeSymbols);
        });
    });
});

// Export global
window.AuthManager = AuthManager;
window.AuthUtils = AuthUtils;