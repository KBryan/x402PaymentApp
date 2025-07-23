/**
 * API Client Module
 * Handles communication with the FastAPI backend
 */

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }
    
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            
            // Handle different response types
            const contentType = response.headers.get('content-type');
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }
            
            if (!response.ok) {
                throw new APIError(response.status, data.detail || data || 'Request failed', data);
            }
            
            return data;
        } catch (error) {
            if (error instanceof APIError) {
                throw error;
            }
            throw new APIError(0, 'Network error', error.message);
        }
    }
    
    // Health check
    async healthCheck() {
        return this.request('/health');
    }
    
    // Plan management
    async createPlan(planData, paymentHeader) {
        return this.request('/plans/create', {
            method: 'POST',
            headers: {
                'X-PAYMENT': paymentHeader
            },
            body: JSON.stringify(planData)
        });
    }
    
    async getPlan(planId) {
        return this.request(`/plans/${planId}`);
    }
    
    async listPlans(activeOnly = true) {
        const params = new URLSearchParams({ active_only: activeOnly });
        return this.request(`/plans?${params}`);
    }
    
    async deactivatePlan(planId, paymentHeader) {
        return this.request(`/plans/${planId}/deactivate`, {
            method: 'PUT',
            headers: {
                'X-PAYMENT': paymentHeader
            }
        });
    }
    
    // Subscription management
    async subscribeToPlan(subscriptionData, paymentHeader) {
        return this.request('/subscribe', {
            method: 'POST',
            headers: {
                'X-PAYMENT': paymentHeader
            },
            body: JSON.stringify(subscriptionData)
        });
    }
    
    async getSubscription(planId, subscriberAddress) {
        return this.request(`/subscriptions/${planId}/${subscriberAddress}`);
    }
    
    async getUserSubscriptions(address, activeOnly = true) {
        const params = new URLSearchParams({ active_only: activeOnly });
        return this.request(`/subscriptions/user/${address}?${params}`);
    }
    
    async cancelSubscription(planId, paymentHeader) {
        return this.request(`/subscriptions/${planId}/cancel`, {
            method: 'POST',
            headers: {
                'X-PAYMENT': paymentHeader
            }
        });
    }
    
    // Payment processing
    async processRecurringPayment(paymentData, paymentHeader) {
        return this.request('/payments/process', {
            method: 'POST',
            headers: {
                'X-PAYMENT': paymentHeader
            },
            body: JSON.stringify(paymentData)
        });
    }
    
    async getPaymentHistory(address) {
        return this.request(`/payments/history/${address}`);
    }
    
    // API access verification
    async verifyAPIAccess(planId, subscriberAddress, paymentHeader) {
        const params = new URLSearchParams({ subscriber_address: subscriberAddress });
        return this.request(`/verify-access/${planId}?${params}`, {
            headers: {
                'X-PAYMENT': paymentHeader
            }
        });
    }
    
    // Development endpoints (remove in production)
    async devListAllPlans() {
        return this.request('/dev/plans');
    }
    
    async devListAllSubscriptions() {
        return this.request('/dev/subscriptions');
    }
    
    async devListAllPayments() {
        return this.request('/dev/payments');
    }
}

// Custom error class for API errors
class APIError extends Error {
    constructor(status, message, details = null) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.details = details;
    }
    
    isNetworkError() {
        return this.status === 0;
    }
    
    isClientError() {
        return this.status >= 400 && this.status < 500;
    }
    
    isServerError() {
        return this.status >= 500;
    }
    
    isPaymentRequired() {
        return this.status === 402;
    }
    
    isNotFound() {
        return this.status === 404;
    }
    
    isForbidden() {
        return this.status === 403;
    }
}

// Data transformation utilities
class DataTransformer {
    static formatPlan(plan) {
        return {
            ...plan,
            created_at: new Date(plan.created_at),
            amount_formatted: `${plan.amount} ${plan.token === 'native' ? 'ETH' : plan.token}`,
            interval_formatted: `${plan.interval_days} day${plan.interval_days !== 1 ? 's' : ''}`,
            duration_formatted: `${plan.duration_days} day${plan.duration_days !== 1 ? 's' : ''}`,
            creator_formatted: this.formatAddress(plan.creator)
        };
    }
    
    static formatSubscription(subscription) {
        const startTime = new Date(subscription.start_time);
        const endTime = new Date(subscription.end_time);
        const nextPayment = new Date(subscription.next_payment_due);
        const now = new Date();
        
        return {
            ...subscription,
            start_time: startTime,
            end_time: endTime,
            next_payment_due: nextPayment,
            subscriber_formatted: this.formatAddress(subscription.subscriber_address),
            total_paid_formatted: `${subscription.total_paid} ETH`,
            days_remaining: Math.max(0, Math.ceil((endTime - now) / (1000 * 60 * 60 * 24))),
            is_expired: now > endTime,
            is_payment_overdue: now > nextPayment && subscription.active
        };
    }
    
    static formatPayment(payment) {
        return {
            ...payment,
            timestamp: new Date(payment.timestamp),
            amount_formatted: `${payment.amount} ETH`,
            subscriber_formatted: this.formatAddress(payment.subscriber_address),
            transaction_hash_formatted: this.formatAddress(payment.transaction_hash)
        };
    }
    
    static formatAddress(address) {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }
    
    static formatDate(date) {
        if (!date) return '';
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }
    
    static formatCurrency(amount, currency = 'ETH') {
        return `${parseFloat(amount).toFixed(4)} ${currency}`;
    }
}

// Cache management for API responses
class APICache {
    constructor(ttl = 300000) { // 5 minutes default TTL
        this.cache = new Map();
        this.ttl = ttl;
    }
    
    set(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
    
    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() - item.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }
        
        return item.data;
    }
    
    clear() {
        this.cache.clear();
    }
    
    delete(key) {
        this.cache.delete(key);
    }
}

// Enhanced API client with caching and retry logic
class EnhancedAPIClient extends APIClient {
    constructor(baseURL = 'http://localhost:8000', options = {}) {
        super(baseURL);
        this.cache = new APICache(options.cacheTTL);
        this.retryAttempts = options.retryAttempts || 3;
        this.retryDelay = options.retryDelay || 1000;
    }
    
    async requestWithCache(endpoint, options = {}, useCache = true) {
        const cacheKey = `${endpoint}_${JSON.stringify(options)}`;
        
        // Check cache for GET requests
        if (useCache && (!options.method || options.method === 'GET')) {
            const cached = this.cache.get(cacheKey);
            if (cached) return cached;
        }
        
        // Make request with retry logic
        let lastError;
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                const result = await this.request(endpoint, options);
                
                // Cache successful GET requests
                if (useCache && (!options.method || options.method === 'GET')) {
                    this.cache.set(cacheKey, result);
                }
                
                return result;
            } catch (error) {
                lastError = error;
                
                // Don't retry client errors (4xx)
                if (error instanceof APIError && error.isClientError()) {
                    throw error;
                }
                
                // Wait before retry
                if (attempt < this.retryAttempts) {
                    await new Promise(resolve => setTimeout(resolve, this.retryDelay * attempt));
                }
            }
        }
        
        throw lastError;
    }
    
    // Override methods to use enhanced request
    async listPlans(activeOnly = true, useCache = true) {
        const params = new URLSearchParams({ active_only: activeOnly });
        return this.requestWithCache(`/plans?${params}`, {}, useCache);
    }
    
    async getPlan(planId, useCache = true) {
        return this.requestWithCache(`/plans/${planId}`, {}, useCache);
    }
    
    async getUserSubscriptions(address, activeOnly = true, useCache = true) {
        const params = new URLSearchParams({ active_only: activeOnly });
        return this.requestWithCache(`/subscriptions/user/${address}?${params}`, {}, useCache);
    }
    
    // Clear cache when data changes
    async createPlan(planData, paymentHeader) {
        const result = await super.createPlan(planData, paymentHeader);
        this.cache.clear(); // Clear cache after creating new data
        return result;
    }
    
    async subscribeToPlan(subscriptionData, paymentHeader) {
        const result = await super.subscribeToPlan(subscriptionData, paymentHeader);
        this.cache.clear(); // Clear cache after creating new data
        return result;
    }
}

// Export for use in other modules
window.APIClient = APIClient;
window.EnhancedAPIClient = EnhancedAPIClient;
window.APIError = APIError;
window.DataTransformer = DataTransformer;

