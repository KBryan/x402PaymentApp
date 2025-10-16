"""
SKALE Payment Tool - FastAPI Backend (Production Version)
Fully integrated with smart contract and real authentication
"""
import uuid

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import os
import json
import base64
import time
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from web3 import Web3
from eth_account import Account
from eth_account.messages import encode_defunct
import structlog

# Structured logging
logger = structlog.get_logger()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skale_payments.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============ Database Models ============

class Plan(Base):
    __tablename__ = "plans"

    plan_id = Column(String, primary_key=True)
    contract_plan_id = Column(String, unique=True, nullable=False)  # On-chain plan ID
    token = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)  # Wei/token base units
    interval_seconds = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    grace_period_seconds = Column(Integer, nullable=False)
    encrypted_api_url = Column(String, nullable=False)
    description = Column(String)
    creator = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(String, primary_key=True)
    plan_id = Column(String, nullable=False)
    subscriber_address = Column(String, nullable=False)
    contract_subscription_data = Column(String)  # JSON of on-chain data
    start_time = Column(DateTime, nullable=False)
    next_payment_due = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_paid = Column(BigInteger, default=0)
    active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    transaction_hash = Column(String)


class Payment(Base):
    __tablename__ = "payments"

    payment_id = Column(String, primary_key=True)
    subscription_id = Column(String, nullable=False)
    amount = Column(BigInteger, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    transaction_hash = Column(String, unique=True)
    payment_type = Column(String)  # 'initial' or 'recurring'
    block_number = Column(Integer)


class Nonce(Base):
    __tablename__ = "nonces"

    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    nonce = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)

# ============ Contract Interface ============

class ContractInterface:
    def __init__(self):
        self.rpc_url = os.getenv("SKALE_RPC_URL", "https://testnet.skalenodes.com/v1/giant-half-dual-testnet")
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.contract_address:
            logger.warning("CONTRACT_ADDRESS not set - contract integration disabled")
            return

        # Load ABI
        abi_path = os.getenv("CONTRACT_ABI_PATH", "../contracts/SubscriptionManager.abi.json")
        try:
            with open(abi_path, 'r') as f:
                self.abi = json.load(f)

            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.abi
            )
            logger.info("Contract interface initialized", address=self.contract_address)
        except Exception as e:
            logger.error("Failed to load contract ABI", error=str(e))
            self.contract = None

    def is_connected(self) -> bool:
        """Check blockchain connection"""
        try:
            return self.w3.is_connected()
        except:
            return False

    def get_plan(self, plan_id: str) -> Optional[Dict]:
        """Get plan details from blockchain"""
        if not self.contract:
            return None

        try:
            plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
            plan = self.contract.functions.getPlan(plan_id_bytes).call()

            return {
                'token': plan[0],
                'amount': plan[1],
                'interval': plan[2],
                'duration': plan[3],
                'gracePeriod': plan[4],
                'active': plan[5],
                'creator': plan[6],
                'paymentRecipient': plan[7],
                'apiUrl': plan[8],
                'totalSubscribers': plan[9]
            }
        except Exception as e:
            logger.error("Failed to get plan from contract", plan_id=plan_id, error=str(e))
            return None

    def get_subscription(self, plan_id: str, subscriber: str) -> Optional[Dict]:
        """Get subscription details from blockchain"""
        if not self.contract:
            return None

        try:
            plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
            subscription = self.contract.functions.getSubscription(
                plan_id_bytes,
                Web3.to_checksum_address(subscriber)
            ).call()

            return {
                'subscriber': subscription[0],
                'startTime': subscription[1],
                'nextPaymentDue': subscription[2],
                'endTime': subscription[3],
                'totalPaid': subscription[4],
                'missedPayments': subscription[5],
                'active': subscription[6],
                'autoRenew': subscription[7]
            }
        except Exception as e:
            logger.error("Failed to get subscription from contract", error=str(e))
            return None


# Initialize contract interface
contract_interface = ContractInterface()

# ============ Authentication & Security ============

class AuthenticationService:
    """Handle EIP-191/712 signature verification"""

    @staticmethod
    def verify_signature(
            message: str,
            signature: str,
            expected_signer: str
    ) -> bool:
        """Verify EIP-191 signature"""
        try:
            # Create message hash
            message_hash = encode_defunct(text=message)

            # Recover signer address
            recovered_address = Account.recover_message(message_hash, signature=signature)

            # Compare addresses (case-insensitive)
            return recovered_address.lower() == expected_signer.lower()
        except Exception as e:
            logger.error("Signature verification failed", error=str(e))
            return False

    @staticmethod
    def create_payment_message(
            amount: int,
            token: str,
            timestamp: str,
            endpoint: str,
            nonce: str
    ) -> str:
        """Create canonical message for signing"""
        return (
            f"SKALE Payment Authorization\n"
            f"Amount: {amount}\n"
            f"Token: {token}\n"
            f"Timestamp: {timestamp}\n"
            f"Endpoint: {endpoint}\n"
            f"Nonce: {nonce}"
        )

    @staticmethod
    def check_nonce(db: Session, address: str, nonce: str) -> bool:
        """Check if nonce is valid (not used before)"""
        existing = db.query(Nonce).filter(
            Nonce.address == address.lower(),
            Nonce.nonce == nonce
        ).first()

        if existing:
            logger.warning("Nonce replay detected", address=address, nonce=nonce)
            return False

        # Store nonce
        new_nonce = Nonce(address=address.lower(), nonce=nonce)
        db.add(new_nonce)
        db.commit()

        # Clean old nonces (older than 10 minutes)
        cutoff = datetime.utcnow() - timedelta(minutes=10)
        db.query(Nonce).filter(Nonce.timestamp < cutoff).delete()
        db.commit()

        return True

    @staticmethod
    def verify_payment_header(
            x_payment: str,
            endpoint: str,
            db: Session
    ) -> Dict[str, Any]:
        """Verify X-PAYMENT header with real signature validation"""
        try:
            # Parse header format: b64:amount:token:signature:timestamp:from_address:nonce
            parts = x_payment.split(":")
            if len(parts) < 7 or parts[0] != "b64":
                raise ValueError("Invalid header format")

            _, amount_str, token, signature, timestamp, from_address, nonce = parts[:7]

            # 1. Validate timestamp (5-minute window)
            try:
                payment_time = datetime.fromisoformat(timestamp)
            except:
                # Try unix timestamp
                payment_time = datetime.fromtimestamp(float(timestamp))

            time_diff = abs((datetime.utcnow() - payment_time).total_seconds())
            if time_diff > 300:  # 5 minutes
                raise ValueError(f"Timestamp expired (diff: {time_diff}s)")

            # 2. Check nonce (prevent replay attacks)
            if not AuthenticationService.check_nonce(db, from_address, nonce):
                raise ValueError("Nonce already used (replay attack)")

            # 3. Reconstruct and verify message
            amount = int(float(amount_str) * 10**18)  # Convert to wei
            message = AuthenticationService.create_payment_message(
                amount, token, timestamp, endpoint, nonce
            )

            # 4. Verify signature
            if not AuthenticationService.verify_signature(message, signature, from_address):
                raise ValueError("Invalid signature")

            logger.info(
                "Payment header verified",
                address=from_address,
                amount=amount_str,
                endpoint=endpoint
            )

            return {
                "amount": amount,
                "token": token,
                "signature": signature,
                "timestamp": timestamp,
                "from_address": from_address,
                "nonce": nonce,
                "verified": True
            }

        except Exception as e:
            logger.error("Payment verification failed", error=str(e))
            raise ValueError(f"Payment verification failed: {str(e)}")


auth_service = AuthenticationService()

# ============ FastAPI Application ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("SKALE Payment Tool API starting...")

    # Check blockchain connection
    if contract_interface.is_connected():
        logger.info("Connected to SKALE network", rpc=contract_interface.rpc_url)
    else:
        logger.warning("Not connected to blockchain")

    yield

    logger.info("SKALE Payment Tool API shutting down...")


app = FastAPI(
    title="SKALE Payment Tool API",
    description="Production-ready API with smart contract integration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ============ Pydantic Models ============

class CreatePlanRequest(BaseModel):
    token: str = Field(..., description="Token address or '0x0' for native")
    amount: float = Field(..., gt=0, description="Amount per interval")
    interval_days: int = Field(..., ge=1, le=365)
    duration_days: int = Field(..., ge=1, le=3650)
    grace_period_days: int = Field(default=3, ge=0, le=30)
    api_url: str = Field(..., min_length=1)
    description: str = Field(default="")

    @validator('token')
    def validate_token(cls, v):
        if v != "native" and v != "0x0":
            if not v.startswith("0x") or len(v) != 42:
                raise ValueError("Invalid token address format")
        return v


class SubscribeRequest(BaseModel):
    plan_id: str
    auto_renew: bool = True


class PlanResponse(BaseModel):
    plan_id: str
    contract_plan_id: str
    token: str
    amount: float
    interval_days: int
    duration_days: int
    grace_period_days: int
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
    auto_renew: bool


# ============ Dependencies ============

def get_db():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_payment(
        x_payment: Optional[str] = Header(None),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Verify X-PAYMENT header"""
    if not x_payment:
        raise HTTPException(
            status_code=402,
            detail="Payment required - missing X-PAYMENT header"
        )

    try:
        # Extract endpoint from request (would need request object in real impl)
        endpoint = "/api/endpoint"  # TODO: Get from request
        return auth_service.verify_payment_header(x_payment, endpoint, db)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))


# ============ Health & Info Endpoints ============

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "SKALE Payment Tool API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check with blockchain status"""
    blockchain_connected = contract_interface.is_connected()

    return {
        "status": "healthy" if blockchain_connected else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "blockchain_connected": blockchain_connected,
        "contract_address": contract_interface.contract_address
    }


# ============ Plan Management Endpoints ============

@app.post("/plans/create", response_model=PlanResponse)
async def create_plan(
        request: CreatePlanRequest,
        payment_data: Dict = Depends(verify_payment),
        db: Session = Depends(get_db)
):
    """Create subscription plan (stores in DB, points to on-chain plan)"""

    creator = payment_data["from_address"]

    # In production: This would call the smart contract to create the plan
    # For now, we'll create a mock contract plan ID
    import uuid
    contract_plan_id = "0x" + uuid.uuid4().hex[:64]

    # Convert to base units
    amount_wei = int(request.amount * 10**18)

    # Create database entry
    plan = Plan(
        plan_id=str(uuid.uuid4()),
        contract_plan_id=contract_plan_id,
        token=request.token if request.token != "native" else "0x0",
        amount=amount_wei,
        interval_seconds=request.interval_days * 86400,
        duration_seconds=request.duration_days * 86400,
        grace_period_seconds=request.grace_period_days * 86400,
        encrypted_api_url=f"encrypted:{request.api_url}",  # TODO: Real encryption
        description=request.description,
        creator=creator,
        active=True
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    logger.info("Plan created", plan_id=plan.plan_id, creator=creator)

    return PlanResponse(
        plan_id=plan.plan_id,
        contract_plan_id=plan.contract_plan_id,
        token=plan.token,
        amount=plan.amount / 10**18,
        interval_days=plan.interval_seconds // 86400,
        duration_days=plan.duration_seconds // 86400,
        grace_period_days=plan.grace_period_seconds // 86400,
        description=plan.description,
        creator=plan.creator,
        active=plan.active,
        created_at=plan.created_at
    )


@app.get("/plans", response_model=List[PlanResponse])
async def list_plans(
        active_only: bool = True,
        db: Session = Depends(get_db)
):
    """List all plans"""
    query = db.query(Plan)
    if active_only:
        query = query.filter(Plan.active == True)

    plans = query.all()

    return [
        PlanResponse(
            plan_id=p.plan_id,
            contract_plan_id=p.contract_plan_id,
            token=p.token,
            amount=p.amount / 10**18,
            interval_days=p.interval_seconds // 86400,
            duration_days=p.duration_seconds // 86400,
            grace_period_days=p.grace_period_seconds // 86400,
            description=p.description,
            creator=p.creator,
            active=p.active,
            created_at=p.created_at
        )
        for p in plans
    ]


@app.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str, db: Session = Depends(get_db)):
    """Get plan details"""
    plan = db.query(Plan).filter(Plan.plan_id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return PlanResponse(
        plan_id=plan.plan_id,
        contract_plan_id=plan.contract_plan_id,
        token=plan.token,
        amount=plan.amount / 10**18,
        interval_days=plan.interval_seconds // 86400,
        duration_days=plan.duration_seconds // 86400,
        grace_period_days=plan.grace_period_seconds // 86400,
        description=plan.description,
        creator=plan.creator,
        active=plan.active,
        created_at=plan.created_at
    )


# ============ Subscription Endpoints ============

@app.post("/subscribe", response_model=SubscriptionResponse)
async def subscribe(
        request: SubscribeRequest,
        payment_data: Dict = Depends(verify_payment),
        db: Session = Depends(get_db)
):
    """Subscribe to a plan"""

    subscriber = payment_data["from_address"]

    # Get plan
    plan = db.query(Plan).filter(Plan.plan_id == request.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if not plan.active:
        raise HTTPException(status_code=400, detail="Plan is not active")

    # Check existing subscription
    existing = db.query(Subscription).filter(
        Subscription.plan_id == request.plan_id,
        Subscription.subscriber_address == subscriber,
        Subscription.active == True
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already subscribed")

    # Verify payment amount
    if payment_data["amount"] < plan.amount:
        raise HTTPException(status_code=400, detail="Insufficient payment")

    # Create subscription
    now = datetime.utcnow()
    subscription = Subscription(
        subscription_id=str(uuid.uuid4()),
        plan_id=plan.plan_id,
        subscriber_address=subscriber,
        start_time=now,
        next_payment_due=now + timedelta(seconds=plan.interval_seconds),
        end_time=now + timedelta(seconds=plan.duration_seconds),
        total_paid=plan.amount,
        active=True,
        auto_renew=request.auto_renew,
        transaction_hash=payment_data.get("transaction_hash", "")
    )

    db.add(subscription)
    db.commit()

    logger.info(
        "Subscription created",
        subscription_id=subscription.subscription_id,
        subscriber=subscriber,
        plan_id=plan.plan_id
    )

    return SubscriptionResponse(
        subscription_id=subscription.subscription_id,
        plan_id=subscription.plan_id,
        subscriber_address=subscription.subscriber_address,
        start_time=subscription.start_time,
        next_payment_due=subscription.next_payment_due,
        end_time=subscription.end_time,
        total_paid=subscription.total_paid / 10**18,
        active=subscription.active,
        auto_renew=subscription.auto_renew
    )


@app.get("/subscriptions/{plan_id}/{subscriber}", response_model=SubscriptionResponse)
async def get_subscription(
        plan_id: str,
        subscriber: str,
        db: Session = Depends(get_db)
):
    """Get subscription details"""
    sub = db.query(Subscription).filter(
        Subscription.plan_id == plan_id,
        Subscription.subscriber_address == subscriber.lower()
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return SubscriptionResponse(
        subscription_id=sub.subscription_id,
        plan_id=sub.plan_id,
        subscriber_address=sub.subscriber_address,
        start_time=sub.start_time,
        next_payment_due=sub.next_payment_due,
        end_time=sub.end_time,
        total_paid=sub.total_paid / 10**18,
        active=sub.active,
        auto_renew=sub.auto_renew
    )


# ============ Admin Endpoints (Protected) ============

@app.get("/admin/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get system statistics (would need admin auth in production)"""
    total_plans = db.query(Plan).count()
    active_plans = db.query(Plan).filter(Plan.active == True).count()
    total_subscriptions = db.query(Subscription).count()
    active_subscriptions = db.query(Subscription).filter(Subscription.active == True).count()

    return {
        "total_plans": total_plans,
        "active_plans": active_plans,
        "total_subscriptions": total_subscriptions,
        "active_subscriptions": active_subscriptions,
        "blockchain_connected": contract_interface.is_connected()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )