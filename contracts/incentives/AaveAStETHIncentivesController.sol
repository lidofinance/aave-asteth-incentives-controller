// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import { RewardsUtils } from '../utils/RewardsUtils.sol';
import { IAStETH } from '../interfaces/IAStETH.sol';
import { IERC20 } from '../dependencies/openzeppelin/IERC20.sol';
import { Ownable } from '../dependencies/openzeppelin/Ownable.sol';
import { SafeERC20 } from '../dependencies/openzeppelin/SafeERC20.sol';
import { UUPSUpgradeable } from '../dependencies/openzeppelin/UUPSUpgradable.sol';

contract AaveAStETHIncentivesController is Ownable, UUPSUpgradeable {
    using RewardsUtils for RewardsUtils.RewardsState;
    using SafeERC20 for IERC20;
    
    event StakingTokenChanged(address indexed oldStakingToken, address indexed newStakingToken);
    event RewardsDistributorChanged(address indexed oldRewardsDistributor, address indexed newRewardsDistributor);
    event RewardAdded(uint256 rewardAmount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardsDurationUpdated(uint256 newDuration);
    event Recovered(address indexed token, uint256 amount);
    event RewardsAccrued(address indexed depositor, uint256 earnedRewards);

    uint8 public constant IMPLEMENTATION_VERSION = 2;
    IERC20 public immutable REWARD_TOKEN;

    uint8 public version;
    IAStETH public stakingToken;
    address public rewardsDistributor;
    uint256 public rewardsDuration;
    RewardsUtils.RewardsState public rewardsState;

    constructor(address _rewardToken, address _owner, address _rewardsDistributor, uint256 _rewardsDuration) {
        REWARD_TOKEN = IERC20(_rewardToken);
        // initialize logic with zero address as owner
        // to prevent access to admin methods of implementaiton
        initialize(_owner, _rewardsDistributor, _rewardsDuration);
    }

    function initialize(address owner, address _rewardsDistributor, uint256 _rewardsDuration) public {
        require(version != IMPLEMENTATION_VERSION, 'ALREADY_INITIALIZED');
        version = IMPLEMENTATION_VERSION;
        _transferOwnership(owner);
        _setRewardsDuration(_rewardsDuration);
        _setRewardsDistributor(_rewardsDistributor);
    }


    function handleAction(
      address user,
      uint256 totalSupply,
      uint256 userBalance
    ) external {
        if (msg.sender != address(stakingToken)) {
            return;
        }
        uint256 earnedRewards = rewardsState.updateDepositorReward(totalSupply, user, userBalance);
        if (earnedRewards > 0) {
            emit RewardsAccrued(user, earnedRewards);
        }
    }

    function depositorRewards(address depositor) external view returns (RewardsUtils.Reward memory) {
        return rewardsState.rewards[depositor];
    }

    function setRewardsDistributor(address newRewardsDistributor) external onlyOwner {
        _setRewardsDistributor(newRewardsDistributor);
    }

    function setRewardsDuration(uint256 _rewardsDuration) external onlyOwner {
        _setRewardsDuration(_rewardsDuration);
    }

    function setStakingToken(address newStakingToken) external onlyOwner {
        address oldStakingToken = address(stakingToken);
        if (oldStakingToken != newStakingToken) {
            stakingToken = IAStETH(newStakingToken);
            emit StakingTokenChanged(oldStakingToken, newStakingToken);
        }
    }

    function claimReward() public {
        (uint256 stakedByUser, uint256 totalStaked) = stakingToken.getInternalUserBalanceAndSupply(msg.sender);
        uint256 reward = rewardsState.payDepositorReward(totalStaked, msg.sender, stakedByUser);
        if (reward > 0) {
            REWARD_TOKEN.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    function notifyRewardAmount(uint256 reward, address rewardHolder) external {
        require(msg.sender == rewardsDistributor, "NOT_REWARDS_DISTRIBUTOR");

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
        rewardsState.updateRewardPeriod(totalStaked, _rewardPerSecond, block.timestamp + _rewardsDuration);
        emit RewardAdded(reward);
    }

    function recoverERC20(address tokenAddress, uint256 tokenAmount) external onlyOwner {
        require(tokenAddress != address(stakingToken), "CANT_WITHDRAW_STAKING_TOKEN");
        IERC20(tokenAddress).safeTransfer(owner(), tokenAmount);
        emit Recovered(tokenAddress, tokenAmount);
    }

    // End rewards emission earlier
    function updatePeriodFinish(uint endDate) external onlyOwner {
        uint256 totalStaked = stakingToken.internalTotalSupply();
        rewardsState.updateRewardPeriod(totalStaked, rewardsState.rewardPerSecond, endDate);
    }

    function earned(address depositor) external view returns (uint256) {
        (uint256 staked, uint256 totalStaked) = stakingToken.getInternalUserBalanceAndSupply(depositor);
        return rewardsState.earnedReward(totalStaked, depositor, staked);
    }

    function periodFinish() external view returns (uint256) {
        return rewardsState.endDate;
    }

    function rewardPerSecond() external view returns (uint256) {
        return rewardsState.rewardPerSecond;
    }

    function _setRewardsDuration(uint256 _rewardsDuration) private {
        require(
            block.timestamp > rewardsState.endDate,
            "REWARD_PERIOD_NOT_FINISHED"
        );
        rewardsDuration = _rewardsDuration;
        emit RewardsDurationUpdated(_rewardsDuration);
    }

    function _setRewardsDistributor(address newRewardsDistributor) private {
        address oldRewardsDistributor = rewardsDistributor;
        if (oldRewardsDistributor != newRewardsDistributor) {
            rewardsDistributor = newRewardsDistributor;
            emit RewardsDistributorChanged(oldRewardsDistributor, newRewardsDistributor);
        }
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}