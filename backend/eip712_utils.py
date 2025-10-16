"""
EIP-712 Typed Structured Data Signing Utilities
For SKALE Payment Tool backend integration
Compatible with eth-account >= 0.8.0
"""

from typing import Dict, Any, Optional
from eth_account import Account
from eth_account.messages import encode_typed_data  # Updated import
from eth_utils import keccak, to_bytes, to_checksum_address
from web3 import Web3
import json


class EIP712Signer:
    """
    EIP-712 signing and verification utilities for SKALE Payment Tool
    Compatible with MetaMask, WalletConnect, and ERC-8001
    """

    def __init__(self, contract_address: str, chain_id: int = 974399131):
        """
        Initialize EIP-712 signer

        Args:
            contract_address: SubscriptionManager contract address
            chain_id: SKALE chain ID (default: Calypso testnet)
        """
        self.contract_address = to_checksum_address(contract_address)
        self.chain_id = chain_id
        self.domain = {
            "name": "SKALE Payment Tool",
            "version": "1",
            "chainId": chain_id,
            "verifyingContract": self.contract_address
        }

    def get_domain(self) -> Dict[str, Any]:
        """Get EIP-712 domain"""
        return self.domain

    def create_subscription_message(
            self,
            plan_id: str,
            subscriber: str,
            amount: int,
            deadline: int,
            nonce: int,
            auto_renew: bool
    ) -> Dict[str, Any]:
        """
        Create EIP-712 typed data for subscription authorization

        Args:
            plan_id: Plan ID (bytes32 as hex string)
            subscriber: Subscriber wallet address
            amount: Payment amount in wei
            deadline: Unix timestamp when signature expires
            nonce: Current nonce for subscriber
            auto_renew: Auto-renewal flag

        Returns:
            EIP-712 structured data dict
        """
        message = {
            "planId": plan_id,
            "subscriber": to_checksum_address(subscriber),
            "amount": amount,
            "deadline": deadline,
            "nonce": nonce,
            "autoRenew": auto_renew
        }

        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "SubscriptionAuthorization": [
                    {"name": "planId", "type": "bytes32"},
                    {"name": "subscriber", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "autoRenew", "type": "bool"}
                ]
            },
            "primaryType": "SubscriptionAuthorization",
            "domain": self.domain,
            "message": message
        }

    def create_payment_message(
            self,
            payer: str,
            token: str,
            amount: int,
            deadline: int,
            nonce: int,
            action: str
    ) -> Dict[str, Any]:
        """
        Create EIP-712 typed data for payment authorization

        Args:
            payer: Payer wallet address
            token: Token address (0x0 for native)
            amount: Payment amount in wei
            deadline: Unix timestamp when signature expires
            nonce: Current nonce for payer
            action: Action string (e.g., "create_plan")

        Returns:
            EIP-712 structured data dict
        """
        # Normalize token address
        if token == "0x0" or token == "native":
            token = "0x0000000000000000000000000000000000000000"
        else:
            token = to_checksum_address(token)

        message = {
            "payer": to_checksum_address(payer),
            "token": token,
            "amount": amount,
            "deadline": deadline,
            "nonce": nonce,
            "action": action
        }

        return {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "chainId", "type": "uint256"},
                    {"name": "verifyingContract", "type": "address"}
                ],
                "PaymentAuthorization": [
                    {"name": "payer", "type": "address"},
                    {"name": "token", "type": "address"},
                    {"name": "amount", "type": "uint256"},
                    {"name": "deadline", "type": "uint256"},
                    {"name": "nonce", "type": "uint256"},
                    {"name": "action", "type": "string"}
                ]
            },
            "primaryType": "PaymentAuthorization",
            "domain": self.domain,
            "message": message
        }

    def sign_subscription(
            self,
            private_key: str,
            plan_id: str,
            subscriber: str,
            amount: int,
            deadline: int,
            nonce: int,
            auto_renew: bool
    ) -> str:
        """
        Sign subscription authorization message

        Args:
            private_key: Private key to sign with
            (other args same as create_subscription_message)

        Returns:
            Signature as hex string
        """
        typed_data = self.create_subscription_message(
            plan_id, subscriber, amount, deadline, nonce, auto_renew
        )

        # Use encode_typed_data (new function name)
        encoded_data = encode_typed_data(full_message=typed_data)
        account = Account.from_key(private_key)
        signed_message = account.sign_message(encoded_data)

        return signed_message.signature.hex()

    def sign_payment(
            self,
            private_key: str,
            payer: str,
            token: str,
            amount: int,
            deadline: int,
            nonce: int,
            action: str
    ) -> str:
        """
        Sign payment authorization message

        Args:
            private_key: Private key to sign with
            (other args same as create_payment_message)

        Returns:
            Signature as hex string
        """
        typed_data = self.create_payment_message(
            payer, token, amount, deadline, nonce, action
        )

        encoded_data = encode_typed_data(full_message=typed_data)
        account = Account.from_key(private_key)
        signed_message = account.sign_message(encoded_data)

        return signed_message.signature.hex()

    def verify_subscription_signature(
            self,
            plan_id: str,
            subscriber: str,
            amount: int,
            deadline: int,
            nonce: int,
            auto_renew: bool,
            signature: str
    ) -> bool:
        """
        Verify subscription authorization signature

        Args:
            (same as create_subscription_message)
            signature: Signature to verify (hex string)

        Returns:
            True if signature is valid and from subscriber
        """
        typed_data = self.create_subscription_message(
            plan_id, subscriber, amount, deadline, nonce, auto_renew
        )

        encoded_data = encode_typed_data(full_message=typed_data)

        # Recover address from signature
        recovered_address = Account.recover_message(
            encoded_data,
            signature=signature
        )

        return recovered_address.lower() == subscriber.lower()

    def verify_payment_signature(
            self,
            payer: str,
            token: str,
            amount: int,
            deadline: int,
            nonce: int,
            action: str,
            signature: str
    ) -> bool:
        """
        Verify payment authorization signature

        Args:
            (same as create_payment_message)
            signature: Signature to verify (hex string)

        Returns:
            True if signature is valid and from payer
        """
        typed_data = self.create_payment_message(
            payer, token, amount, deadline, nonce, action
        )

        encoded_data = encode_typed_data(full_message=typed_data)
        recovered_address = Account.recover_message(
            encoded_data,
            signature=signature
        )

        return recovered_address.lower() == payer.lower()

    def get_domain_separator(self) -> str:
        """
        Calculate EIP-712 domain separator

        Returns:
            Domain separator as hex string
        """
        domain_type_hash = keccak(
            text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
        )

        name_hash = keccak(text=self.domain["name"])
        version_hash = keccak(text=self.domain["version"])

        domain_separator = keccak(
            domain_type_hash +
            name_hash +
            version_hash +
            self.domain["chainId"].to_bytes(32, byteorder='big') +
            to_bytes(hexstr=self.domain["verifyingContract"]).rjust(32, b'\x00')
        )

        return '0x' + domain_separator.hex()


# Helper functions for API integration

def create_subscription_request(
        signer: EIP712Signer,
        private_key: str,
        plan_id: str,
        amount_eth: float,
        auto_renew: bool = True,
        valid_for_seconds: int = 300
) -> Dict[str, Any]:
    """
    Helper to create a complete subscription request with signature

    Args:
        signer: EIP712Signer instance
        private_key: User's private key
        plan_id: Plan ID to subscribe to
        amount_eth: Amount in ETH (will be converted to wei)
        auto_renew: Enable auto-renewal
        valid_for_seconds: How long signature is valid (default 5 minutes)

    Returns:
        Dict with all data needed for API request
    """
    from datetime import datetime, timedelta
    import time

    account = Account.from_key(private_key)
    subscriber = account.address
    amount_wei = Web3.to_wei(amount_eth, 'ether')
    deadline = int(time.time() + valid_for_seconds)

    # In production, fetch nonce from contract
    nonce = 0  # TODO: Get from contract.functions.getNonce(subscriber).call()

    signature = signer.sign_subscription(
        private_key,
        plan_id,
        subscriber,
        amount_wei,
        deadline,
        nonce,
        auto_renew
    )

    return {
        "plan_id": plan_id,
        "subscriber": subscriber,
        "amount": amount_wei,
        "deadline": deadline,
        "nonce": nonce,
        "auto_renew": auto_renew,
        "signature": signature
    }


def create_frontend_signing_data(
        signer: EIP712Signer,
        plan_id: str,
        subscriber: str,
        amount_wei: int,
        deadline: int,
        nonce: int,
        auto_renew: bool
) -> Dict[str, Any]:
    """
    Create EIP-712 data for frontend wallet to sign
    This is what you send to MetaMask/WalletConnect

    Returns:
        JSON-serializable dict for eth_signTypedData_v4
    """
    return signer.create_subscription_message(
        plan_id,
        subscriber,
        amount_wei,
        deadline,
        nonce,
        auto_renew
    )


# Test and example usage
if __name__ == "__main__":
    import time

    # Example configuration
    CONTRACT_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc9e7595f0f8a3"
    CHAIN_ID = 974399131  # SKALE Calypso testnet

    # Initialize signer
    signer = EIP712Signer(CONTRACT_ADDRESS, CHAIN_ID)

    print("EIP-712 Signer initialized")
    print(f"Domain: {signer.get_domain()}")
    print(f"Domain Separator: {signer.get_domain_separator()}")

    # Example: Create and sign a subscription
    # NOTE: Replace with real private key for testing
    TEST_PRIVATE_KEY = "0x" + "1" * 64  # NEVER use this in production!
    PLAN_ID = "0x" + "a" * 64  # Example plan ID

    try:
        account = Account.from_key(TEST_PRIVATE_KEY)
        subscriber = account.address

        print(f"\nTest Account: {subscriber}")

        # Create signature
        amount_wei = Web3.to_wei(1.5, 'ether')
        deadline = int(time.time()) + 300  # 5 minutes
        nonce = 0

        signature = signer.sign_subscription(
            TEST_PRIVATE_KEY,
            PLAN_ID,
            subscriber,
            amount_wei,
            deadline,
            nonce,
            True
        )

        print(f"\nSubscription Signature: {signature[:20]}...")

        # Verify signature
        is_valid = signer.verify_subscription_signature(
            PLAN_ID,
            subscriber,
            amount_wei,
            deadline,
            nonce,
            True,
            signature
        )

        print(f"Signature Valid: {is_valid}")

        # Create request data
        request_data = create_subscription_request(
            signer,
            TEST_PRIVATE_KEY,
            PLAN_ID,
            1.5,
            True
        )

        print("\nAPI Request Data:")
        print(json.dumps({
            "plan_id": request_data["plan_id"],
            "subscriber": request_data["subscriber"],
            "amount": str(request_data["amount"]),
            "deadline": request_data["deadline"],
            "nonce": request_data["nonce"],
            "auto_renew": request_data["auto_renew"],
            "signature": request_data["signature"][:20] + "..."
        }, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This example uses a test key. Replace with real key for actual use.")


# Frontend integration example
FRONTEND_EXAMPLE = """
// Frontend JavaScript/TypeScript example
// File: frontend/src/utils/eip712.ts

import { ethers } from 'ethers';

// 1. Get signing data from backend API
const response = await fetch('/api/get-subscription-signing-data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    planId: '0x...',
    amount: ethers.utils.parseEther('1.5'),
    autoRenew: true
  })
});

const signingData = await response.json();

// 2. Request signature from user's wallet
const provider = new ethers.providers.Web3Provider(window.ethereum);
const signer = provider.getSigner();
const address = await signer.getAddress();

// EIP-712 signature request (compatible with MetaMask, WalletConnect, etc.)
const signature = await provider.send('eth_signTypedData_v4', [
  address,
  JSON.stringify(signingData)
]);

// 3. Send signed request to backend
const subscribeResponse = await fetch('/api/subscribe', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    planId: signingData.message.planId,
    autoRenew: signingData.message.autoRenew,
    deadline: signingData.message.deadline,
    signature: signature
  })
});

const result = await subscribeResponse.json();
console.log('Subscription created:', result);
"""