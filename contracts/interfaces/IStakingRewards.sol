// SPDX-FileCopyrightText: 2021 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.10;

/// @author psirex
/// @notice Staking rewards interface to work with RewardsManager contract
interface IStakingRewards {
    /// @notice Returns end date of the reward period
    function periodFinish() external view returns (uint256);

    /// @notice Starts reward period to distribute given amount of tokens from the current timestamp
    ///     during rewards duration.
    /// @param reward Amount of tokens to distribute on reward period
    /// @param rewardHolder Address to retrieve reward tokens
    function notifyRewardAmount(uint256 reward, address rewardHolder) external;
}
