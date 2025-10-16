// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SubscriptionManager (Simplified for Testing)
 * @dev Basic subscription management without complex dependencies
 */
contract SubscriptionManager {
    struct SubscriptionPlan {
        address token;
        uint256 amount;
        uint256 interval;
        uint256 duration;
        uint256 gracePeriod;
        bool active;
        address creator;
        address payable paymentRecipient;
        string apiUrl;
        uint256 totalSubscribers;
    }

    struct Subscription {
        address subscriber;
        uint256 startTime;
        uint256 nextPaymentDue;
        uint256 endTime;
        uint256 totalPaid;
        uint256 missedPayments;
        bool active;
        bool autoRenew;
    }

    mapping(bytes32 => SubscriptionPlan) public plans;
    mapping(bytes32 => mapping(address => Subscription)) public subscriptions;
    mapping(address => uint256) public nonces;

    bytes32[] public allPlans;
    uint256 public planCounter;

    event PlanCreated(bytes32 indexed planId, address indexed creator, address token, uint256 amount);
    event SubscriptionCreated(bytes32 indexed planId, address indexed subscriber);
    event PaymentProcessed(bytes32 indexed planId, address indexed subscriber, uint256 amount);

    constructor() {}

    function createPlan(
        address token,
        uint256 amount,
        uint256 interval,
        uint256 duration,
        uint256 gracePeriod,
        string memory apiUrl
    ) external returns (bytes32 planId) {
        require(amount > 0, "Amount must be > 0");
        require(interval > 0, "Interval must be > 0");

        planCounter++;
        planId = keccak256(abi.encodePacked(msg.sender, planCounter, block.timestamp));

        plans[planId] = SubscriptionPlan({
            token: token,
            amount: amount,
            interval: interval,
            duration: duration,
            gracePeriod: gracePeriod,
            active: true,
            creator: msg.sender,
            paymentRecipient: payable(msg.sender),
            apiUrl: apiUrl,
            totalSubscribers: 0
        });

        allPlans.push(planId);

        emit PlanCreated(planId, msg.sender, token, amount);
    }

    function subscribe(bytes32 planId, bool autoRenew) external payable {
        SubscriptionPlan memory plan = plans[planId];
        require(plan.active, "Plan not active");
        require(subscriptions[planId][msg.sender].subscriber == address(0), "Already subscribed");

        if (plan.token == address(0)) {
            require(msg.value >= plan.amount, "Insufficient payment");
            (bool success,) = plan.paymentRecipient.call{value: plan.amount}("");
            require(success, "Payment failed");
        }

        uint256 startTime = block.timestamp;

        subscriptions[planId][msg.sender] = Subscription({
            subscriber: msg.sender,
            startTime: startTime,
            nextPaymentDue: startTime + plan.interval,
            endTime: startTime + plan.duration,
            totalPaid: plan.amount,
            missedPayments: 0,
            active: true,
            autoRenew: autoRenew
        });

        plans[planId].totalSubscribers++;

        emit SubscriptionCreated(planId, msg.sender);
        emit PaymentProcessed(planId, msg.sender, plan.amount);
    }

    function getPlan(bytes32 planId) external view returns (SubscriptionPlan memory) {
        return plans[planId];
    }

    function getSubscription(bytes32 planId, address subscriber) external view returns (Subscription memory) {
        return subscriptions[planId][subscriber];
    }

    function getAllPlans() external view returns (bytes32[] memory) {
        return allPlans;
    }

    function getNonce(address user) external view returns (uint256) {
        return nonces[user];
    }
}
