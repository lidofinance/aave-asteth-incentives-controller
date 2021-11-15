// SPDX-FileCopyrightText: 2021 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.10;

interface IAaveIncentivesController {
    /// @dev Called by the corresponding asset on any update that affects the rewards distribution
    /// @param user The address of the user
    /// @param totalSupply The total supply of the asset in the lending pool before update
    /// @param userBalance The balance of the user of the asset in the lending pool before update
    function handleAction(
        address user,
        uint256 totalSupply,
        uint256 userBalance
    ) external;
}
