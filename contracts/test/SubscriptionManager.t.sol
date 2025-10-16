// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "../src/SubscriptionManager.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock Token", "MOCK") {
        _mint(msg.sender, 1000000 * 10 ** 18);
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

contract SubscriptionManagerTest is Test {
    SubscriptionManager public manager;
    MockERC20 public token;

    address public creator = address(1);
    address public subscriber = address(2);

    bytes32 public planId;

    function setUp() public {
        manager = new SubscriptionManager();
        token = new MockERC20();

        vm.deal(creator, 100 ether);
        vm.deal(subscriber, 100 ether);
        token.mint(subscriber, 10000 * 10 ** 18);
    }

    function testCreatePlanWithNativeToken() public {
        vm.startPrank(creator);

        planId = manager.createPlan(address(0), 1 ether, 30 days, 365 days, 3 days, "https://api.example.com");

        SubscriptionManager.SubscriptionPlan memory plan = manager.getPlan(planId);
        assertEq(plan.amount, 1 ether);
        assertTrue(plan.active);

        vm.stopPrank();
    }

    function testSubscribeWithNativeToken() public {
        vm.prank(creator);
        planId = manager.createPlan(address(0), 1 ether, 30 days, 365 days, 3 days, "https://api.example.com");

        vm.prank(subscriber);
        manager.subscribe{value: 1 ether}(planId, true);

        SubscriptionManager.Subscription memory sub = manager.getSubscription(planId, subscriber);
        assertTrue(sub.active);
        assertEq(sub.totalPaid, 1 ether);
    }
}
