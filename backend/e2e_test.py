#!/usr/bin/env python3
"""
End-to-End Test for SKALE Payment Tool
Tests the complete flow: Contract → Backend → Signatures
"""

import requests
import json
from web3 import Web3
from eth_account import Account
from eip712_utils import EIP712Signer
import time

# Configuration
API_URL = "http://localhost:8000"
RPC_URL = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
CHAIN_ID = 31337

# Anvil test accounts
TEST_ACCOUNTS = {
    "deployer": {
        "address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        "key": "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    },
    "subscriber": {
        "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
        "key": "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
    }
}

# ABI for contract interaction
CONTRACT_ABI = [
    {
        "inputs": [],
        "name": "planCounter",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "getNonce",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getDomainSeparator",
        "outputs": [{"name": "", "type": "bytes32"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

# Test 1: Check Services
print_section("Step 1: Verify All Services Running")

try:
    # Check API
    resp = requests.get(f"{API_URL}/health", timeout=2)
    if resp.status_code == 200:
        health = resp.json()
        print_success("Backend API is running")
        print_info(f"   Blockchain connected: {health.get('blockchain_connected')}")
    else:
        print_error("API returned non-200 status")
        exit(1)
except Exception as e:
    print_error(f"Cannot connect to API: {e}")
    print_info("Make sure API is running: cd backend && python main.py")
    exit(1)

try:
    # Check Blockchain
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if w3.is_connected():
        block = w3.eth.block_number
        print_success(f"Blockchain connected (Block: {block})")
    else:
        print_error("Cannot connect to blockchain")
        exit(1)
except Exception as e:
    print_error(f"Blockchain connection failed: {e}")
    print_info("Make sure Anvil is running: anvil")
    exit(1)

# Test 2: Check Contract
print_section("Step 2: Verify Smart Contract")

try:
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    plan_counter = contract.functions.planCounter().call()
    print_success(f"Contract deployed at {CONTRACT_ADDRESS}")
    print_info(f"   Plan counter: {plan_counter}")
    
    # Get domain separator
    domain_separator = contract.functions.getDomainSeparator().call()
    print_info(f"   Domain separator: {domain_separator.hex()[:20]}...")
except Exception as e:
    print_error(f"Contract interaction failed: {e}")
    print_info("Make sure contract is deployed")
    exit(1)

# Test 3: Check Database
print_section("Step 3: Check Database & API")

try:
    resp = requests.get(f"{API_URL}/admin/stats")
    stats = resp.json()
    print_success("Database connected")
    print_info(f"   Total plans: {stats['total_plans']}")
    print_info(f"   Active subscriptions: {stats['active_subscriptions']}")
    
    # Get plans
    resp = requests.get(f"{API_URL}/plans")
    plans = resp.json()
    if len(plans) > 0:
        print_success(f"Found {len(plans)} test plans in database")
        for plan in plans[:3]:
            print_info(f"   - {plan['description']}: {plan['amount']} ETH")
    else:
        print_info("No plans in database yet")
except Exception as e:
    print_error(f"Database check failed: {e}")
    exit(1)

# Test 4: EIP-712 Signature Creation
print_section("Step 4: Test EIP-712 Signature Creation")

try:
    signer = EIP712Signer(CONTRACT_ADDRESS, CHAIN_ID)
    subscriber_account = Account.from_key(TEST_ACCOUNTS["subscriber"]["key"])
    
    print_info(f"Test subscriber: {subscriber_account.address}")
    
    # Get nonce from contract
    nonce = contract.functions.getNonce(subscriber_account.address).call()
    print_info(f"Current nonce: {nonce}")
    
    # Create test subscription data
    plan_id = "0x" + "a" * 64  # Test plan ID
    amount_wei = Web3.to_wei(1.5, 'ether')
    deadline = int(time.time()) + 300  # 5 minutes
    
    # Sign subscription
    signature = signer.sign_subscription(
        TEST_ACCOUNTS["subscriber"]["key"],
        plan_id,
        subscriber_account.address,
        amount_wei,
        deadline,
        nonce,
        True  # auto_renew
    )
    
    print_success("EIP-712 signature created")
    print_info(f"   Signature: {signature[:20]}...")
    print_info(f"   Deadline: {deadline}")
    print_info(f"   Amount: 1.5 ETH")
    
    # Verify signature locally
    is_valid = signer.verify_subscription_signature(
        plan_id,
        subscriber_account.address,
        amount_wei,
        deadline,
        nonce,
        True,
        signature
    )
    
    if is_valid:
        print_success("Signature verified locally")
    else:
        print_error("Signature verification failed")
        exit(1)
        
except Exception as e:
    print_error(f"EIP-712 test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 5: Account Balances
print_section("Step 5: Check Account Balances")

for name, account in TEST_ACCOUNTS.items():
    balance = w3.eth.get_balance(account["address"])
    balance_eth = w3.from_wei(balance, 'ether')
    print_info(f"{name.capitalize()}: {balance_eth} ETH")

# Summary
print_section("✅ End-to-End Test Summary")

print_success("All systems operational!")
print()
print("Components tested:")
print("  ✅ Backend API")
print("  ✅ SQLite Database")
print("  ✅ Anvil Blockchain")
print("  ✅ Smart Contract")
print("  ✅ EIP-712 Signatures")
print()
print("🎉 Ready for full integration testing!")
print()
print("Next steps:")
print("  1. Open http://localhost:8000/docs to explore API")
print("  2. Use the test accounts above for transactions")
print("  3. Check contract on Anvil for on-chain state")
print()
print("Test accounts:")
print(f"  Deployer:   {TEST_ACCOUNTS['deployer']['address']}")
print(f"  Subscriber: {TEST_ACCOUNTS['subscriber']['address']}")
print()
