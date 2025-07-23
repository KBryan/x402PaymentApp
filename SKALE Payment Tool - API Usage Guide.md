# SKALE Payment Tool - API Usage Guide

This guide provides detailed instructions on how to use the SKALE Payment Tool API for subscription management and payment processing.

## Quick Start

### 1. Start the API Server

```bash
cd backend
source venv/bin/activate
python main.py
```

The API will be available at: `http://localhost:8000`

### 2. Access API Documentation

- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health

## Authentication

The API uses X402 payment-based authentication. Include the payment header in protected requests:

```http
X-PAYMENT: b64:amount:token:signature:timestamp:from_address
```

### X402 Header Format

```
b64:100:native:0x1234...signature:2025-07-20T15:30:00Z:0xabcd...address
```

**Components:**
- `b64`: Protocol identifier
- `amount`: Payment amount (float)
- `token`: Token type ("native" or contract address)
- `signature`: Payment signature
- `timestamp`: ISO timestamp
- `from_address`: Payer's address

## API Endpoints

### Core Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-20T15:30:00.123456"
}
```

#### Root Information
```http
GET /
```

**Response:**
```json
{
  "message": "SKALE Payment Tool API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### Plan Management

#### Create New Plan
```http
POST /plans/create
X-PAYMENT: b64:100:native:signature:timestamp:address
Content-Type: application/json

{
  "token": "native",
  "amount": 100.0,
  "interval_days": 30,
  "duration_days": 365,
  "api_url": "https://api.example.com/protected",
  "description": "Premium API Access Plan"
}
```

**Response:**
```json
{
  "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
  "token": "native",
  "amount": 100.0,
  "interval_days": 30,
  "duration_days": 365,
  "encrypted_api_url": "x402_encrypted_...",
  "description": "Premium API Access Plan",
  "creator": "0x1111111111111111111111111111111111111111",
  "active": true,
  "created_at": "2025-07-20T15:30:00.123456"
}
```

#### List All Plans
```http
GET /plans?active_only=true
```

**Response:**
```json
[
  {
    "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
    "token": "native",
    "amount": 100.0,
    "interval_days": 30,
    "duration_days": 365,
    "encrypted_api_url": "x402_encrypted_...",
    "description": "Premium API Access Plan",
    "creator": "0x1111111111111111111111111111111111111111",
    "active": true,
    "created_at": "2025-07-20T15:30:00.123456"
  }
]
```

#### Get Specific Plan
```http
GET /plans/{plan_id}
```

#### Deactivate Plan
```http
PUT /plans/{plan_id}/deactivate
X-PAYMENT: b64:amount:token:signature:timestamp:address
```

### Subscription Management

#### Subscribe to Plan
```http
POST /subscribe
X-PAYMENT: b64:100:native:signature:timestamp:address
Content-Type: application/json

{
  "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
  "subscriber_address": "0x2222222222222222222222222222222222222222"
}
```

**Response:**
```json
{
  "subscription_id": "sub_12345678-1234-1234-1234-123456789012",
  "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
  "subscriber_address": "0x2222222222222222222222222222222222222222",
  "start_time": "2025-07-20T15:30:00.123456",
  "next_payment_due": "2025-08-19T15:30:00.123456",
  "end_time": "2026-07-20T15:30:00.123456",
  "total_paid": 100.0,
  "active": true
}
```

#### Get Subscription Details
```http
GET /subscriptions/{plan_id}/{subscriber_address}
```

#### Get User Subscriptions
```http
GET /subscriptions/user/{address}?active_only=true
```

#### Cancel Subscription
```http
POST /subscriptions/{plan_id}/cancel
X-PAYMENT: b64:amount:token:signature:timestamp:address
```

### Payment Processing

#### Process Recurring Payment
```http
POST /payments/process
X-PAYMENT: b64:100:native:signature:timestamp:address
Content-Type: application/json

{
  "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
  "subscriber_address": "0x2222222222222222222222222222222222222222",
  "transaction_hash": "0x1234567890abcdef..."
}
```

#### Get Payment History
```http
GET /payments/history/{address}
```

**Response:**
```json
{
  "payments": [
    {
      "payment_id": "pay_12345678-1234-1234-1234-123456789012",
      "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
      "subscriber_address": "0x2222222222222222222222222222222222222222",
      "amount": 100.0,
      "timestamp": "2025-07-20T15:30:00.123456",
      "transaction_hash": "0x1234567890abcdef...",
      "payment_type": "initial"
    }
  ]
}
```

### Access Verification

#### Verify API Access
```http
GET /verify-access/{plan_id}?subscriber_address=0x2222...
X-PAYMENT: b64:amount:token:signature:timestamp:address
```

**Response:**
```json
{
  "access_granted": true,
  "api_url": "https://api.example.com/protected",
  "subscription_expires": "2026-07-20T15:30:00.123456",
  "next_payment_due": "2025-08-19T15:30:00.123456"
}
```

### Development Endpoints

#### List All Plans (No Auth)
```http
GET /dev/plans
```

#### List All Subscriptions (No Auth)
```http
GET /dev/subscriptions
```

#### List All Payments (No Auth)
```http
GET /dev/payments
```

#### Reset All Data
```http
POST /dev/reset
```

## Code Examples

### Python Example

```python
import requests
import json
from datetime import datetime

# API Configuration
API_BASE = "http://localhost:8000"
HEADERS = {
    "Content-Type": "application/json",
    "X-PAYMENT": "b64:100:native:signature123:2025-07-20T15:30:00Z:0x1111111111111111111111111111111111111111"
}

# Create a new plan
def create_plan():
    data = {
        "token": "native",
        "amount": 100.0,
        "interval_days": 30,
        "duration_days": 365,
        "api_url": "https://api.example.com/protected",
        "description": "Premium API Access Plan"
    }
    
    response = requests.post(
        f"{API_BASE}/plans/create",
        headers=HEADERS,
        json=data
    )
    
    if response.status_code == 200:
        plan = response.json()
        print(f"Plan created: {plan['plan_id']}")
        return plan
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Subscribe to a plan
def subscribe_to_plan(plan_id, subscriber_address):
    data = {
        "plan_id": plan_id,
        "subscriber_address": subscriber_address
    }
    
    response = requests.post(
        f"{API_BASE}/subscribe",
        headers=HEADERS,
        json=data
    )
    
    if response.status_code == 200:
        subscription = response.json()
        print(f"Subscribed: {subscription['subscription_id']}")
        return subscription
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# List all plans
def list_plans():
    response = requests.get(f"{API_BASE}/plans")
    
    if response.status_code == 200:
        plans = response.json()
        print(f"Found {len(plans)} plans")
        for plan in plans:
            print(f"- {plan['plan_id']}: {plan['description']}")
        return plans
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return []

# Example usage
if __name__ == "__main__":
    # List existing plans
    plans = list_plans()
    
    # Create a new plan
    new_plan = create_plan()
    
    if new_plan:
        # Subscribe to the plan
        subscription = subscribe_to_plan(
            new_plan['plan_id'],
            "0x2222222222222222222222222222222222222222"
        )
```

### JavaScript Example

```javascript
// API Configuration
const API_BASE = "http://localhost:8000";
const PAYMENT_HEADER = "b64:100:native:signature123:2025-07-20T15:30:00Z:0x1111111111111111111111111111111111111111";

// Create a new plan
async function createPlan() {
    const data = {
        token: "native",
        amount: 100.0,
        interval_days: 30,
        duration_days: 365,
        api_url: "https://api.example.com/protected",
        description: "Premium API Access Plan"
    };
    
    try {
        const response = await fetch(`${API_BASE}/plans/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-PAYMENT': PAYMENT_HEADER
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const plan = await response.json();
            console.log(`Plan created: ${plan.plan_id}`);
            return plan;
        } else {
            const error = await response.text();
            console.error(`Error: ${response.status} - ${error}`);
            return null;
        }
    } catch (error) {
        console.error('Network error:', error);
        return null;
    }
}

// Subscribe to a plan
async function subscribeToPlan(planId, subscriberAddress) {
    const data = {
        plan_id: planId,
        subscriber_address: subscriberAddress
    };
    
    try {
        const response = await fetch(`${API_BASE}/subscribe`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-PAYMENT': PAYMENT_HEADER
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const subscription = await response.json();
            console.log(`Subscribed: ${subscription.subscription_id}`);
            return subscription;
        } else {
            const error = await response.text();
            console.error(`Error: ${response.status} - ${error}`);
            return null;
        }
    } catch (error) {
        console.error('Network error:', error);
        return null;
    }
}

// List all plans
async function listPlans() {
    try {
        const response = await fetch(`${API_BASE}/plans`);
        
        if (response.ok) {
            const plans = await response.json();
            console.log(`Found ${plans.length} plans`);
            plans.forEach(plan => {
                console.log(`- ${plan.plan_id}: ${plan.description}`);
            });
            return plans;
        } else {
            const error = await response.text();
            console.error(`Error: ${response.status} - ${error}`);
            return [];
        }
    } catch (error) {
        console.error('Network error:', error);
        return [];
    }
}

// Example usage
async function main() {
    // List existing plans
    const plans = await listPlans();
    
    // Create a new plan
    const newPlan = await createPlan();
    
    if (newPlan) {
        // Subscribe to the plan
        const subscription = await subscribeToPlan(
            newPlan.plan_id,
            "0x2222222222222222222222222222222222222222"
        );
    }
}

// Run the example
main().catch(console.error);
```

### cURL Examples

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# List plans
curl -X GET "http://localhost:8000/plans"

# Create plan (with authentication)
curl -X POST "http://localhost:8000/plans/create" \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: b64:100:native:signature123:2025-07-20T15:30:00Z:0x1111111111111111111111111111111111111111" \
  -d '{
    "token": "native",
    "amount": 100.0,
    "interval_days": 30,
    "duration_days": 365,
    "api_url": "https://api.example.com/protected",
    "description": "Premium API Access Plan"
  }'

# Subscribe to plan
curl -X POST "http://localhost:8000/subscribe" \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: b64:100:native:signature123:2025-07-20T15:30:00Z:0x2222222222222222222222222222222222222222" \
  -d '{
    "plan_id": "bbb819cc-c633-41bc-abb4-899333133104",
    "subscriber_address": "0x2222222222222222222222222222222222222222"
  }'

# Get subscription details
curl -X GET "http://localhost:8000/subscriptions/bbb819cc-c633-41bc-abb4-899333133104/0x2222222222222222222222222222222222222222"

# Verify API access
curl -X GET "http://localhost:8000/verify-access/bbb819cc-c633-41bc-abb4-899333133104?subscriber_address=0x2222222222222222222222222222222222222222" \
  -H "X-PAYMENT: b64:100:native:signature123:2025-07-20T15:30:00Z:0x2222222222222222222222222222222222222222"
```

## Error Handling

### Common HTTP Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Missing or invalid authentication
- **402 Payment Required**: X402 payment verification failed
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

#### Missing Payment Header
```json
{
  "detail": "Payment required - missing X-PAYMENT header"
}
```

#### Invalid Payment Header
```json
{
  "detail": "Payment verification failed: Invalid payment header format"
}
```

#### Insufficient Payment
```json
{
  "detail": "Insufficient payment amount"
}
```

#### Plan Not Found
```json
{
  "detail": "Plan not found"
}
```

#### Already Subscribed
```json
{
  "detail": "Already subscribed to this plan"
}
```

## 🔧 Testing

### Test with Development Endpoints

```bash
# Reset all data
curl -X POST "http://localhost:8000/dev/reset"

# List all data without authentication
curl -X GET "http://localhost:8000/dev/plans"
curl -X GET "http://localhost:8000/dev/subscriptions"
curl -X GET "http://localhost:8000/dev/payments"
```

### Automated Testing Script

```bash
#!/bin/bash

API_BASE="http://localhost:8000"
PAYMENT_HEADER="b64:100:native:signature123:2025-07-20T15:30:00Z:0x1111111111111111111111111111111111111111"

echo "Testing SKALE Payment Tool API..."

# Health check
echo "1. Health check..."
curl -s "$API_BASE/health" | jq .

# List plans
echo "2. List plans..."
curl -s "$API_BASE/plans" | jq .

# Create plan
echo "3. Create plan..."
PLAN_RESPONSE=$(curl -s -X POST "$API_BASE/plans/create" \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: $PAYMENT_HEADER" \
  -d '{
    "token": "native",
    "amount": 100.0,
    "interval_days": 30,
    "duration_days": 365,
    "api_url": "https://api.example.com/protected",
    "description": "Test Plan"
  }')

PLAN_ID=$(echo "$PLAN_RESPONSE" | jq -r .plan_id)
echo "Created plan: $PLAN_ID"

# Subscribe to plan
echo "4. Subscribe to plan..."
curl -s -X POST "$API_BASE/subscribe" \
  -H "Content-Type: application/json" \
  -H "X-PAYMENT: $PAYMENT_HEADER" \
  -d "{
    \"plan_id\": \"$PLAN_ID\",
    \"subscriber_address\": \"0x2222222222222222222222222222222222222222\"
  }" | jq .

echo "API testing complete!"
```

## Additional Resources

- **Interactive API Documentation**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Main README**: [README.md](README.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Frontend Integration**: See `frontend/js/api-client.js`

## Support

For issues or questions:
1. Check the interactive documentation at `/docs`
2. Review error messages and status codes
3. Test with development endpoints first
4. Check server logs for detailed error information

---

**Happy coding with the SKALE Payment Tool API!** 🚀

