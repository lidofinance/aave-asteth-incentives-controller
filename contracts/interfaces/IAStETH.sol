// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

interface IAStETH {
    function internalTotalSupply() external view returns (uint256);

    function getInternalUserBalanceAndSupply(address user) external view returns (uint256, uint256);
}
