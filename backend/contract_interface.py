"""
Smart Contract Interface for SKALE Payment Tool
Handles interaction with the SubscriptionManager contract
"""

from web3 import Web3
from eth_account import Account
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class SubscriptionManagerInterface:
    def __init__(self, web3_provider_url: str, contract_address: str, contract_abi: List[Dict]):
        """Initialize contract interface"""
        self.w3 = Web3(Web3.HTTPProvider(web3_provider_url))
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=contract_abi)
        
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        return self.w3.is_connected()
    
    def get_account_from_private_key(self, private_key: str) -> Account:
        """Get account from private key"""
        return Account.from_key(private_key)
    
    def create_plan(
        self, 
        creator_private_key: str,
        token_address: str,
        amount: int,
        interval: int,
        duration: int,
        api_url: str
    ) -> Tuple[str, str]:
        """
        Create a new subscription plan
        Returns (transaction_hash, plan_id)
        """
        account = self.get_account_from_private_key(creator_private_key)
        
        # Build transaction
        function = self.contract.functions.createPlan(
            Web3.to_checksum_address(token_address) if token_address != "0x0" else "0x0000000000000000000000000000000000000000",
            amount,
            interval,
            duration,
            api_url
        )
        
        # Get gas estimate
        gas_estimate = function.estimate_gas({'from': account.address})
        
        # Build transaction
        transaction = function.build_transaction({
            'from': account.address,
            'gas': gas_estimate,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(account.address),
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, creator_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for transaction receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Extract plan ID from logs
        plan_id = None
        for log in receipt.logs:
            try:
                decoded_log = self.contract.events.PlanCreated().process_log(log)
                plan_id = decoded_log['args']['planId'].hex()
                break
            except:
                continue
        
        return tx_hash.hex(), plan_id
    
    def subscribe_to_plan(
        self,
        subscriber_private_key: str,
        plan_id: str,
        value: int = 0
    ) -> str:
        """
        Subscribe to a plan
        Returns transaction_hash
        """
        account = self.get_account_from_private_key(subscriber_private_key)
        plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
        
        # Build transaction
        function = self.contract.functions.subscribe(plan_id_bytes)
        
        # Get gas estimate
        gas_estimate = function.estimate_gas({'from': account.address, 'value': value})
        
        # Build transaction
        transaction = function.build_transaction({
            'from': account.address,
            'gas': gas_estimate,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(account.address),
            'value': value
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, subscriber_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        return tx_hash.hex()
    
    def process_recurring_payment(
        self,
        payer_private_key: str,
        plan_id: str,
        subscriber_address: str,
        value: int = 0
    ) -> str:
        """
        Process recurring payment for a subscription
        Returns transaction_hash
        """
        account = self.get_account_from_private_key(payer_private_key)
        plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
        
        # Build transaction
        function = self.contract.functions.processRecurringPayment(
            plan_id_bytes,
            Web3.to_checksum_address(subscriber_address)
        )
        
        # Get gas estimate
        gas_estimate = function.estimate_gas({'from': account.address, 'value': value})
        
        # Build transaction
        transaction = function.build_transaction({
            'from': account.address,
            'gas': gas_estimate,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(account.address),
            'value': value
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.sign_transaction(transaction, payer_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        return tx_hash.hex()
    
    def get_plan(self, plan_id: str) -> Dict:
        """Get plan details"""
        plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
        plan = self.contract.functions.getPlan(plan_id_bytes).call()
        
        return {
            'token': plan[0],
            'amount': plan[1],
            'interval': plan[2],
            'duration': plan[3],
            'active': plan[4],
            'creator': plan[5],
            'apiUrl': plan[6]
        }
    
    def get_subscription(self, plan_id: str, subscriber_address: str) -> Dict:
        """Get subscription details"""
        plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
        subscription = self.contract.functions.getSubscription(
            plan_id_bytes,
            Web3.to_checksum_address(subscriber_address)
        ).call()
        
        return {
            'subscriber': subscription[0],
            'startTime': subscription[1],
            'nextPaymentDue': subscription[2],
            'endTime': subscription[3],
            'totalPaid': subscription[4],
            'active': subscription[5]
        }
    
    def check_subscription_status(self, plan_id: str, subscriber_address: str) -> Tuple[bool, bool]:
        """
        Check subscription status
        Returns (is_active, is_current_on_payments)
        """
        plan_id_bytes = bytes.fromhex(plan_id.replace('0x', ''))
        result = self.contract.functions.checkSubscriptionStatus(
            plan_id_bytes,
            Web3.to_checksum_address(subscriber_address)
        ).call()
        
        return result[0], result[1]
    
    def get_user_plans(self, creator_address: str) -> List[str]:
        """Get all plans created by a user"""
        plans = self.contract.functions.getUserPlans(
            Web3.to_checksum_address(creator_address)
        ).call()
        
        return [plan.hex() for plan in plans]
    
    def get_user_subscriptions(self, subscriber_address: str) -> List[str]:
        """Get all subscriptions for a user"""
        subscriptions = self.contract.functions.getUserSubscriptions(
            Web3.to_checksum_address(subscriber_address)
        ).call()
        
        return [sub.hex() for sub in subscriptions]
    
    def get_all_plans(self) -> List[str]:
        """Get all plans"""
        plans = self.contract.functions.getAllPlans().call()
        return [plan.hex() for plan in plans]

# Contract ABI (simplified version - in production, load from compiled contract)
SUBSCRIPTION_MANAGER_ABI = [
    {
        "inputs": [],
        "name": "createPlan",
        "outputs": [{"name": "planId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "planId", "type": "bytes32"}],
        "name": "subscribe",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "planId", "type": "bytes32"},
            {"name": "subscriber", "type": "address"}
        ],
        "name": "processRecurringPayment",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [{"name": "planId", "type": "bytes32"}],
        "name": "getPlan",
        "outputs": [
            {
                "components": [
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "interval", "type": "uint256"},
                    {"name": "duration", "type": "uint256"},
                    {"name": "active", "type": "bool"},
                    {"name": "creator", "type": "address"},
                    {"name": "apiUrl", "type": "string"}
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "planId", "type": "bytes32"},
            {"name": "subscriber", "type": "address"}
        ],
        "name": "getSubscription",
        "outputs": [
            {
                "components": [
                    {"name": "subscriber", "type": "address"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "nextPaymentDue", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                    {"name": "totalPaid", "type": "uint256"},
                    {"name": "active", "type": "bool"}
                ],
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "planId", "type": "bytes32"},
            {"name": "subscriber", "type": "address"}
        ],
        "name": "checkSubscriptionStatus",
        "outputs": [
            {"name": "isActive", "type": "bool"},
            {"name": "isCurrentOnPayments", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "creator", "type": "address"}],
        "name": "getUserPlans",
        "outputs": [{"name": "", "type": "bytes32[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "subscriber", "type": "address"}],
        "name": "getUserSubscriptions",
        "outputs": [{"name": "", "type": "bytes32[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAllPlans",
        "outputs": [{"name": "", "type": "bytes32[]"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "planId", "type": "bytes32"},
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "token", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "interval", "type": "uint256"}
        ],
        "name": "PlanCreated",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "planId", "type": "bytes32"},
            {"indexed": True, "name": "subscriber", "type": "address"},
            {"indexed": False, "name": "startTime", "type": "uint256"},
            {"indexed": False, "name": "endTime", "type": "uint256"}
        ],
        "name": "SubscriptionCreated",
        "type": "event"
    }
]

# Configuration
class ContractConfig:
    def __init__(self):
        self.web3_provider_url = os.getenv("WEB3_PROVIDER_URL", "http://localhost:8545")
        self.contract_address = os.getenv("CONTRACT_ADDRESS", "")
        self.default_private_key = os.getenv("DEFAULT_PRIVATE_KEY", "")
    
    def get_contract_interface(self) -> SubscriptionManagerInterface:
        """Get contract interface instance"""
        if not self.contract_address:
            raise ValueError("CONTRACT_ADDRESS environment variable not set")
        
        return SubscriptionManagerInterface(
            self.web3_provider_url,
            self.contract_address,
            SUBSCRIPTION_MANAGER_ABI
        )

