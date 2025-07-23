"""
SKALE Payment Tool - FastAPI Backend (FIXED VERSION)
Main application with X402 encryption integration and smart contract interaction
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import uuid
import hashlib
import base64
import json
import os
from web3 import Web3
from eth_account import Account

# Initialize FastAPI app
app = FastAPI(
    title="SKALE Payment Tool API",
    description="Backend API for SKALE Payment Chain and Tool with X402 encryption",
    version="1.0.0"
)

# FIXED: Proper CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
plans_db: Dict[str, Dict] = {}
subscriptions_db: Dict[str, Dict] = {}
payments_db: List[Dict] = []

# Initialize with a test plan for development
def initialize_test_data():
    """Initialize with test data for development"""
    test_plan_id = "bbb819cc-c633-41bc-abb4-899333133104"
    test_plan = {
        "plan_id": test_plan_id,
        "token": "native",
        "amount": 100.0,
        "interval_days": 30,
        "duration_days": 365,
        "encrypted_api_url": "x402_encrypted_aHR0cHM6Ly9hcGkuZXhhbXBsZS5jb20vcHJvdGVjdGVkOmRlZmF1bHRfa2V5OjIwMjUtMDctMjBUMTU6MzU6MDMuNTIyNzcw",
        "description": "Test subscription plan",
        "creator": "0x1111111111111111111111111111111111111111",
        "active": True,
        "created_at": datetime.utcnow()
    }
    plans_db[test_plan_id] = test_plan

# X402 Encryption Placeholder (replace with real X402 implementation)
class X402Encryption:
    @staticmethod
    def encrypt_url(url: str, key: str = "default_key") -> str:
        """Placeholder encryption function"""
        combined = f"{url}:{key}:{datetime.utcnow().isoformat()}"
        encoded = base64.b64encode(combined.encode()).decode()
        return f"x402_encrypted_{encoded}"
    
    @staticmethod
    def decrypt_url(encrypted_url: str, key: str = "default_key") -> str:
        """Placeholder decryption function"""
        if not encrypted_url.startswith("x402_encrypted_"):
            raise ValueError("Invalid encrypted URL format")
        
        encoded = encrypted_url.replace("x402_encrypted_", "")
        try:
            decoded = base64.b64decode(encoded).decode()
            url = decoded.split(":")[0]
            return url
        except Exception:
            raise ValueError("Failed to decrypt URL")
    
    @staticmethod
    def verify_payment_header(x_payment: str) -> Dict[str, Any]:
        """Placeholder payment header verification"""
        try:
            # Handle both base64 encoded and direct JSON formats
            if x_payment.startswith("b64:"):
                # X402 format: b64:amount:token:signature:timestamp:from_address
                parts = x_payment.split(":")
                if len(parts) >= 6:
                    return {
                        "amount": float(parts[1]),
                        "token": parts[2],
                        "signature": parts[3],
                        "timestamp": parts[4],
                        "from_address": parts[5]
                    }
            
            # Try to decode as base64 JSON
            try:
                payload = base64.b64decode(x_payment).decode()
                payment_data = json.loads(payload)
            except:
                # If not base64, try direct JSON
                payment_data = json.loads(x_payment)
            
            # Basic validation
            required_fields = ["amount", "token", "signature", "timestamp"]
            for field in required_fields:
                if field not in payment_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Check timestamp (within 5 minutes)
            try:
                timestamp = datetime.fromisoformat(payment_data["timestamp"])
                if datetime.utcnow() - timestamp > timedelta(minutes=5):
                    raise ValueError("Payment header expired")
            except:
                # If timestamp parsing fails, allow it for development
                pass
            
            return payment_data
        except Exception as e:
            raise ValueError(f"Invalid payment header: {str(e)}")

# Pydantic models
class CreatePlanRequest(BaseModel):
    token: str  # Token contract address or "native" for native token
    amount: float
    interval_days: int
    duration_days: int
    api_url: str
    description: Optional[str] = ""

class SubscribeRequest(BaseModel):
    plan_id: str
    subscriber_address: str

class PaymentRequest(BaseModel):
    plan_id: str
    subscriber_address: str
    transaction_hash: str

class PlanResponse(BaseModel):
    plan_id: str
    token: str
    amount: float
    interval_days: int
    duration_days: int
    encrypted_api_url: str
    description: str
    creator: str
    active: bool
    created_at: datetime

class SubscriptionResponse(BaseModel):
    subscription_id: str
    plan_id: str
    subscriber_address: str
    start_time: datetime
    next_payment_due: datetime
    end_time: datetime
    total_paid: float
    active: bool

# Dependency for X402 authentication
async def verify_x402_payment(x_payment: Optional[str] = Header(None)):
    """Verify X402 payment header for protected endpoints"""
    if not x_payment:
        raise HTTPException(status_code=402, detail="Payment required - missing X-PAYMENT header")
    
    try:
        payment_data = X402Encryption.verify_payment_header(x_payment)
        return payment_data
    except ValueError as e:
        raise HTTPException(status_code=402, detail=f"Payment verification failed: {str(e)}")

# Startup event to initialize test data
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    initialize_test_data()
    print("SKALE Payment Tool API started successfully")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Plan management endpoints
@app.post("/plans/create", response_model=PlanResponse)
async def create_plan(
    request: CreatePlanRequest,
    payment_data: Dict = Depends(verify_x402_payment)
):
    """Create a new subscription plan with X402 protection"""
    
    # Generate unique plan ID
    plan_id = str(uuid.uuid4())
    
    # Encrypt API URL
    encrypted_url = X402Encryption.encrypt_url(request.api_url)
    
    # Extract creator from payment data (in real implementation, this would be from signature)
    creator = payment_data.get("from_address", "0x" + "0" * 40)
    
    # Create plan
    plan = {
        "plan_id": plan_id,
        "token": request.token,
        "amount": request.amount,
        "interval_days": request.interval_days,
        "duration_days": request.duration_days,
        "encrypted_api_url": encrypted_url,
        "description": request.description,
        "creator": creator,
        "active": True,
        "created_at": datetime.utcnow()
    }
    
    plans_db[plan_id] = plan
    
    return PlanResponse(**plan)

@app.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str):
    """Get plan details by ID"""
    if plan_id not in plans_db:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return PlanResponse(**plans_db[plan_id])

@app.get("/plans", response_model=List[PlanResponse])
async def list_plans(active_only: bool = True):
    """List all plans"""
    plans = list(plans_db.values())
    
    if active_only:
        plans = [plan for plan in plans if plan["active"]]
    
    return [PlanResponse(**plan) for plan in plans]

@app.put("/plans/{plan_id}/deactivate")
async def deactivate_plan(
    plan_id: str,
    payment_data: Dict = Depends(verify_x402_payment)
):
    """Deactivate a plan (only creator can do this)"""
    if plan_id not in plans_db:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan = plans_db[plan_id]
    creator = payment_data.get("from_address", "")
    
    if plan["creator"] != creator:
        raise HTTPException(status_code=403, detail="Only plan creator can deactivate")
    
    plan["active"] = False
    return {"message": "Plan deactivated successfully"}

# Subscription management endpoints
@app.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe_to_plan(
    request: SubscribeRequest,
    payment_data: Dict = Depends(verify_x402_payment)
):
    """Subscribe to a plan with payment verification"""
    
    # Check if plan exists and is active
    if request.plan_id not in plans_db:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    plan = plans_db[request.plan_id]
    if not plan["active"]:
        raise HTTPException(status_code=400, detail="Plan is not active")
    
    # Check if already subscribed
    subscription_key = f"{request.plan_id}:{request.subscriber_address}"
    if subscription_key in subscriptions_db:
        existing_sub = subscriptions_db[subscription_key]
        if existing_sub["active"]:
            raise HTTPException(status_code=400, detail="Already subscribed to this plan")
    
    # Verify payment amount matches plan
    if payment_data["amount"] < plan["amount"]:
        raise HTTPException(status_code=400, detail="Insufficient payment amount")
    
    # Create subscription
    subscription_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=plan["duration_days"])
    next_payment = start_time + timedelta(days=plan["interval_days"])
    
    subscription = {
        "subscription_id": subscription_id,
        "plan_id": request.plan_id,
        "subscriber_address": request.subscriber_address,
        "start_time": start_time,
        "next_payment_due": next_payment,
        "end_time": end_time,
        "total_paid": plan["amount"],
        "active": True
    }
    
    subscriptions_db[subscription_key] = subscription
    
    # Record payment
    payment_record = {
        "payment_id": str(uuid.uuid4()),
        "plan_id": request.plan_id,
        "subscriber_address": request.subscriber_address,
        "amount": plan["amount"],
        "timestamp": start_time,
        "transaction_hash": payment_data.get("transaction_hash", ""),
        "payment_type": "initial"
    }
    payments_db.append(payment_record)
    
    return SubscriptionResponse(**subscription)

@app.get("/subscriptions/{plan_id}/{subscriber_address}", response_model=SubscriptionResponse)
async def get_subscription(plan_id: str, subscriber_address: str):
    """Get subscription details"""
    subscription_key = f"{plan_id}:{subscriber_address}"
    
    if subscription_key not in subscriptions_db:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    return SubscriptionResponse(**subscriptions_db[subscription_key])

@app.get("/subscriptions/user/{address}", response_model=List[SubscriptionResponse])
async def get_user_subscriptions(address: str, active_only: bool = True):
    """Get all subscriptions for a user"""
    user_subscriptions = []
    
    for subscription in subscriptions_db.values():
        if subscription["subscriber_address"] == address:
            if not active_only or subscription["active"]:
                user_subscriptions.append(subscription)
    
    return [SubscriptionResponse(**sub) for sub in user_subscriptions]

@app.post("/subscriptions/{plan_id}/cancel")
async def cancel_subscription(
    plan_id: str,
    payment_data: Dict = Depends(verify_x402_payment)
):
    """Cancel a subscription"""
    subscriber_address = payment_data.get("from_address", "")
    subscription_key = f"{plan_id}:{subscriber_address}"
    
    if subscription_key not in subscriptions_db:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription = subscriptions_db[subscription_key]
    if subscription["subscriber_address"] != subscriber_address:
        raise HTTPException(status_code=403, detail="Can only cancel your own subscription")
    
    subscription["active"] = False
    return {"message": "Subscription cancelled successfully"}

# Payment processing endpoints
@app.post("/payments/process")
async def process_recurring_payment(
    request: PaymentRequest,
    payment_data: Dict = Depends(verify_x402_payment)
):
    """Process a recurring payment"""
    subscription_key = f"{request.plan_id}:{request.subscriber_address}"
    
    if subscription_key not in subscriptions_db:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription = subscriptions_db[subscription_key]
    plan = plans_db[request.plan_id]
    
    # Check if payment is due
    if datetime.utcnow() < subscription["next_payment_due"]:
        raise HTTPException(status_code=400, detail="Payment not due yet")
    
    # Check if subscription is still active and not expired
    if not subscription["active"] or datetime.utcnow() > subscription["end_time"]:
        raise HTTPException(status_code=400, detail="Subscription is not active or expired")
    
    # Verify payment amount
    if payment_data["amount"] < plan["amount"]:
        raise HTTPException(status_code=400, detail="Insufficient payment amount")
    
    # Update subscription
    subscription["next_payment_due"] += timedelta(days=plan["interval_days"])
    subscription["total_paid"] += plan["amount"]
    
    # Record payment
    payment_record = {
        "payment_id": str(uuid.uuid4()),
        "plan_id": request.plan_id,
        "subscriber_address": request.subscriber_address,
        "amount": plan["amount"],
        "timestamp": datetime.utcnow(),
        "transaction_hash": request.transaction_hash,
        "payment_type": "recurring"
    }
    payments_db.append(payment_record)
    
    return {"message": "Payment processed successfully", "next_payment_due": subscription["next_payment_due"]}

@app.get("/payments/history/{address}")
async def get_payment_history(address: str):
    """Get payment history for an address"""
    user_payments = [
        payment for payment in payments_db 
        if payment["subscriber_address"] == address
    ]
    
    return {"payments": user_payments}

# API access verification endpoint
@app.get("/verify-access/{plan_id}")
async def verify_api_access(
    plan_id: str,
    subscriber_address: str,
    payment_data: Dict = Depends(verify_x402_payment)
):
    """Verify if subscriber has active access to API"""
    subscription_key = f"{plan_id}:{subscriber_address}"
    
    if subscription_key not in subscriptions_db:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    subscription = subscriptions_db[subscription_key]
    plan = plans_db[plan_id]
    
    # Check subscription status
    is_active = (
        subscription["active"] and 
        datetime.utcnow() <= subscription["end_time"] and
        datetime.utcnow() < subscription["next_payment_due"]
    )
    
    if not is_active:
        raise HTTPException(status_code=402, detail="Subscription expired or payment overdue")
    
    # Decrypt API URL
    try:
        api_url = X402Encryption.decrypt_url(plan["encrypted_api_url"])
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to decrypt API URL")
    
    return {
        "access_granted": True,
        "api_url": api_url,
        "subscription_expires": subscription["end_time"],
        "next_payment_due": subscription["next_payment_due"]
    }

# Development endpoints (remove in production)
@app.get("/dev/plans")
async def dev_list_all_plans():
    """Development endpoint to list all plans without authentication"""
    return {"plans": list(plans_db.values())}

@app.get("/dev/subscriptions")
async def dev_list_all_subscriptions():
    """Development endpoint to list all subscriptions without authentication"""
    return {"subscriptions": list(subscriptions_db.values())}

@app.get("/dev/payments")
async def dev_list_all_payments():
    """Development endpoint to list all payments without authentication"""
    return {"payments": payments_db}

@app.post("/dev/reset")
async def dev_reset_data():
    """Development endpoint to reset all data"""
    global plans_db, subscriptions_db, payments_db
    plans_db.clear()
    subscriptions_db.clear()
    payments_db.clear()
    initialize_test_data()
    return {"message": "Data reset successfully"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SKALE Payment Tool API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

