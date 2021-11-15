// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

interface IAaveIncentivesController {
    function handleAction(
        address user,
        uint256 totalSupply,
        uint256 userBalance
    ) external;
}
