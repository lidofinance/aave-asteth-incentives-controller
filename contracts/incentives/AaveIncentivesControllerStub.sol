// SPDX-FileCopyrightText: 2021 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.10;

import {Ownable} from "../dependencies/openzeppelin/Ownable.sol";
import {UUPSUpgradeable} from "../dependencies/openzeppelin/UUPSUpgradable.sol";
import {StorageSlot} from "../dependencies/openzeppelin/StorageSlot.sol";

import {IStakingRewards} from "../interfaces/IStakingRewards.sol";
import {IAaveIncentivesController} from "../interfaces/IAaveIncentivesController.sol";

import {UnstructuredStorageVersionised} from "./UnstructuredStorageVersionised.sol";

/// @author psirex
/// @notice Upgradable stub implementation for the IAaveIncentivesController
contract AaveIncentivesControllerStub is
    UnstructuredStorageVersionised,
    IAaveIncentivesController,
    IStakingRewards
{
    error MethodNotUnimplementedError();
    uint256 private constant _IMPLEMENTATION_VERSION = 1;

    constructor() UnstructuredStorageVersionised(_IMPLEMENTATION_VERSION) {
        _initialize(address(0));
    }

    function initialize(address owner) external {
        _initialize(owner);
    }

    /// @notice Stub implementation of handleAction method
    /// @dev Called by the corresponding asset on any update that affects the rewards distribution
    /// @param user The address of the user
    /// @param totalSupply The total supply of the asset in the lending pool before update
    /// @param userBalance The balance of the user of the asset in the lending pool before update
    function handleAction(
        address user,
        uint256 totalSupply,
        uint256 userBalance
    ) external override {}

    /// @notice Stub implementation to always return 0 as period finish
    function periodFinish() external pure returns (uint256) {
        return 0;
    }

    /// @notice Stub implementation which reverts with MethodNotUnimplementedError()
    function notifyRewardAmount(uint256 reward, address rewardHolder) external {
        revert MethodNotUnimplementedError();
    }
}
