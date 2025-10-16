from eip712_utils import EIP712Signer
from eth_account import Account
from web3 import Web3
import requests
import time

# Configuration
API_URL = "http://localhost:8000"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
CHAIN_ID = 31337

# Test account (Anvil's first account)
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

def create_test_plan():
    print("Creating test plan with EIP-712 signature...\n")
    
    # Initialize signer
    signer = EIP712Signer(CONTRACT_ADDRESS, CHAIN_ID)
    account = Account.from_key(PRIVATE_KEY)
    
    print(f"Using account: {account.address}")
    
    # Create payment signature
    amount_wei = Web3.to_wei(0.01, 'ether')
    deadline = int(time.time()) + 300
    
    signature = signer.sign_payment(
        PRIVATE_KEY,
        account.address,
        "0x0000000000000000000000000000000000000000",  # Native token
        amount_wei,
        deadline,
        0,  # Nonce
        "create_plan"
    )
    
    print(f"Signature created: {signature[:20]}...\n")
    
    # Format: b64:amount:token:signature:timestamp:from_address:nonce
    # IMPORTANT: amount should be a number, not the signature!
    payment_header = f"b64:0.01:0x0:{signature}:{int(time.time())}:{account.address}:test-nonce"
    
    print(f"Payment header: {payment_header[:50]}...\n")
    
    # Create plan data
    plan_data = {
        "token": "native",
        "amount": 1.5,
        "interval_days": 30,
        "duration_days": 365,
        "grace_period_days": 3,
        "api_url": "https://api.example.com/premium",
        "description": "Premium Monthly Subscription"
    }
    
    try:
        response = requests.post(
            f"{API_URL}/plans/create",
            json=plan_data,
            headers={"X-PAYMENT": payment_header}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        if response.status_code == 200:
            print("✅ Plan created successfully!")
        else:
            print("⚠️  Plan creation failed (expected - needs full signature verification)")
    except Exception as e:
        print(f"Error: {e}\n")
    
    # Check plans list
    response = requests.get(f"{API_URL}/plans")
    plans = response.json()
    print(f"\nTotal plans now: {len(plans)}")
    
    if len(plans) > 0:
        print("\nPlans:")
        for plan in plans:
            print(f"  - {plan['description']}: {plan['amount']} ETH/{plan['interval_days']} days")

if __name__ == "__main__":
    create_test_plan()
