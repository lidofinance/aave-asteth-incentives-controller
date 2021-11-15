// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import {IERC20} from "../dependencies/openzeppelin/IERC20.sol";
import {Ownable} from "../dependencies/openzeppelin/Ownable.sol";
import {SafeERC20} from "../dependencies/openzeppelin/SafeERC20.sol";
import {UUPSUpgradeable} from "../dependencies/openzeppelin/UUPSUpgradable.sol";
import {StorageSlot} from "../dependencies/openzeppelin/StorageSlot.sol";

import {RewardsUtils} from "../utils/RewardsUtils.sol";
import {UnstructuredStorageVersionised} from "./UnstructuredStorageVersionised.sol";

import {IAStETH} from "../interfaces/IAStETH.sol";
import {IAaveIncentivesController} from "../interfaces/IAaveIncentivesController.sol";

/// @author psirex
/// @notice Upgradable implementation for the IAaveIncentivesController
///     with linear rewards distribution across depositors proportional
///     to their stake size.
contract AaveAStETHIncentivesController is
    UnstructuredStorageVersionised,
    IAaveIncentivesController
{
    using RewardsUtils for RewardsUtils.RewardsState;
    using SafeERC20 for IERC20;

    error NotRewardsDistributorError();
    error RewardsPeriodNotFinishedError();

    event RewardsDistributorChanged(
        address indexed oldRewardsDistributor,
        address indexed newRewardsDistributor
    );
    event RewardAdded(uint256 rewardAmount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardsDurationUpdated(uint256 newDuration);
    event Recovered(address indexed token, uint256 amount);
    event RewardsAccrued(address indexed depositor, uint256 earnedRewards);

    bytes32 private constant REWARDS_DISTRIBUTOR_SLOT =
        keccak256("Lido.AaveAStETHIncentivesController.rewardsDistributor");
    bytes32 private constant REWARDS_DURATION_SLOT =
        keccak256("Lido.AaveAStETHIncentivesController.rewardsDuration");
    bytes32 private constant REWARDS_STATE_SLOT =
        keccak256("Lido.AaveAStETHIncentivesController.rewardsState");

    uint256 private constant _IMPLEMENTATION_VERSION = 2;

    IERC20 public immutable REWARD_TOKEN;
    IAStETH public immutable STAKING_TOKEN;

    constructor(
        address _rewardToken,
        address _stakingToken,
        address _owner,
        address _rewardsDistributor,
        uint256 _rewardsDuration
    ) UnstructuredStorageVersionised(_IMPLEMENTATION_VERSION) {
        REWARD_TOKEN = IERC20(_rewardToken);
        STAKING_TOKEN = IAStETH(_stakingToken);
        initialize(_owner, _rewardsDistributor, _rewardsDuration);
    }

    /// @notice Initializes contract if the current version hasn't initialized yet.
    ///     Transfers ownership to owner, sets rewards distributor and
    ///     sets rewards duration.
    function initialize(
        address owner,
        address _rewardsDistributor,
        uint256 _rewardsDuration
    ) public {
        _initialize(owner);
        _setRewardsDuration(_rewardsDuration);
        _setRewardsDistributor(_rewardsDistributor);
    }

    /// @notice Returns current rewards distributor address
    function rewardsDistributor() external view returns (address) {
        return _getRewardsDistributor();
    }

    /// @notice Returns current rewards duration
    function rewardsDuration() external view returns (uint256) {
        return _getRewardsDuration();
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
        if (msg.sender != address(STAKING_TOKEN)) {
            return;
        }
        uint256 earnedRewards = _getRewardsState().updateDepositorReward(
            totalSupply,
            user,
            userBalance
        );
        if (earnedRewards > 0) {
            emit RewardsAccrued(user, earnedRewards);
        }
    }

    /// @notice Sets the value of rewards distributor. Might be called only by the owner
    function setRewardsDistributor(address newRewardsDistributor) external onlyOwner {
        _setRewardsDistributor(newRewardsDistributor);
    }

    /// @notice Sets the value of rewards duration. Might be called only by the owner
    function setRewardsDuration(uint256 _rewardsDuration) external onlyOwner {
        _setRewardsDuration(_rewardsDuration);
    }

    /// @notice Transfers all earned tokens to the depositor and reset his reward
    function claimReward() public {
        (uint256 stakedByUser, uint256 totalStaked) = STAKING_TOKEN.getInternalUserBalanceAndSupply(
            msg.sender
        );
        uint256 reward = _getRewardsState().payDepositorReward(
            totalStaked,
            msg.sender,
            stakedByUser
        );
        if (reward > 0) {
            REWARD_TOKEN.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    /// @notice Starts reward period to distribute given amount of tokens from the current timestamp
    ///     during rewards duration. If the previous reward period hasn't finished, adds the given
    ///     reward to the previous reward. Might be called only by rewards distributor
    /// @param reward Amount of tokens to distribute on reward period
    /// @param rewardHolder Address to retrieve reward tokens
    function notifyRewardAmount(uint256 reward, address rewardHolder) external {
        if (msg.sender != _getRewardsDistributor()) {
            revert NotRewardsDistributorError();
        }
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
        _getRewardsState().updateRewardPeriod(
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
        uint256 totalStaked = STAKING_TOKEN.internalTotalSupply();
        _getRewardsState().updateRewardPeriod(
            totalStaked,
            _getRewardsState().rewardPerSecond,
            endDate
        );
    }

    /// @notice Returns amount of tokens earned by the depositor
    /// @param depositor Address of the depositor
    function earned(address depositor) external view returns (uint256) {
        (uint256 staked, uint256 totalStaked) = STAKING_TOKEN.getInternalUserBalanceAndSupply(
            depositor
        );
        return _getRewardsState().earnedReward(totalStaked, depositor, staked);
    }

    /// @notice Returns end date of the reward period
    function periodFinish() external view returns (uint256) {
        return _getRewardsState().endDate;
    }

    /// @notice Returns current reward per second
    function rewardPerSecond() external view returns (uint256) {
        return _getRewardsState().rewardPerSecond;
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
        if (block.timestamp <= _getRewardsState().endDate) {
            revert RewardsPeriodNotFinishedError();
        }
        StorageSlot.getUint256Slot(REWARDS_DURATION_SLOT).value = _rewardsDuration;
        emit RewardsDurationUpdated(_rewardsDuration);
    }
}
