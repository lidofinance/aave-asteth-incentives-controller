// SPDX-FileCopyrightText: 2021 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.10;

import {IERC20} from "../dependencies/openzeppelin/IERC20.sol";
import {Address} from "../dependencies/openzeppelin/Address.sol";
import {Ownable} from "../dependencies/openzeppelin/Ownable.sol";
import {SafeERC20} from "../dependencies/openzeppelin/SafeERC20.sol";
import {RewardsUtils} from "../utils/RewardsUtils.sol";

import {IAStETH} from "../interfaces/IAStETH.sol";
import {IStakingRewards} from "../interfaces/IStakingRewards.sol";
import {IAaveIncentivesController} from "../interfaces/IAaveIncentivesController.sol";

/// @author psirex
/// @notice Implementation for the IAaveIncentivesController with
///     linear rewards distribution across depositors proportional
///     to their stake size.
contract AaveAStETHIncentivesController is IAaveIncentivesController, IStakingRewards, Ownable {
    using RewardsUtils for RewardsUtils.RewardsState;
    using SafeERC20 for IERC20;

    error NotRewardsDistributorError();
    error RewardsPeriodNotFinishedError();
    error AlreadyInitializedError();
    error StakingTokenIsNotContractError();

    event RewardsDistributorChanged(
        address indexed oldRewardsDistributor,
        address indexed newRewardsDistributor
    );
    event RewardAdded(uint256 rewardAmount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardsDurationUpdated(uint256 newDuration);
    event Recovered(address indexed token, uint256 amount);
    event RewardsAccrued(address indexed depositor, uint256 earnedRewards);
    event Initialized(address indexed stakingToken);

    IERC20 public immutable REWARD_TOKEN;

    IAStETH public stakingToken;
    address public rewardsDistributor;
    uint256 public rewardsDuration;
    RewardsUtils.RewardsState internal rewardsState;

    constructor(
        address _rewardToken,
        uint256 _rewardsDuration,
        address _rewardsDistributor
    ) {
        REWARD_TOKEN = IERC20(_rewardToken);
        _setRewardsDuration(_rewardsDuration);
        _setRewardsDistributor(_rewardsDistributor);
    }

    /// @notice Sets stakingToken variable if it wasn't set earlier
    /// @dev setStakingToken sets via standalone method instead of constructor
    ///     because AAVE's ATokens requires IncentivesController to be passed
    ///     on the deployment stage.
    function initialize(address _stakingToken) external onlyOwner {
        if (address(stakingToken) != address(0)) {
            revert AlreadyInitializedError();
        }
        if (!Address.isContract(_stakingToken)) {
            revert StakingTokenIsNotContractError();
        }
        stakingToken = IAStETH(_stakingToken);
        emit Initialized(_stakingToken);
    }

    /// @notice Updates rewards of the depositor
    /// @dev Called by the corresponding asset on any update that affects the rewards distribution
    /// @param user The address of the user
    /// @param totalSupply The total supply of the asset in the lending pool before update
    /// @param userBalance The balance of the user of the asset in the lending pool before update
    function handleAction(
        address user,
        uint256 totalSupply,
        uint256 userBalance
    ) external override {
        if (msg.sender != address(stakingToken)) {
            return;
        }
        uint256 earnedRewards = rewardsState.updateDepositorReward(totalSupply, user, userBalance);
        if (earnedRewards > 0) {
            emit RewardsAccrued(user, earnedRewards);
        }
    }

    /// @notice Sets the value of rewards distributor. Might be called only by the owner
    function setRewardsDistributor(address newRewardsDistributor) external onlyOwner {
        _setRewardsDistributor(newRewardsDistributor);
    }

    /// @notice Sets the value of rewards duration. Might be called only by the owner
    function setRewardsDuration(uint256 newRewardsDuration) external onlyOwner {
        _setRewardsDuration(newRewardsDuration);
    }

    /// @notice Transfers all earned tokens to the depositor and reset his reward
    function claimReward() public {
        (uint256 stakedByUser, uint256 totalStaked) = stakingToken.getInternalUserBalanceAndSupply(
            msg.sender
        );
        uint256 reward = rewardsState.payDepositorReward(totalStaked, msg.sender, stakedByUser);
        if (reward > 0) {
            REWARD_TOKEN.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    /// @notice Starts reward period to distribute given amount of tokens from the current timestamp
    ///     during rewards duration. If the previous reward period hasn't finished, adds the given
    ///     reward to the previous reward. Might be called only by rewards distributor
    /// @param reward Amount of tokens to distribute on reward period
    /// @param rewardHolder Address to retrieve reward tokens from
    function notifyRewardAmount(uint256 reward, address rewardHolder) external {
        if (msg.sender != rewardsDistributor) {
            revert NotRewardsDistributorError();
        }
        REWARD_TOKEN.safeTransferFrom(rewardHolder, address(this), reward);
        uint256 _periodFinish = rewardsState.endDate;
        uint256 _rewardsDuration = rewardsDuration;
        uint256 _rewardPerSecond = 0;
        if (block.timestamp >= _periodFinish) {
            _rewardPerSecond = reward / _rewardsDuration;
        } else {
            uint256 remaining = _periodFinish - block.timestamp;
            uint256 leftover = remaining * rewardsState.rewardPerSecond;
            _rewardPerSecond = (reward + leftover) / _rewardsDuration;
        }
        uint256 totalStaked = stakingToken.internalTotalSupply();
        rewardsState.updateRewardPeriod(
            totalStaked,
            _rewardPerSecond,
            block.timestamp + _rewardsDuration
        );
        emit RewardAdded(reward);
    }

    /// @notice Allows recovering ERC20 tokens from incentives controller to the owner address.
    ///     Might be called only by the owner
    /// @param tokenAddress Address of ERC20 token to recover
    /// @param tokenAmount Number of tokens to recover
    function recoverERC20(address tokenAddress, uint256 tokenAmount) external onlyOwner {
        IERC20(tokenAddress).safeTransfer(owner(), tokenAmount);
        emit Recovered(tokenAddress, tokenAmount);
    }

    /// @notice  Updates end date of reward program. Might be used to end rewards emission earlier.
    ///     Might be called only by the owner
    /// @param endDate New end date of reward program. Must be greater or equal than the block.timestamp
    function updatePeriodFinish(uint256 endDate) external onlyOwner {
        uint256 totalStaked = stakingToken.internalTotalSupply();
        rewardsState.updateRewardPeriod(totalStaked, rewardsState.rewardPerSecond, endDate);
    }

    /// @notice Returns amount of tokens earned by the depositor
    /// @param depositor Address of the depositor
    function earned(address depositor) external view returns (uint256) {
        (uint256 staked, uint256 totalStaked) = stakingToken.getInternalUserBalanceAndSupply(
            depositor
        );
        return rewardsState.earnedReward(totalStaked, depositor, staked);
    }

    /// @notice Returns end date of the reward period
    function periodFinish() external view returns (uint256) {
        return rewardsState.endDate;
    }

    /// @notice Returns current reward per second
    function rewardPerSecond() external view returns (uint256) {
        return rewardsState.rewardPerSecond;
    }

    function _setRewardsDistributor(address newRewardsDistributor) internal {
        address oldRewardsDistributor = rewardsDistributor;
        if (oldRewardsDistributor != newRewardsDistributor) {
            rewardsDistributor = newRewardsDistributor;
            emit RewardsDistributorChanged(oldRewardsDistributor, newRewardsDistributor);
        }
    }

    function _setRewardsDuration(uint256 _rewardsDuration) internal {
        if (block.timestamp <= rewardsState.endDate) {
            revert RewardsPeriodNotFinishedError();
        }
        rewardsDuration = _rewardsDuration;
        emit RewardsDurationUpdated(_rewardsDuration);
    }
}
