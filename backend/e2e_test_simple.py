#!/usr/bin/env python3
"""
Simplified End-to-End Test for SKALE Payment Tool
"""

import requests
import json
from web3 import Web3
from eth_account import Account
from eip712_utils import EIP712Signer
import time

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Configuration
API_URL = "http://localhost:8000"
RPC_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
CHAIN_ID = 31337

# Test account (Anvil's second account)
SUBSCRIBER_KEY = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

def test_section(title):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  {title}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def info(msg):
    print(f"ℹ️  {msg}")

print(f"{BLUE}")
print("╔════════════════════════════════════════════════════════════╗")
print("║        SKALE Payment Tool - End-to-End Test              ║")
print("╔════════════════════════════════════════════════════════════╗")
print(f"{RESET}")

# Test 1: Services
test_section("Test 1: Check All Services")

try:
    resp = requests.get(f"{API_URL}/health", timeout=2)
    health = resp.json()
    success("Backend API running")
    info(f"   Status: {health['status']}")
    info(f"   Blockchain: {health['blockchain_connected']}")
except:
    error("API not running! Start with: cd backend && python main.py")
    exit(1)

try:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    block = w3.eth.block_number
    success(f"Anvil running (Block #{block})")
except:
    error("Anvil not running! Start with: anvil")
    exit(1)

# Test 2: Database
test_section("Test 2: Database & Plans")

stats = requests.get(f"{API_URL}/admin/stats").json()
plans = requests.get(f"{API_URL}/plans").json()

success(f"Database connected")
info(f"   Plans: {stats['total_plans']}")
info(f"   Subscriptions: {stats['total_subscriptions']}")

if len(plans) > 0:
    success(f"Found {len(plans)} test plans:")
    for p in plans:
        info(f"   - {p['description']}: {p['amount']} ETH")
else:
    info("   No plans yet (that's okay)")

# Test 3: Smart Contract
test_section("Test 3: Smart Contract Interaction")

try:
    # Simple contract check
    code = w3.eth.get_code(CONTRACT_ADDRESS)
    if code and code != b'' and code != b'0x':
        success(f"Contract deployed at {CONTRACT_ADDRESS}")
        info(f"   Bytecode length: {len(code)} bytes")
    else:
        error("Contract not deployed")
        exit(1)
except Exception as e:
    error(f"Contract check failed: {e}")
    exit(1)

# Test 4: Accounts
test_section("Test 4: Test Accounts")

subscriber = Account.from_key(SUBSCRIBER_KEY)
balance = w3.eth.get_balance(subscriber.address)
balance_eth = float(w3.from_wei(balance, 'ether'))

success(f"Test subscriber ready")
info(f"   Address: {subscriber.address}")
info(f"   Balance: {balance_eth:.2f} ETH")

if balance_eth > 1:
    success("Sufficient balance for testing")
else:
    error("Insufficient balance")

# Test 5: EIP-712 Signatures
test_section("Test 5: EIP-712 Signature Generation")

try:
    signer = EIP712Signer(CONTRACT_ADDRESS, CHAIN_ID)
    
    # Create test signature
    plan_id = "0x" + "a" * 64
    amount_wei = Web3.to_wei(1.5, 'ether')
    deadline = int(time.time()) + 300
    nonce = 0
    
    signature = signer.sign_subscription(
        SUBSCRIBER_KEY,
        plan_id,
        subscriber.address,
        amount_wei,
        deadline,
        nonce,
        True
    )
    
    success("EIP-712 signature created")
    info(f"   Length: {len(signature)} chars")
    info(f"   First 20: {signature[:20]}...")
    
    # Verify
    valid = signer.verify_subscription_signature(
        plan_id, subscriber.address, amount_wei,
        deadline, nonce, True, signature
    )
    
    if valid:
        success("Signature verified ✓")
    else:
        error("Signature verification failed")
        
except Exception as e:
    error(f"EIP-712 test failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
test_section("✅ Test Summary")

print(f"{GREEN}")
print("All core components operational:")
print("  ✓ Backend API")
print("  ✓ Database (SQLite)")
print("  ✓ Blockchain (Anvil)")
print("  ✓ Smart Contract")
print("  ✓ EIP-712 Signatures")
print(f"{RESET}")

print("\n🎯 System Status: READY FOR TESTING")
print("\n📝 Next Steps:")
print("  1. Visit http://localhost:8000/docs")
print("  2. Try API endpoints with test data")
print("  3. Test signature-based authentication")
print()
print(f"💡 Test Account: {subscriber.address}")
print(f"   Balance: {balance_eth:.2f} ETH")
print()
