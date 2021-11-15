// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

interface IAStETH {
    /// @notice Returns the internal total supply of the aToken
    function internalTotalSupply() external view returns (uint256);

    /// @dev Returns the internal balance of the user and the scaled total supply
    /// @param user The address of the user
    /// @return The internal balance and the scaled total supply
    function getInternalUserBalanceAndSupply(address user) external view returns (uint256, uint256);
}
