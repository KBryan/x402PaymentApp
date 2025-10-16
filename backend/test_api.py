"""
Test script for SKALE Payment Tool API
Tests basic functionality without X402 authentication
"""

import requests
import json
import base64
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def create_test_payment_header():
    """Create a test X-PAYMENT header"""
    payment_data = {
        "amount": 100.0,
        "token": "native",
        "signature": "0x" + "a" * 130,  # Mock signature
        "timestamp": datetime.utcnow().isoformat(),
        "from_address": "0x" + "1" * 40,
        "transaction_hash": "0x" + "b" * 64
    }
    
    payload = base64.b64encode(json.dumps(payment_data).encode()).decode()
    return payload

def test_health_check():
    """Test health check endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.status_code} - {response.json()}")
    return response.status_code == 200

def test_create_plan():
    """Test plan creation"""
    headers = {"X-PAYMENT": create_test_payment_header()}
    
    plan_data = {
        "token": "native",
        "amount": 100.0,
        "interval_days": 30,
        "duration_days": 365,
        "api_url": "https://api.example.com/protected",
        "description": "Test subscription plan"
    }
    
    response = requests.post(f"{BASE_URL}/plans/create", json=plan_data, headers=headers)
    print(f"Create Plan: {response.status_code}")
    
    if response.status_code == 200:
        plan = response.json()
        print(f"Created plan ID: {plan['plan_id']}")
        return plan['plan_id']
    else:
        print(f"Error: {response.text}")
        return None

def test_list_plans():
    """Test listing plans"""
    response = requests.get(f"{BASE_URL}/dev/plans")
    print(f"List Plans: {response.status_code}")
    
    if response.status_code == 200:
        plans = response.json()
        print(f"Found {len(plans['plans'])} plans")
        return plans['plans']
    else:
        print(f"Error: {response.text}")
        return []

def test_subscribe_to_plan(plan_id):
    """Test subscribing to a plan"""
    headers = {"X-PAYMENT": create_test_payment_header()}
    
    subscribe_data = {
        "plan_id": plan_id,
        "subscriber_address": "0x" + "2" * 40
    }
    
    response = requests.post(f"{BASE_URL}/subscribe", json=subscribe_data, headers=headers)
    print(f"Subscribe: {response.status_code}")
    
    if response.status_code == 200:
        subscription = response.json()
        print(f"Created subscription ID: {subscription['subscription_id']}")
        return subscription
    else:
        print(f"Error: {response.text}")
        return None

def test_get_subscription(plan_id, subscriber_address):
    """Test getting subscription details"""
    response = requests.get(f"{BASE_URL}/subscriptions/{plan_id}/{subscriber_address}")
    print(f"Get Subscription: {response.status_code}")
    
    if response.status_code == 200:
        subscription = response.json()
        print(f"Subscription active: {subscription['active']}")
        return subscription
    else:
        print(f"Error: {response.text}")
        return None

def test_verify_access(plan_id, subscriber_address):
    """Test API access verification"""
    headers = {"X-PAYMENT": create_test_payment_header()}
    
    response = requests.get(
        f"{BASE_URL}/verify-access/{plan_id}",
        params={"subscriber_address": subscriber_address},
        headers=headers
    )
    print(f"Verify Access: {response.status_code}")
    
    if response.status_code == 200:
        access_info = response.json()
        print(f"Access granted: {access_info['access_granted']}")
        print(f"API URL: {access_info['api_url']}")
        return access_info
    else:
        print(f"Error: {response.text}")
        return None

def run_tests():
    """Run all tests"""
    print("=== SKALE Payment Tool API Tests ===\n")
    
    # Test health check
    if not test_health_check():
        print("Health check failed, stopping tests")
        return
    
    print()
    
    # Test plan creation
    plan_id = test_create_plan()
    if not plan_id:
        print("Plan creation failed, stopping tests")
        return
    
    print()
    
    # Test listing plans
    plans = test_list_plans()
    print()
    
    # Test subscription
    subscriber_address = "0x" + "2" * 40
    subscription = test_subscribe_to_plan(plan_id)
    if not subscription:
        print("Subscription failed, stopping tests")
        return
    
    print()
    
    # Test getting subscription
    test_get_subscription(plan_id, subscriber_address)
    print()
    
    # Test access verification
    test_verify_access(plan_id, subscriber_address)
    print()
    
    print("=== All tests completed ===")

if __name__ == "__main__":
    run_tests()

