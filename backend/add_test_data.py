import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skale_payments.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Plan(Base):
    __tablename__ = "plans"
    
    plan_id = Column(String, primary_key=True)
    contract_plan_id = Column(String, unique=True, nullable=False)
    token = Column(String, nullable=False)
    amount = Column(Float, nullable=False)  # Changed to Float for SQLite
    interval_seconds = Column(Integer, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    grace_period_seconds = Column(Integer, nullable=False)
    encrypted_api_url = Column(String, nullable=False)
    description = Column(String)
    creator = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

print("Adding test data to database...\n")

db = SessionLocal()

# Create test plans - using smaller numbers for SQLite
plans_data = [
    {
        "description": "Basic Monthly Plan",
        "amount": 0.5,
        "interval_days": 30,
        "duration_days": 365
    },
    {
        "description": "Premium Monthly Plan", 
        "amount": 1.5,
        "interval_days": 30,
        "duration_days": 365
    },
    {
        "description": "Enterprise Yearly Plan",
        "amount": 15.0,
        "interval_days": 365,
        "duration_days": 365
    }
]

for plan_data in plans_data:
    test_plan = Plan(
        plan_id=str(uuid.uuid4()),
        contract_plan_id="0x" + uuid.uuid4().hex + uuid.uuid4().hex[:32],
        token="0x0000000000000000000000000000000000000000",
        amount=plan_data["amount"],  # Store as ETH, not wei
        interval_seconds=plan_data["interval_days"] * 86400,
        duration_seconds=plan_data["duration_days"] * 86400,
        grace_period_seconds=259200,
        encrypted_api_url=f"https://api.example.com/{plan_data['description'].lower().replace(' ', '-')}",
        description=plan_data["description"],
        creator="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        active=True
    )
    
    db.add(test_plan)
    print(f"✅ Created: {plan_data['description']} - {plan_data['amount']} ETH")

db.commit()
db.close()

print("\n🎉 Test data added successfully!")
print("\nTest with:")
print("  curl http://localhost:8000/plans")
print("  curl http://localhost:8000/admin/stats")
