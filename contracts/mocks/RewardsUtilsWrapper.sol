// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import {RewardsUtils} from "../utils/RewardsUtils.sol";

contract RewardsUtilsWrapper {
    using RewardsUtils for RewardsUtils.RewardsState;
    RewardsUtils.RewardsState public rewardsState;

    function depositorRewards(address depositor)
        external
        view
        returns (RewardsUtils.Reward memory)
    {
        return rewardsState.rewards[depositor];
    }

    function updateRewardPeriod(
        uint256 totalStaked,
        uint256 rewardPerSecond,
        uint256 endDate
    ) external {
        rewardsState.updateRewardPeriod(totalStaked, rewardPerSecond, endDate);
    }

    function earnedReward(
        uint256 totalStaked,
        address depositor,
        uint256 staked
    ) external view returns (uint256) {
        return rewardsState.earnedReward(totalStaked, depositor, staked);
    }

    function updateDepositorReward(
        uint256 totalStaked,
        address depositor,
        uint256 staked
    ) external returns (uint256) {
        return rewardsState.updateDepositorReward(totalStaked, depositor, staked);
    }

    function payDepositorReward(
        uint256 totalStaked,
        address depositor,
        uint256 staked
    ) external returns (uint256) {
        return rewardsState.payDepositorReward(totalStaked, depositor, staked);
    }

    function rewardPerToken(uint256 totalStaked) external view returns (uint256) {
        return rewardsState.rewardPerToken(totalStaked);
    }
}
