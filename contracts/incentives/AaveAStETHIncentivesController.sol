// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import { RewardsUtils } from '../utils/RewardsUtils.sol';
import { IAStETH } from '../interfaces/IAStETH.sol';
import { IERC20 } from '../dependencies/openzeppelin/IERC20.sol';
import { Ownable } from '../dependencies/openzeppelin/Ownable.sol';
import { SafeERC20 } from '../dependencies/openzeppelin/SafeERC20.sol';
import { UUPSUpgradeable } from '../dependencies/openzeppelin/UUPSUpgradable.sol';
import { StorageSlot } from '../dependencies/openzeppelin/StorageSlot.sol';

contract AaveAStETHIncentivesController is Ownable, UUPSUpgradeable {
    using RewardsUtils for RewardsUtils.RewardsState;
    using SafeERC20 for IERC20;
    
    event RewardsDistributorChanged(address indexed oldRewardsDistributor, address indexed newRewardsDistributor);
    event RewardAdded(uint256 rewardAmount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardsDurationUpdated(uint256 newDuration);
    event Recovered(address indexed token, uint256 amount);
    event RewardsAccrued(address indexed depositor, uint256 earnedRewards);

    bytes32 private constant VERSION_SLOT = keccak256('Lido.AaveAStETHIncentivesController.version');
    bytes32 private constant REWARDS_DISTRIBUTOR_SLOT = keccak256('Lido.AaveAStETHIncentivesController.rewardsDistributor');
    bytes32 private constant REWARDS_DURATION_SLOT = keccak256('Lido.AaveAStETHIncentivesController.rewardsDuration');
    bytes32 private constant REWARDS_STATE_SLOT = keccak256('Lido.AaveAStETHIncentivesController.rewardsState');

    uint256 public constant IMPLEMENTATION_VERSION = 2;
    IERC20 public immutable REWARD_TOKEN;
    IAStETH public immutable STAKING_TOKEN;

    constructor(address _rewardToken, address _stakingToken, address _owner, address _rewardsDistributor, uint256 _rewardsDuration) {
        REWARD_TOKEN = IERC20(_rewardToken);
        STAKING_TOKEN = IAStETH(_stakingToken);
        // initialize logic with zero address as owner
        // to prevent access to admin methods of implementaiton
        initialize(_owner, _rewardsDistributor, _rewardsDuration);
    }

    function initialize(address owner, address _rewardsDistributor, uint256 _rewardsDuration) public {
        require(_getVersion() != IMPLEMENTATION_VERSION, 'ALREADY_INITIALIZED');
        _setVersion(IMPLEMENTATION_VERSION);
        _transferOwnership(owner);
        _setRewardsDuration(_rewardsDuration);
        _setRewardsDistributor(_rewardsDistributor);
    }

    function version() external view returns (uint256) {
        return _getVersion();
    }

    function rewardsDistributor() external view returns (address) {
        return _getRewardsDistributor();
    }

    function rewardsDuration() external view returns (uint256) {
        return _getRewardsDuration();
    }

    function handleAction(
      address user,
      uint256 totalSupply,
      uint256 userBalance
    ) external {
        if (msg.sender != address(STAKING_TOKEN)) {
            return;
        }
        uint256 earnedRewards = _getRewardsState().updateDepositorReward(totalSupply, user, userBalance);
        if (earnedRewards > 0) {
            emit RewardsAccrued(user, earnedRewards);
        }
    }

    function depositorRewards(address depositor) external view returns (RewardsUtils.Reward memory) {
        return _getRewardsState().rewards[depositor];
    }

    function setRewardsDistributor(address newRewardsDistributor) external onlyOwner {
        _setRewardsDistributor(newRewardsDistributor);
    }

    function setRewardsDuration(uint256 _rewardsDuration) external onlyOwner {
        _setRewardsDuration(_rewardsDuration);
    }

    function claimReward() public {
        (uint256 stakedByUser, uint256 totalStaked) = STAKING_TOKEN.getInternalUserBalanceAndSupply(msg.sender);
        uint256 reward = _getRewardsState().payDepositorReward(totalStaked, msg.sender, stakedByUser);
        if (reward > 0) {
            REWARD_TOKEN.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    function notifyRewardAmount(uint256 reward, address rewardHolder) external {
        require(msg.sender == _getRewardsDistributor(), "NOT_REWARDS_DISTRIBUTOR");

        REWARD_TOKEN.safeTransferFrom(rewardHolder, address(this), reward);
        uint256 _periodFinish = _getRewardsState().endDate;
        uint256 _rewardsDuration = _getRewardsDuration();
        uint256 _rewardPerSecond = 0;
        if (block.timestamp >= _periodFinish) {
            _rewardPerSecond = reward / _rewardsDuration;
        } else {
            uint256 remaining = _periodFinish - block.timestamp;
            uint256 leftover = remaining * _getRewardsState().rewardPerSecond;
            _rewardPerSecond = (reward + leftover) / _rewardsDuration;
        }
        uint256 totalStaked = STAKING_TOKEN.internalTotalSupply();
        _getRewardsState().updateRewardPeriod(totalStaked, _rewardPerSecond, block.timestamp + _rewardsDuration);
        emit RewardAdded(reward);
    }

    function recoverERC20(address tokenAddress, uint256 tokenAmount) external onlyOwner {
        require(tokenAddress != address(STAKING_TOKEN), "CANT_WITHDRAW_STAKING_TOKEN");
        IERC20(tokenAddress).safeTransfer(owner(), tokenAmount);
        emit Recovered(tokenAddress, tokenAmount);
    }

    // End rewards emission earlier
    function updatePeriodFinish(uint endDate) external onlyOwner {
        uint256 totalStaked = STAKING_TOKEN.internalTotalSupply();
        _getRewardsState().updateRewardPeriod(totalStaked, _getRewardsState().rewardPerSecond, endDate);
    }

    function earned(address depositor) external view returns (uint256) {
        (uint256 staked, uint256 totalStaked) = STAKING_TOKEN.getInternalUserBalanceAndSupply(depositor);
        return _getRewardsState().earnedReward(totalStaked, depositor, staked);
    }

    function periodFinish() external view returns (uint256) {
        return _getRewardsState().endDate;
    }

    function rewardPerSecond() external view returns (uint256) {
        return _getRewardsState().rewardPerSecond;
    }

    function _getVersion() private view returns (uint256) {
        return StorageSlot.getUint256Slot(VERSION_SLOT).value;
    } 

    function _setVersion(uint256 newVersion) private {
        StorageSlot.getUint256Slot(VERSION_SLOT).value = newVersion;
    }

    function _getRewardsDistributor() private view returns (address) {
        return StorageSlot.getAddressSlot(REWARDS_DISTRIBUTOR_SLOT).value;
    }

    function _setRewardsDistributor(address newRewardsDistributor) private {
        address oldRewardsDistributor = _getRewardsDistributor();
        if (oldRewardsDistributor != newRewardsDistributor) {
            StorageSlot.getAddressSlot(REWARDS_DISTRIBUTOR_SLOT).value = newRewardsDistributor;
            emit RewardsDistributorChanged(oldRewardsDistributor, newRewardsDistributor);
        }
    }

    function _getRewardsState() private pure returns (RewardsUtils.RewardsState storage result) {
        bytes32 rewards_state_slot = REWARDS_STATE_SLOT;
        assembly {
            result.slot := rewards_state_slot
        }
    }

    function _getRewardsDuration() private view returns (uint256) {
        return StorageSlot.getUint256Slot(REWARDS_DURATION_SLOT).value;
    }

    function _setRewardsDuration(uint256 _rewardsDuration) private {
        require(
            block.timestamp > _getRewardsState().endDate,
            "REWARD_PERIOD_NOT_FINISHED"
        );
        StorageSlot.getUint256Slot(REWARDS_DURATION_SLOT).value = _rewardsDuration;
        emit RewardsDurationUpdated(_rewardsDuration);
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}
}