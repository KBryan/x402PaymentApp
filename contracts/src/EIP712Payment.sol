// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";

/**
 * @title EIP712Payment
 * @dev EIP-712 typed structured data hashing and signing for payment authorization
 * Supports ERC-8001 and wallet integrations
 */
contract EIP712Payment is EIP712 {
    using ECDSA for bytes32;

    // EIP-712 Type Hashes
    bytes32 public constant PAYMENT_AUTHORIZATION_TYPEHASH = keccak256(
        "PaymentAuthorization(address payer,address token,uint256 amount,uint256 deadline,uint256 nonce,string action)"
    );

    bytes32 public constant SUBSCRIPTION_AUTHORIZATION_TYPEHASH = keccak256(
        "SubscriptionAuthorization(bytes32 planId,address subscriber,uint256 amount,uint256 deadline,uint256 nonce,bool autoRenew)"
    );

    bytes32 public constant RECURRING_PAYMENT_TYPEHASH = keccak256(
        "RecurringPayment(bytes32 planId,address subscriber,uint256 amount,uint256 paymentNumber,uint256 deadline,uint256 nonce)"
    );

    // Nonce tracking for replay protection
    mapping(address => uint256) public nonces;

    // Events
    event NonceIncremented(address indexed user, uint256 newNonce);

    constructor() EIP712("SKALE Payment Tool", "1") {}

    /**
     * @dev Verify payment authorization signature
     * @param payer Address of the payer
     * @param token Token address (address(0) for native)
     * @param amount Payment amount
     * @param deadline Signature expiration timestamp
     * @param nonce User's current nonce
     * @param action Action being authorized (e.g., "create_plan", "subscribe")
     * @param signature EIP-712 signature
     * @return bool True if signature is valid
     */
    function verifyPaymentAuthorization(
        address payer,
        address token,
        uint256 amount,
        uint256 deadline,
        uint256 nonce,
        string memory action,
        bytes memory signature
    ) public view returns (bool) {
        require(block.timestamp <= deadline, "Signature expired");
        require(nonce == nonces[payer], "Invalid nonce");

        bytes32 structHash = keccak256(
            abi.encode(PAYMENT_AUTHORIZATION_TYPEHASH, payer, token, amount, deadline, nonce, keccak256(bytes(action)))
        );

        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = hash.recover(signature);

        return signer == payer;
    }

    /**
     * @dev Verify subscription authorization signature
     * @param planId Plan identifier
     * @param subscriber Subscriber address
     * @param amount Payment amount
     * @param deadline Signature expiration
     * @param nonce User's current nonce
     * @param autoRenew Auto-renewal flag
     * @param signature EIP-712 signature
     * @return bool True if signature is valid
     */
    function verifySubscriptionAuthorization(
        bytes32 planId,
        address subscriber,
        uint256 amount,
        uint256 deadline,
        uint256 nonce,
        bool autoRenew,
        bytes memory signature
    ) public view returns (bool) {
        require(block.timestamp <= deadline, "Signature expired");
        require(nonce == nonces[subscriber], "Invalid nonce");

        bytes32 structHash = keccak256(
            abi.encode(SUBSCRIPTION_AUTHORIZATION_TYPEHASH, planId, subscriber, amount, deadline, nonce, autoRenew)
        );

        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = hash.recover(signature);

        return signer == subscriber;
    }

    /**
     * @dev Verify recurring payment authorization
     * @param planId Plan identifier
     * @param subscriber Subscriber address
     * @param amount Payment amount
     * @param paymentNumber Sequential payment number
     * @param deadline Signature expiration
     * @param nonce User's current nonce
     * @param signature EIP-712 signature
     * @return bool True if signature is valid
     */
    function verifyRecurringPayment(
        bytes32 planId,
        address subscriber,
        uint256 amount,
        uint256 paymentNumber,
        uint256 deadline,
        uint256 nonce,
        bytes memory signature
    ) public view returns (bool) {
        require(block.timestamp <= deadline, "Signature expired");
        require(nonce == nonces[subscriber], "Invalid nonce");

        bytes32 structHash = keccak256(
            abi.encode(RECURRING_PAYMENT_TYPEHASH, planId, subscriber, amount, paymentNumber, deadline, nonce)
        );

        bytes32 hash = _hashTypedDataV4(structHash);
        address signer = hash.recover(signature);

        return signer == subscriber;
    }

    /**
     * @dev Increment nonce for a user (called after successful operation)
     * @param user User address
     */
    function _incrementNonce(address user) internal {
        nonces[user]++;
        emit NonceIncremented(user, nonces[user]);
    }

    /**
     * @dev Get domain separator for EIP-712
     * @return bytes32 Domain separator hash
     */
    function getDomainSeparator() external view returns (bytes32) {
        return _domainSeparatorV4();
    }

    /**
     * @dev Get current nonce for a user
     * @param user User address
     * @return uint256 Current nonce
     */
    function getNonce(address user) external view returns (uint256) {
        return nonces[user];
    }

    /**
     * @dev Build typed data hash for off-chain signing
     * @param structHash The struct hash to sign
     * @return bytes32 The typed data hash
     */
    function getTypedDataHash(bytes32 structHash) external view returns (bytes32) {
        return _hashTypedDataV4(structHash);
    }

    /**
     * @dev Helper to build payment authorization struct hash
     */
    function buildPaymentAuthorizationHash(
        address payer,
        address token,
        uint256 amount,
        uint256 deadline,
        uint256 nonce,
        string memory action
    ) external pure returns (bytes32) {
        return keccak256(
            abi.encode(PAYMENT_AUTHORIZATION_TYPEHASH, payer, token, amount, deadline, nonce, keccak256(bytes(action)))
        );
    }

    /**
     * @dev Helper to build subscription authorization struct hash
     */
    function buildSubscriptionAuthorizationHash(
        bytes32 planId,
        address subscriber,
        uint256 amount,
        uint256 deadline,
        uint256 nonce,
        bool autoRenew
    ) external pure returns (bytes32) {
        return keccak256(
            abi.encode(SUBSCRIPTION_AUTHORIZATION_TYPEHASH, planId, subscriber, amount, deadline, nonce, autoRenew)
        );
    }
}
