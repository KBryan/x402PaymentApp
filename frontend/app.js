/**
 * Main Application Logic
 * Coordinates all components and handles application state
 */

class SKALEPaymentApp {
    constructor() {
        this.web3 = new Web3Integration();
        this.api = new EnhancedAPIClient();
        this.paymentSigner = new PaymentSigner(this.web3);
        
        this.isInitialized = false;
        this.currentUser = null;
        this.userPlans = [];
        this.userSubscriptions = [];
        this.activityLog = [];
        
        this.init();
    }
    
    async init() {
        try {
            // Setup Web3 event listeners
            this.setupWeb3Listeners();
            
            // Setup UI event listeners
            this.setupUIListeners();
            
            // Check API health
            await this.checkAPIHealth();
            
            // Load initial data
            await this.loadInitialData();
            
            this.isInitialized = true;
            console.log('SKALE Payment App initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize app:', error);
            toastManager.error('Failed to initialize application');
        }
    }
    
    setupWeb3Listeners() {
        this.web3.onWalletConnect((account) => {
            this.handleWalletConnected(account);
        });
        
        this.web3.onWalletDisconnect(() => {
            this.handleWalletDisconnected();
        });
        
        this.web3.onAccountChanged((account) => {
            this.handleAccountChanged(account);
        });
        
        this.web3.onChainChanged((chainId) => {
            this.handleChainChanged(chainId);
        });
    }
    
    setupUIListeners() {
        // Wallet connection
        document.getElementById('connectWallet').addEventListener('click', () => {
            this.connectWallet();
        });
        
        document.getElementById('disconnectWallet').addEventListener('click', () => {
            this.disconnectWallet();
        });
        
        // Plan creation
        document.getElementById('createPlanBtn').addEventListener('click', () => {
            modalManager.open('createPlanModal');
        });
        
        document.getElementById('createPlanForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCreatePlan();
        });
        
        // Token type change
        document.getElementById('planToken').addEventListener('change', (e) => {
            const customTokenGroup = document.getElementById('customTokenGroup');
            if (e.target.value === 'custom') {
                customTokenGroup.style.display = 'block';
            } else {
                customTokenGroup.style.display = 'none';
            }
        });
        
        // Subscription confirmation
        document.getElementById('confirmSubscription').addEventListener('click', () => {
            this.handleConfirmSubscription();
        });
    }
    
    async checkAPIHealth() {
        try {
            const health = await this.api.healthCheck();
            console.log('API Health:', health);
            return true;
        } catch (error) {
            console.error('API health check failed:', error);
            toastManager.error('Backend API is not available');
            return false;
        }
    }
    
    async loadInitialData() {
        try {
            // Load public plans
            await planManager.loadPlans();
            
            // If wallet is connected, load user data
            if (this.web3.isWalletConnected()) {
                await this.loadUserData();
            }
            
            // Update dashboard
            await dashboardManager.updateStats();
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
        }
    }
    
    async loadUserData() {
        if (!this.currentUser) return;
        
        try {
            // Load user subscriptions
            const subscriptions = await this.api.getUserSubscriptions(this.currentUser);
            this.userSubscriptions = subscriptions;
            
            // Load user payment history
            const payments = await this.api.getPaymentHistory(this.currentUser);
            
            // Update activity log
            this.updateActivityLog(subscriptions, payments.payments);
            
        } catch (error) {
            console.error('Failed to load user data:', error);
        }
    }
    
    updateActivityLog(subscriptions, payments) {
        const activities = [];
        
        // Add subscription activities
        subscriptions.forEach(sub => {
            activities.push({
                type: 'subscription_created',
                message: `Subscribed to plan ${DataTransformer.formatAddress(sub.plan_id)}`,
                timestamp: sub.start_time
            });
        });
        
        // Add payment activities
        payments.forEach(payment => {
            activities.push({
                type: 'payment_processed',
                message: `Payment of ${payment.amount} ETH processed`,
                timestamp: payment.timestamp
            });
        });
        
        // Sort by timestamp (newest first)
        activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        this.activityLog = activities.slice(0, 10); // Keep last 10 activities
        
        // Update UI
        this.renderActivityLog();
    }
    
    renderActivityLog() {
        const container = document.getElementById('recentActivity');
        if (!container) return;
        
        if (this.activityLog.length === 0) {
            container.innerHTML = `
                <div class="activity-item">
                    <i class="fas fa-info-circle"></i>
                    <span>No recent activity</span>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.activityLog
            .map(activity => ActivityItem.create(activity))
            .join('');
    }
    
    async connectWallet() {
        try {
            loadingManager.show('Connecting wallet...');
            
            const result = await this.web3.connectWallet();
            
            if (result.success) {
                toastManager.success('Wallet connected successfully');
            }
            
        } catch (error) {
            console.error('Wallet connection failed:', error);
            toastManager.error(error.message || 'Failed to connect wallet');
        } finally {
            loadingManager.hide();
        }
    }
    
    async disconnectWallet() {
        try {
            await this.web3.disconnectWallet();
            toastManager.info('Wallet disconnected');
        } catch (error) {
            console.error('Wallet disconnection failed:', error);
        }
    }
    
    handleWalletConnected(account) {
        this.currentUser = account;
        
        // Update UI
        document.getElementById('connectWallet').classList.add('hidden');
        document.getElementById('walletInfo').classList.remove('hidden');
        document.querySelector('.wallet-address').textContent = this.web3.formatAddress(account);
        
        // Load user data
        this.loadUserData();
        
        // Update dashboard
        dashboardManager.updateStats();
    }
    
    handleWalletDisconnected() {
        this.currentUser = null;
        this.userSubscriptions = [];
        this.activityLog = [];
        
        // Update UI
        document.getElementById('connectWallet').classList.remove('hidden');
        document.getElementById('walletInfo').classList.add('hidden');
        
        // Clear user-specific data
        this.renderActivityLog();
        dashboardManager.updateStats();
    }
    
    handleAccountChanged(account) {
        this.currentUser = account;
        document.querySelector('.wallet-address').textContent = this.web3.formatAddress(account);
        
        // Reload user data
        this.loadUserData();
        dashboardManager.updateStats();
    }
    
    handleChainChanged(chainId) {
        console.log('Chain changed to:', chainId);
        toastManager.info('Network changed. Please refresh if needed.');
    }
    
    async handleCreatePlan() {
        if (!this.web3.isWalletConnected()) {
            toastManager.error('Please connect your wallet first');
            return;
        }
        
        try {
            loadingManager.show('Creating plan...');
            
            // Get form data
            const formData = this.getCreatePlanFormData();
            
            // Validate form
            const errors = FormValidator.validatePlanForm(formData);
            if (errors.length > 0) {
                FormValidator.showErrors(errors);
                loadingManager.hide();
                return;
            }
            
            // Create payment signature
            const timestamp = new Date().toISOString();
            const signatureData = await this.paymentSigner.createPaymentSignature(
                'create_plan',
                0.01, // Small fee for plan creation
                'native',
                timestamp
            );
            
            const paymentHeader = this.paymentSigner.createPaymentHeader({
                amount: 0.01,
                token: 'native',
                signature: signatureData.signature,
                timestamp: timestamp,
                from_address: this.currentUser
            });
            
            // Create plan via API
            const plan = await this.api.createPlan(formData, paymentHeader);
            
            toastManager.success('Plan created successfully!');
            modalManager.close();
            
            // Reload plans
            await planManager.loadPlans();
            
            // Clear form
            document.getElementById('createPlanForm').reset();
            
        } catch (error) {
            console.error('Plan creation failed:', error);
            toastManager.error(error.message || 'Failed to create plan');
        } finally {
            loadingManager.hide();
        }
    }
    
    getCreatePlanFormData() {
        const form = document.getElementById('createPlanForm');
        const formData = new FormData(form);
        
        const token = formData.get('planToken') || document.getElementById('planToken').value;
        const customTokenAddress = document.getElementById('customTokenAddress').value;
        
        return {
            token: token === 'custom' ? customTokenAddress : 'native',
            amount: parseFloat(document.getElementById('planAmount').value),
            interval_days: parseInt(document.getElementById('planInterval').value),
            duration_days: parseInt(document.getElementById('planDuration').value),
            api_url: document.getElementById('planApiUrl').value,
            description: document.getElementById('planDescription').value
        };
    }
    
    async handleConfirmSubscription() {
        if (!this.web3.isWalletConnected()) {
            toastManager.error('Please connect your wallet first');
            return;
        }
        
        const planId = modalManager.activeModal?.dataset.planId;
        if (!planId) {
            toastManager.error('No plan selected');
            return;
        }
        
        try {
            loadingManager.show('Processing subscription...');
            
            // Get plan details
            const plan = await this.api.getPlan(planId);
            
            // Create payment signature
            const timestamp = new Date().toISOString();
            const signatureData = await this.paymentSigner.createPaymentSignature(
                planId,
                plan.amount,
                plan.token,
                timestamp
            );
            
            const paymentHeader = this.paymentSigner.createPaymentHeader({
                amount: plan.amount,
                token: plan.token,
                signature: signatureData.signature,
                timestamp: timestamp,
                from_address: this.currentUser
            });
            
            // Subscribe via API
            const subscription = await this.api.subscribeToPlan({
                plan_id: planId,
                subscriber_address: this.currentUser
            }, paymentHeader);
            
            toastManager.success('Subscription created successfully!');
            modalManager.close();
            
            // Reload user data
            await this.loadUserData();
            await subscriptionManager.loadSubscriptions();
            
        } catch (error) {
            console.error('Subscription failed:', error);
            toastManager.error(error.message || 'Failed to create subscription');
        } finally {
            loadingManager.hide();
        }
    }
}

// Dashboard Manager
class DashboardManager {
    constructor() {
        this.stats = {
            totalPlans: 0,
            totalSubscribers: 0,
            totalRevenue: 0,
            monthlyGrowth: 0
        };
    }
    
    async loadData() {
        await this.updateStats();
    }
    
    async updateStats() {
        try {
            // Get all plans and subscriptions for stats
            const plansData = await app.api.devListAllPlans();
            const subscriptionsData = await app.api.devListAllSubscriptions();
            const paymentsData = await app.api.devListAllPayments();
            
            this.stats.totalPlans = plansData.plans.filter(p => p.active).length;
            this.stats.totalSubscribers = new Set(subscriptionsData.subscriptions.map(s => s.subscriber_address)).size;
            this.stats.totalRevenue = paymentsData.payments.reduce((sum, p) => sum + p.amount, 0);
            this.stats.monthlyGrowth = this.calculateGrowth(paymentsData.payments);
            
            this.renderStats();
            
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }
    
    calculateGrowth(payments) {
        const now = new Date();
        const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        
        const lastMonthPayments = payments.filter(p => {
            const date = new Date(p.timestamp);
            return date >= lastMonth && date < thisMonth;
        });
        
        const thisMonthPayments = payments.filter(p => {
            const date = new Date(p.timestamp);
            return date >= thisMonth;
        });
        
        const lastMonthTotal = lastMonthPayments.reduce((sum, p) => sum + p.amount, 0);
        const thisMonthTotal = thisMonthPayments.reduce((sum, p) => sum + p.amount, 0);
        
        if (lastMonthTotal === 0) return thisMonthTotal > 0 ? 100 : 0;
        
        return Math.round(((thisMonthTotal - lastMonthTotal) / lastMonthTotal) * 100);
    }
    
    renderStats() {
        document.getElementById('totalPlans').textContent = this.stats.totalPlans;
        document.getElementById('totalSubscribers').textContent = this.stats.totalSubscribers;
        document.getElementById('totalRevenue').textContent = `${this.stats.totalRevenue.toFixed(2)} ETH`;
        document.getElementById('monthlyGrowth').textContent = `${this.stats.monthlyGrowth >= 0 ? '+' : ''}${this.stats.monthlyGrowth}%`;
    }
}

// Plan Manager
class PlanManager {
    constructor() {
        this.plans = [];
    }
    
    async loadPlans() {
        try {
            const response = await app.api.listPlans();
            this.plans = response;
            this.renderPlans();
        } catch (error) {
            console.error('Failed to load plans:', error);
            toastManager.error('Failed to load plans');
        }
    }
    
    renderPlans() {
        const container = document.getElementById('plansGrid');
        if (!container) return;
        
        if (this.plans.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-layer-group"></i>
                    <h3>No plans available</h3>
                    <p>Create your first subscription plan to get started.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.plans
            .map(plan => PlanCard.create(plan))
            .join('');
    }
    
    async subscribe(planId) {
        if (!app.web3.isWalletConnected()) {
            toastManager.error('Please connect your wallet first');
            return;
        }
        
        try {
            const plan = await app.api.getPlan(planId);
            this.showSubscriptionModal(plan);
        } catch (error) {
            console.error('Failed to load plan details:', error);
            toastManager.error('Failed to load plan details');
        }
    }
    
    showSubscriptionModal(plan) {
        const modal = document.getElementById('subscribeModal');
        modal.dataset.planId = plan.plan_id;
        
        // Populate plan details
        document.getElementById('subscriptionDetails').innerHTML = `
            <div class="plan-summary">
                <h4>${plan.description || 'Subscription Plan'}</h4>
                <p class="plan-creator">Created by ${DataTransformer.formatAddress(plan.creator)}</p>
            </div>
        `;
        
        document.getElementById('paymentAmount').textContent = `${plan.amount} ${plan.token === 'native' ? 'ETH' : plan.token}`;
        document.getElementById('paymentToken').textContent = plan.token === 'native' ? 'Native Token' : 'ERC-20 Token';
        document.getElementById('paymentInterval').textContent = `Every ${plan.interval_days} day${plan.interval_days !== 1 ? 's' : ''}`;
        
        modalManager.open('subscribeModal');
    }
    
    async viewDetails(planId) {
        try {
            const plan = await app.api.getPlan(planId);
            // Show plan details in a modal or navigate to details page
            console.log('Plan details:', plan);
        } catch (error) {
            console.error('Failed to load plan details:', error);
        }
    }
}

// Subscription Manager
class SubscriptionManager {
    constructor() {
        this.subscriptions = [];
        this.currentFilter = 'all';
    }
    
    async loadSubscriptions() {
        if (!app.currentUser) {
            this.renderEmptyState();
            return;
        }
        
        try {
            const subscriptions = await app.api.getUserSubscriptions(app.currentUser, false);
            this.subscriptions = subscriptions;
            this.renderSubscriptions();
        } catch (error) {
            console.error('Failed to load subscriptions:', error);
            toastManager.error('Failed to load subscriptions');
        }
    }
    
    renderSubscriptions() {
        const container = document.getElementById('subscriptionsGrid');
        if (!container) return;
        
        if (this.subscriptions.length === 0) {
            this.renderEmptyState();
            return;
        }
        
        const filteredSubscriptions = this.filterSubscriptions();
        
        container.innerHTML = filteredSubscriptions
            .map(subscription => SubscriptionCard.create(subscription))
            .join('');
    }
    
    renderEmptyState() {
        const container = document.getElementById('subscriptionsGrid');
        if (!container) return;
        
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-credit-card"></i>
                <h3>No subscriptions found</h3>
                <p>Subscribe to plans to see them here.</p>
            </div>
        `;
    }
    
    filterSubscriptions() {
        if (this.currentFilter === 'all') return this.subscriptions;
        
        return this.subscriptions.filter(sub => {
            const formatted = DataTransformer.formatSubscription(sub);
            
            switch (this.currentFilter) {
                case 'active':
                    return sub.active && !formatted.is_expired;
                case 'expired':
                    return formatted.is_expired;
                case 'cancelled':
                    return !sub.active;
                default:
                    return true;
            }
        });
    }
    
    async cancel(planId) {
        if (!confirm('Are you sure you want to cancel this subscription?')) {
            return;
        }
        
        try {
            loadingManager.show('Cancelling subscription...');
            
            const timestamp = new Date().toISOString();
            const signatureData = await app.paymentSigner.createPaymentSignature(
                planId,
                0,
                'native',
                timestamp
            );
            
            const paymentHeader = app.paymentSigner.createPaymentHeader({
                amount: 0,
                token: 'native',
                signature: signatureData.signature,
                timestamp: timestamp,
                from_address: app.currentUser
            });
            
            await app.api.cancelSubscription(planId, paymentHeader);
            
            toastManager.success('Subscription cancelled successfully');
            await this.loadSubscriptions();
            
        } catch (error) {
            console.error('Failed to cancel subscription:', error);
            toastManager.error('Failed to cancel subscription');
        } finally {
            loadingManager.hide();
        }
    }
    
    async viewDetails(subscriptionId) {
        // Show subscription details
        console.log('View subscription details:', subscriptionId);
    }
    
    async payNow(planId) {
        // Handle overdue payment
        console.log('Process payment for plan:', planId);
    }
}

// Analytics Manager
class AnalyticsManager {
    constructor() {
        this.data = {
            revenue: [],
            subscriptionStatus: [],
            topPlans: [],
            paymentHistory: []
        };
    }
    
    async loadAnalytics() {
        try {
            const [plans, subscriptions, payments] = await Promise.all([
                app.api.devListAllPlans(),
                app.api.devListAllSubscriptions(),
                app.api.devListAllPayments()
            ]);
            
            this.processAnalyticsData(plans.plans, subscriptions.subscriptions, payments.payments);
            this.renderAnalytics();
            
        } catch (error) {
            console.error('Failed to load analytics:', error);
        }
    }
    
    processAnalyticsData(plans, subscriptions, payments) {
        // Process revenue data
        this.data.revenue = this.processRevenueData(payments);
        
        // Process subscription status
        this.data.subscriptionStatus = this.processSubscriptionStatus(subscriptions);
        
        // Process top plans
        this.data.topPlans = this.processTopPlans(plans, subscriptions);
        
        // Process payment history
        this.data.paymentHistory = payments.slice(-10).reverse();
    }
    
    processRevenueData(payments) {
        const last7Days = [];
        const now = new Date();
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            const dateStr = date.toISOString().split('T')[0];
            
            const dayPayments = payments.filter(p => 
                p.timestamp.startsWith(dateStr)
            );
            
            const total = dayPayments.reduce((sum, p) => sum + p.amount, 0);
            
            last7Days.push({
                date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
                value: total
            });
        }
        
        return last7Days;
    }
    
    processSubscriptionStatus(subscriptions) {
        const active = subscriptions.filter(s => s.active).length;
        const expired = subscriptions.filter(s => {
            const endTime = new Date(s.end_time);
            return endTime < new Date();
        }).length;
        const cancelled = subscriptions.filter(s => !s.active).length;
        
        return [
            { label: 'Active', value: active },
            { label: 'Expired', value: expired },
            { label: 'Cancelled', value: cancelled }
        ];
    }
    
    processTopPlans(plans, subscriptions) {
        const planStats = plans.map(plan => {
            const planSubscriptions = subscriptions.filter(s => s.plan_id === plan.plan_id);
            const revenue = planSubscriptions.reduce((sum, s) => sum + s.total_paid, 0);
            
            return {
                ...plan,
                subscriber_count: planSubscriptions.length,
                revenue: revenue
            };
        });
        
        return planStats
            .sort((a, b) => b.revenue - a.revenue)
            .slice(0, 5);
    }
    
    renderAnalytics() {
        // Render revenue chart
        chartManager.createRevenueChart('revenueChart', {
            labels: this.data.revenue.map(d => d.date),
            values: this.data.revenue.map(d => d.value)
        });
        
        // Render status chart
        chartManager.createStatusChart('statusChart', {
            labels: this.data.subscriptionStatus.map(d => d.label),
            values: this.data.subscriptionStatus.map(d => d.value)
        });
        
        // Render top plans
        this.renderTopPlans();
        
        // Render payment history
        this.renderPaymentHistory();
    }
    
    renderTopPlans() {
        const container = document.getElementById('topPlans');
        if (!container) return;
        
        if (this.data.topPlans.length === 0) {
            container.innerHTML = '<p class="text-muted">No plans available</p>';
            return;
        }
        
        container.innerHTML = this.data.topPlans.map((plan, index) => `
            <div class="top-plan-item">
                <div class="plan-rank">#${index + 1}</div>
                <div class="plan-info">
                    <div class="plan-name">${plan.description || 'Unnamed Plan'}</div>
                    <div class="plan-stats">
                        ${plan.subscriber_count} subscribers • ${plan.revenue.toFixed(2)} ETH
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    renderPaymentHistory() {
        const container = document.getElementById('paymentHistory');
        if (!container) return;
        
        if (this.data.paymentHistory.length === 0) {
            container.innerHTML = '<p class="text-muted">No payments yet</p>';
            return;
        }
        
        container.innerHTML = this.data.paymentHistory.map(payment => `
            <div class="payment-item">
                <div class="payment-info">
                    <div class="payment-amount">${payment.amount} ETH</div>
                    <div class="payment-details">
                        ${DataTransformer.formatAddress(payment.subscriber_address)} • 
                        ${DataTransformer.formatDate(payment.timestamp)}
                    </div>
                </div>
                <div class="payment-type">${payment.payment_type}</div>
            </div>
        `).join('');
    }
}

// Initialize application
let app, dashboardManager, planManager, subscriptionManager, analyticsManager;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize managers
    app = new SKALEPaymentApp();
    dashboardManager = new DashboardManager();
    planManager = new PlanManager();
    subscriptionManager = new SubscriptionManager();
    analyticsManager = new AnalyticsManager();
    
    // Setup filter buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('filter-btn')) {
            // Update active filter
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            
            // Update filter and re-render
            subscriptionManager.currentFilter = e.target.dataset.filter;
            subscriptionManager.renderSubscriptions();
        }
    });
    
    // Make managers globally available
    window.app = app;
    window.dashboardManager = dashboardManager;
    window.planManager = planManager;
    window.subscriptionManager = subscriptionManager;
    window.analyticsManager = analyticsManager;
});

// Add some CSS animations for toast slide out
const style = document.createElement('style');
style.textContent = `
    @keyframes toastSlideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: var(--text-secondary);
    }
    
    .empty-state i {
        font-size: 3rem;
        margin-bottom: 1rem;
        color: var(--primary-color);
    }
    
    .empty-state h3 {
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }
    
    .top-plan-item, .payment-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .plan-rank {
        font-weight: 700;
        color: var(--primary-color);
        min-width: 2rem;
    }
    
    .plan-info {
        flex: 1;
    }
    
    .plan-name {
        font-weight: 500;
        margin-bottom: 0.25rem;
    }
    
    .plan-stats, .payment-details {
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    
    .payment-amount {
        font-weight: 600;
        color: var(--success-color);
    }
    
    .payment-type {
        font-size: 0.75rem;
        padding: 0.25rem 0.5rem;
        background: var(--background-color);
        border-radius: var(--radius-sm);
        text-transform: uppercase;
        font-weight: 600;
    }
`;
document.head.appendChild(style);

