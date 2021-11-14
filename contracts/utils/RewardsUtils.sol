// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

/// @author psirex
/// @notice Provides logic and data structure for convenient work with
///   staking rewards distributed in a time-based manner
library RewardsUtils {
  /// @notice Keeps reward data for depositor
  /// @param paidReward The reward paid to the depositor
  /// @param upcomingReward The upcoming depositor's reward
  /// @param accumulatedRewardPerTokenPaid The value of RewardsState.accumulatedRewardPerToken
  ///   has used to calculate the upcomingReward last time.
  struct Reward {
    uint256 paidReward;
    uint256 upcomingReward;
    uint256 accumulatedRewardPerTokenPaid;
  }

  /// @notice Stores state of rewards program
  /// @param endDate End date of the reward program
  /// @param updatedAt Last update timestamp
  /// @param rewardPerSecond Amount of tokens distributed in one second
  /// @param accumulatedRewardPerToken Sum of historical values
  ///   (PRECISION * timeDelta * rewardPerSecond) / totalStaked where timeDelta is a time passed from last update
  /// @param rewards Rewards info of depositors
  struct RewardsState {
    uint256 endDate;
    uint256 updatedAt;
    uint256 rewardPerSecond;
    uint256 accumulatedRewardPerToken;
    mapping(address => Reward) rewards;
  }

  uint256 constant private PRECISION = 1e18;

  /// @notice Updates current state of the reward program
  /// @param state State of the reward program
  /// @param totalStaked The total staked amount of tokens
  /// @param rewardPerSecond Amount of tokens to distribute in one second
  /// @param endDate End date of the reward program
  /// @dev endDate value must be greater or equal to the current block.timestamp value
  function updateRewardPeriod(
    RewardsState storage state,
    uint256 totalStaked,
    uint256 rewardPerSecond,
    uint256 endDate
  ) internal {
    require(endDate >= block.timestamp, 'END_DATE_TOO_LOW');
    state.accumulatedRewardPerToken = rewardPerToken(state, totalStaked);
    state.endDate = endDate;
    state.updatedAt = block.timestamp;
    state.rewardPerSecond = rewardPerSecond;
  }

  /// @notice Returns reward depositor earned and able to retrieve
  /// @param state State of the reward program
  /// @param totalStaked The total staked amount of tokens at the current block timestamp
  /// @param depositor Address of the depositor
  /// @param staked Amount of tokens staked by the depositor at the current block timestamp
  function earnedReward(RewardsState storage state, uint256 totalStaked, address depositor, uint256 staked)
    internal
    view
    returns (uint256)
  {
    Reward storage depositorReward = state.rewards[depositor];
    return depositorReward.upcomingReward + staked * (rewardPerToken(state, totalStaked) - depositorReward.accumulatedRewardPerTokenPaid) / PRECISION;
  }

  /// @notice Updates reward of depositor stores this value in the upcoming reward and return
  ///   the new value of unpaid earned reward
  /// @param state State of the reward program
  /// @param prevTotalStaked The total amount of tokens has staked by all depositors before the current update
  /// @param depositor Address of the depositor
  /// @param prevStaked The amount of tokens staked by the depositor before the current update
  /// @return depositorReward The new value of unpaid reward earned by the depositor
  /// @dev This method must be called on every change of the depositor's balance with totalStaked
  ///   and staked equal to prev values of the balance of the depositor and totalStaked
  function updateDepositorReward(RewardsState storage state, uint256 prevTotalStaked, address depositor, uint256 prevStaked)
    internal returns (uint256 depositorReward)
  {
    uint256 newRewardPerToken = _updateRewardPerToken(state, prevTotalStaked);
    depositorReward = earnedReward(state, prevTotalStaked, depositor, prevStaked);
    state.rewards[depositor].accumulatedRewardPerTokenPaid = newRewardPerToken;
    state.rewards[depositor].upcomingReward = depositorReward;
  }

  /// @notice Marks upcoming reward as paid resets its value and return amount of paid reward
  /// @param state State of the reward program
  /// @param totalStaked The total staked amount of tokens at the current block timestamp
  /// @param depositor Address of the depositor
  /// @param staked Amount of tokens staked by the depositor at the current block timestamp
  /// @return paidReward The amount of reward paid to the depositor
  function payDepositorReward(RewardsState storage state, uint256 totalStaked, address depositor, uint256 staked)
    internal
    returns (uint256 paidReward)
  {
    paidReward = updateDepositorReward(state, totalStaked, depositor, staked);
    state.rewards[depositor].upcomingReward = 0;
    state.rewards[depositor].paidReward += paidReward;
  }

  /// @notice Returns value of accumulated reward per token at the time equal to
  /// minimum between current block timestamp or reward period end date
  /// @param state State of the reward program
  /// @param totalStaked The total staked amount of tokens at the current block timestamp
  function rewardPerToken(RewardsState storage state, uint256 totalStaked) internal view returns (uint256) {
    if (totalStaked == 0) {
      return 0;
    }
    uint256 timeDelta = _blockTimestampOrEndDate(state) - state.updatedAt;
    uint256 unaccountedRewardPerToken = (PRECISION * timeDelta * state.rewardPerSecond) / totalStaked;
    return state.accumulatedRewardPerToken + unaccountedRewardPerToken;
  }


  /// @notice Updates the accumulated reward per token value
  /// @param state State of the reward program
  /// @param totalStaked The total staked amount of tokens at the current block timestamp
  function _updateRewardPerToken(RewardsState storage state, uint256 totalStaked) private returns (uint256) {
      uint256 newRewardPerToken = rewardPerToken(state, totalStaked);
      state.accumulatedRewardPerToken = newRewardPerToken;
      state.updatedAt = _blockTimestampOrEndDate(state);
      return newRewardPerToken;
  }

  /// @notice Returns the minimum between block.timestamp and endDate
  /// @param state State of the reward program
  function _blockTimestampOrEndDate(RewardsState storage state)
    private
    view
    returns (uint256)
  {
    return state.endDate > block.timestamp ? block.timestamp : state.endDate;
  }
}