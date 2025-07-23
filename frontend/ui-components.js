/**
 * UI Components and Utilities
 * Handles UI interactions, modals, notifications, and component rendering
 */

// Toast notification system
class ToastManager {
    constructor() {
        this.container = document.getElementById('toastContainer');
        this.toasts = [];
    }
    
    show(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        this.toasts.push(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            this.remove(toast);
        }, duration);
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getIcon(type);
        toast.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="toastManager.remove(this.parentElement)">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        return toast;
    }
    
    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }
    
    remove(toast) {
        if (toast && toast.parentElement) {
            toast.style.animation = 'toastSlideOut 0.3s ease-in forwards';
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.parentElement.removeChild(toast);
                }
                this.toasts = this.toasts.filter(t => t !== toast);
            }, 300);
        }
    }
    
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
    
    clear() {
        this.toasts.forEach(toast => this.remove(toast));
    }
}

// Loading overlay manager
class LoadingManager {
    constructor() {
        this.overlay = document.getElementById('loadingOverlay');
        this.isVisible = false;
    }
    
    show(message = 'Processing...') {
        const messageElement = this.overlay.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        this.overlay.classList.remove('hidden');
        this.isVisible = true;
    }
    
    hide() {
        this.overlay.classList.add('hidden');
        this.isVisible = false;
    }
    
    toggle(show, message) {
        if (show) {
            this.show(message);
        } else {
            this.hide();
        }
    }
}

// Modal manager
class ModalManager {
    constructor() {
        this.activeModal = null;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.close();
            }
        });
        
        // Close modal with escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.close();
            }
        });
        
        // Close button handlers
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-close') || 
                e.target.closest('.modal-close') ||
                e.target.dataset.action === 'close-modal') {
                this.close();
            }
        });
    }
    
    open(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            this.activeModal = modal;
            document.body.style.overflow = 'hidden';
        }
    }
    
    close() {
        if (this.activeModal) {
            this.activeModal.classList.remove('active');
            this.activeModal = null;
            document.body.style.overflow = '';
        }
    }
    
    isOpen() {
        return this.activeModal !== null;
    }
}

// Plan card component
class PlanCard {
    static create(plan) {
        const formattedPlan = DataTransformer.formatPlan(plan);
        
        return `
            <div class="plan-card" data-plan-id="${plan.plan_id}">
                <div class="plan-header">
                    <div class="plan-title">${plan.description || 'Subscription Plan'}</div>
                    <div class="plan-amount">${formattedPlan.amount_formatted}</div>
                    <div class="plan-interval">per ${formattedPlan.interval_formatted}</div>
                </div>
                <div class="plan-body">
                    <div class="plan-details">
                        <div class="plan-detail">
                            <strong>Duration:</strong>
                            <span>${formattedPlan.duration_formatted}</span>
                        </div>
                        <div class="plan-detail">
                            <strong>Token:</strong>
                            <span>${plan.token === 'native' ? 'Native' : 'ERC-20'}</span>
                        </div>
                        <div class="plan-detail">
                            <strong>Creator:</strong>
                            <span>${formattedPlan.creator_formatted}</span>
                        </div>
                        <div class="plan-detail">
                            <strong>Status:</strong>
                            <span class="text-${plan.active ? 'success' : 'error'}">
                                ${plan.active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                    </div>
                    <div class="plan-actions">
                        <button class="btn btn-primary" onclick="planManager.subscribe('${plan.plan_id}')">
                            <i class="fas fa-credit-card"></i>
                            Subscribe
                        </button>
                        <button class="btn btn-secondary" onclick="planManager.viewDetails('${plan.plan_id}')">
                            <i class="fas fa-eye"></i>
                            Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
}

// Subscription card component
class SubscriptionCard {
    static create(subscription) {
        const formatted = DataTransformer.formatSubscription(subscription);
        const statusClass = formatted.is_expired ? 'expired' : 
                           !subscription.active ? 'cancelled' : 'active';
        
        return `
            <div class="subscription-card" data-subscription-id="${subscription.subscription_id}">
                <div class="subscription-header">
                    <div class="subscription-status ${statusClass}">
                        <i class="fas fa-circle"></i>
                        ${statusClass.charAt(0).toUpperCase() + statusClass.slice(1)}
                    </div>
                    <div class="subscription-amount">${formatted.total_paid_formatted}</div>
                </div>
                <div class="subscription-body">
                    <div class="subscription-details">
                        <div class="subscription-detail">
                            <strong>Plan ID:</strong>
                            <span>${DataTransformer.formatAddress(subscription.plan_id)}</span>
                        </div>
                        <div class="subscription-detail">
                            <strong>Start Date:</strong>
                            <span>${DataTransformer.formatDate(subscription.start_time)}</span>
                        </div>
                        <div class="subscription-detail">
                            <strong>End Date:</strong>
                            <span>${DataTransformer.formatDate(subscription.end_time)}</span>
                        </div>
                        ${subscription.active && !formatted.is_expired ? `
                        <div class="subscription-detail">
                            <strong>Next Payment:</strong>
                            <span class="${formatted.is_payment_overdue ? 'text-error' : 'text-success'}">
                                ${DataTransformer.formatDate(subscription.next_payment_due)}
                            </span>
                        </div>
                        ` : ''}
                        <div class="subscription-detail">
                            <strong>Days Remaining:</strong>
                            <span>${formatted.days_remaining}</span>
                        </div>
                    </div>
                    <div class="subscription-actions">
                        ${subscription.active && !formatted.is_expired ? `
                        <button class="btn btn-warning" onclick="subscriptionManager.cancel('${subscription.plan_id}')">
                            <i class="fas fa-times"></i>
                            Cancel
                        </button>
                        ` : ''}
                        <button class="btn btn-secondary" onclick="subscriptionManager.viewDetails('${subscription.subscription_id}')">
                            <i class="fas fa-eye"></i>
                            Details
                        </button>
                        ${formatted.is_payment_overdue ? `
                        <button class="btn btn-primary" onclick="subscriptionManager.payNow('${subscription.plan_id}')">
                            <i class="fas fa-credit-card"></i>
                            Pay Now
                        </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
}

// Activity item component
class ActivityItem {
    static create(activity) {
        const icons = {
            plan_created: 'fas fa-plus-circle text-success',
            subscription_created: 'fas fa-credit-card text-primary',
            payment_processed: 'fas fa-coins text-warning',
            subscription_cancelled: 'fas fa-times-circle text-error'
        };
        
        return `
            <div class="activity-item">
                <i class="${icons[activity.type] || 'fas fa-info-circle'}"></i>
                <div class="activity-content">
                    <div class="activity-message">${activity.message}</div>
                    <div class="activity-time">${DataTransformer.formatDate(activity.timestamp)}</div>
                </div>
            </div>
        `;
    }
}

// Form validation utilities
class FormValidator {
    static validatePlanForm(formData) {
        const errors = [];
        
        if (!formData.token) {
            errors.push('Token type is required');
        }
        
        if (formData.token === 'custom' && !formData.customTokenAddress) {
            errors.push('Custom token address is required');
        }
        
        if (formData.token === 'custom' && !web3Integration.isValidAddress(formData.customTokenAddress)) {
            errors.push('Invalid token address format');
        }
        
        if (!formData.amount || parseFloat(formData.amount) <= 0) {
            errors.push('Amount must be greater than 0');
        }
        
        if (!formData.interval_days || parseInt(formData.interval_days) < 1) {
            errors.push('Interval must be at least 1 day');
        }
        
        if (!formData.duration_days || parseInt(formData.duration_days) < 1) {
            errors.push('Duration must be at least 1 day');
        }
        
        if (!formData.api_url) {
            errors.push('API URL is required');
        }
        
        try {
            new URL(formData.api_url);
        } catch {
            errors.push('Invalid API URL format');
        }
        
        return errors;
    }
    
    static showErrors(errors, containerId = 'errorContainer') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        if (errors.length === 0) {
            container.innerHTML = '';
            container.style.display = 'none';
            return;
        }
        
        container.innerHTML = `
            <div class="error-list">
                ${errors.map(error => `<div class="error-item"><i class="fas fa-exclamation-circle"></i> ${error}</div>`).join('')}
            </div>
        `;
        container.style.display = 'block';
    }
}

// Chart utilities
class ChartManager {
    constructor() {
        this.charts = {};
    }
    
    createRevenueChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Revenue',
                    data: data.values,
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                }
            }
        });
    }
    
    createStatusChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: [
                        'rgb(16, 185, 129)',
                        'rgb(239, 68, 68)',
                        'rgb(100, 116, 139)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    updateChart(canvasId, newData) {
        const chart = this.charts[canvasId];
        if (chart) {
            chart.data = newData;
            chart.update();
        }
    }
    
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    }
    
    destroyAll() {
        Object.keys(this.charts).forEach(canvasId => {
            this.destroyChart(canvasId);
        });
    }
}

// Navigation manager
class NavigationManager {
    constructor() {
        this.currentSection = 'dashboard';
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        document.addEventListener('click', (e) => {
            const navLink = e.target.closest('.nav-link');
            if (navLink) {
                e.preventDefault();
                const section = navLink.dataset.section;
                if (section) {
                    this.navigateTo(section);
                }
            }
            
            const actionBtn = e.target.closest('.action-btn');
            if (actionBtn) {
                const action = actionBtn.dataset.action;
                this.handleQuickAction(action);
            }
        });
    }
    
    navigateTo(section) {
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');
        
        // Update active section
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(section).classList.add('active');
        
        this.currentSection = section;
        
        // Load section data
        this.loadSectionData(section);
    }
    
    loadSectionData(section) {
        switch (section) {
            case 'dashboard':
                dashboardManager.loadData();
                break;
            case 'plans':
                planManager.loadPlans();
                break;
            case 'subscriptions':
                subscriptionManager.loadSubscriptions();
                break;
            case 'analytics':
                analyticsManager.loadAnalytics();
                break;
        }
    }
    
    handleQuickAction(action) {
        switch (action) {
            case 'create-plan':
                this.navigateTo('plans');
                setTimeout(() => modalManager.open('createPlanModal'), 100);
                break;
            case 'view-subscriptions':
                this.navigateTo('subscriptions');
                break;
            case 'analytics':
                this.navigateTo('analytics');
                break;
        }
    }
}

// Initialize global instances
const toastManager = new ToastManager();
const loadingManager = new LoadingManager();
const modalManager = new ModalManager();
const chartManager = new ChartManager();
const navigationManager = new NavigationManager();

// Export for use in other modules
window.toastManager = toastManager;
window.loadingManager = loadingManager;
window.modalManager = modalManager;
window.chartManager = chartManager;
window.navigationManager = navigationManager;
window.PlanCard = PlanCard;
window.SubscriptionCard = SubscriptionCard;
window.ActivityItem = ActivityItem;
window.FormValidator = FormValidator;

