// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "forge-std/Script.sol";
import "../src/SubscriptionManager.sol";

contract DeployScript is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        SubscriptionManager subscriptionManager = new SubscriptionManager();

        console.log("SubscriptionManager deployed to:", address(subscriptionManager));

        vm.stopBroadcast();
    }
}
