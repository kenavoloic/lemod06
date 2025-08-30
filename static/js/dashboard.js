// static/js/dashboard.js - Fonctionnalités pour les tableaux de bord

class DashboardManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupStatsCards();
        this.setupQuickActions();
        this.setupRecentActivities();
        this.loadDashboardData();
    }
    
    setupStatsCards() {
        const statsCards = document.querySelectorAll('.stats-card');
        
        // Animation d'apparition en cascade
        statsCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.6s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
        
        // Animation hover améliorée
        statsCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-8px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });
    }
    
    setupQuickActions() {
        const actionButtons = document.querySelectorAll('.quick-actions .btn');
        
        actionButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Effet de clic
                button.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    button.style.transform = '';
                }, 150);
                
                // Analytics (si nécessaire)
                this.trackAction(button.textContent.trim());
            });
        });
    }
    
    setupRecentActivities() {
        const activities = document.querySelectorAll('.activity-item');
        
        // Auto-refresh des activités récentes
        if (activities.length > 0) {
            setInterval(() => {
                this.refreshRecentActivities();
            }, 30000); // Toutes les 30 secondes
        }
    }
    
    async loadDashboardData() {
        try {
            // Chargement des statistiques dynamiques si disponible
            const statsEndpoint = document.querySelector('[data-stats-url]');
            if (statsEndpoint) {
                const response = await fetch(statsEndpoint.dataset.statsUrl);
                const data = await response.json();
                this.updateStats(data);
            }
        } catch (error) {
            console.error('Erreur lors du chargement des données:', error);
        }
    }
    
    updateStats(data) {
        // Mettre à jour les cartes de statistiques
        Object.entries(data).forEach(([key, value]) => {
            const statElement = document.querySelector(`[data-stat="${key}"]`);
            if (statElement) {
                this.animateNumber(statElement, parseInt(value) || 0);
            }
        });
    }
    
    animateNumber(element, targetValue) {
        const startValue = parseInt(element.textContent) || 0;
        const duration = 1000;
        const step = (targetValue - startValue) / (duration / 16);
        let currentValue = startValue;
        
        const animate = () => {
            currentValue += step;
            
            if ((step > 0 && currentValue >= targetValue) || 
                (step < 0 && currentValue <= targetValue)) {
                element.textContent = targetValue;
            } else {
                element.textContent = Math.round(currentValue);
                requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    async refreshRecentActivities() {
        const activitiesContainer = document.querySelector('.recent-activities tbody');
        if (!activitiesContainer) return;
        
        try {
            const response = await fetch('/api/recent-activities/');
            const activities = await response.json();
            
            // Mettre à jour le contenu
            activitiesContainer.innerHTML = activities.map(activity => `
                <tr>
                    <td>${AppUtils.formatDate(activity.date)}</td>
                    <td>${activity.description}</td>
                    <td><span class="badge bg-${activity.type}">${activity.status}</span></td>
                </tr>
            `).join('');
            
        } catch (error) {
            console.error('Erreur refresh activités:', error);
        }
    }
    
    trackAction(actionName) {
        // Envoyer les analytics si nécessaire
        console.log('Action dashboard:', actionName);
        
        // Exemple d'envoi vers un service d'analytics
        if (window.gtag) {
            gtag('event', 'dashboard_action', {
                'action_name': actionName,
                'page_title': document.title
            });
        }
    }
    
    exportDashboardData() {
        const data = {
            timestamp: new Date().toISOString(),
            stats: {},
            activities: []
        };
        
        // Collecter les stats
        document.querySelectorAll('[data-stat]').forEach(el => {
            data.stats[el.dataset.stat] = el.textContent;
        });
        
        // Collecter les activités
        document.querySelectorAll('.activity-item').forEach(item => {
            const title = item.querySelector('.activity-title')?.textContent;
            const time = item.querySelector('.activity-time')?.textContent;
            if (title && time) {
                data.activities.push({ title, time });
            }
        });
        
        // Télécharger en JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], 
                             { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `dashboard-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Utilitaires spécifiques au dashboard
const DashboardUtils = {
    /**
     * Crée un graphique simple avec Chart.js (si disponible)
     */
    createChart(canvasId, config) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !window.Chart) return null;
        
        return new Chart(canvas, config);
    },
    
    /**
     * Configure un widget de statistiques en temps réel
     */
    setupLiveStats(selector, endpoint, interval = 30000) {
        const element = document.querySelector(selector);
        if (!element) return;
        
        const updateStats = async () => {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                
                Object.entries(data).forEach(([key, value]) => {
                    const statEl = element.querySelector(`[data-live-stat="${key}"]`);
                    if (statEl) {
                        statEl.textContent = value;
                        statEl.classList.add('updated');
                        setTimeout(() => statEl.classList.remove('updated'), 1000);
                    }
                });
            } catch (error) {
                console.error('Erreur mise à jour stats:', error);
            }
        };
        
        // Première mise à jour
        updateStats();
        
        // Mise à jour périodique
        return setInterval(updateStats, interval);
    }
};

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.dashboard-container') || 
        document.body.classList.contains('dashboard')) {
        window.dashboardManager = new DashboardManager();
    }
    
    // Raccourcis clavier pour le dashboard
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case 'r':
                    e.preventDefault();
                    location.reload();
                    break;
                case 'e':
                    if (window.dashboardManager) {
                        e.preventDefault();
                        window.dashboardManager.exportDashboardData();
                    }
                    break;
            }
        }
    });
});

// Export
window.DashboardManager = DashboardManager;
window.DashboardUtils = DashboardUtils;
