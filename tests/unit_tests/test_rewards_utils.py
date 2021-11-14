import pytest
from brownie import Wei, chain
from utils.common import is_almost_equal
from utils.constants import (
    ONE_MONTH,
    ONE_WEEK,
    DEFAULT_REWARDS_DURATION,
    DEFAULT_TOTAL_REWARD,
    DEFAULT_TOTAL_STAKED,
)

PRECISION = 10 ** 18
DEFAULT_REWARD_PER_SECOND = Wei("1000 ether") // DEFAULT_REWARDS_DURATION


def get_end_date(duration=DEFAULT_REWARDS_DURATION):
    return chain[-1].timestamp + duration


def compute_reward_per_token(total_staked, duration, reward_per_second):
    return (PRECISION * duration * reward_per_second) // total_staked


def default_reward_per_token(duration):
    return (PRECISION * duration * DEFAULT_REWARD_PER_SECOND) // DEFAULT_TOTAL_STAKED


@pytest.fixture(scope="function")
def start_reward_period(rewards_utils_wrapper, deployer):
    rewards_utils_wrapper.updateRewardPeriod(
        DEFAULT_TOTAL_STAKED,
        DEFAULT_REWARD_PER_SECOND,
        get_end_date(),
        {"from": deployer},
    )


def test_update_reward_period_start_rewards(rewards_utils_wrapper, deployer):
    """
    Checks that sets correct values on updateRewardPeriod call at first time
    """
    rewards_state = rewards_utils_wrapper.rewardsState().dict()
    # validate that rewards state has initial values
    assert rewards_state["endDate"] == 0
    assert rewards_state["updatedAt"] == 0
    assert rewards_state["rewardPerSecond"] == 0
    assert rewards_state["accumulatedRewardPerToken"] == 0

    end_date = get_end_date()
    rewards_utils_wrapper.updateRewardPeriod(
        DEFAULT_TOTAL_STAKED,
        DEFAULT_REWARD_PER_SECOND,
        end_date,
        {"from": deployer},
    )

    # validate that rewards state was updated correctly
    rewards_state = rewards_utils_wrapper.rewardsState().dict()
    assert rewards_state["endDate"] == end_date
    assert rewards_state["updatedAt"] == chain[-1].timestamp
    assert rewards_state["rewardPerSecond"] == DEFAULT_REWARD_PER_SECOND
    assert rewards_state["accumulatedRewardPerToken"] == 0


@pytest.mark.usefixtures("start_reward_period")
def test_update_reward_period_continue_rewards(rewards_utils_wrapper, deployer):
    """
    Checks that sets correct values on updateRewardPeriod call to continue rewards period
    """
    # wait half of the reward period
    chain.sleep(ONE_MONTH // 2)
    chain.mine()

    # update reward period
    end_date = get_end_date(ONE_WEEK)
    reward_per_second = DEFAULT_TOTAL_REWARD // ONE_WEEK
    rewards_utils_wrapper.updateRewardPeriod(
        DEFAULT_TOTAL_STAKED,
        DEFAULT_TOTAL_REWARD // ONE_WEEK,
        get_end_date(ONE_WEEK),
        {"from": deployer},
    )

    # validate that rewards state was updated correctly
    rewards_state = rewards_utils_wrapper.rewardsState().dict()
    assert rewards_state["endDate"] == end_date
    assert rewards_state["updatedAt"] == chain[-1].timestamp
    assert rewards_state["rewardPerSecond"] == reward_per_second
    expected_reward_per_token = compute_reward_per_token(
        DEFAULT_TOTAL_STAKED, ONE_MONTH // 2, DEFAULT_REWARD_PER_SECOND
    )
    assert is_almost_equal(
        rewards_state["accumulatedRewardPerToken"],
        expected_reward_per_token,
        DEFAULT_REWARD_PER_SECOND,
    )


@pytest.mark.usefixtures("start_reward_period")
def test_update_reward_period_continue_rewards_with_break(
    rewards_utils_wrapper, deployer
):
    """
    Checks that sets correct values on updateRewardPeriod call to continue rewards period
    """
    # wait two reward periods
    chain.sleep(2 * DEFAULT_REWARD_PER_SECOND)
    chain.mine()

    # update reward period
    end_date = get_end_date(ONE_WEEK)
    reward_per_second = DEFAULT_TOTAL_REWARD // ONE_WEEK
    rewards_utils_wrapper.updateRewardPeriod(
        DEFAULT_TOTAL_STAKED, reward_per_second, end_date, {"from": deployer}
    )

    # validate that rewards state was updated correctly
    rewards_state = rewards_utils_wrapper.rewardsState().dict()
    assert rewards_state["endDate"] == end_date
    assert rewards_state["updatedAt"] == chain[-1].timestamp
    assert rewards_state["rewardPerSecond"] == reward_per_second
    expected_reward_per_token = compute_reward_per_token(
        DEFAULT_TOTAL_STAKED, ONE_MONTH, DEFAULT_REWARD_PER_SECOND
    )
    assert is_almost_equal(
        rewards_state["accumulatedRewardPerToken"],
        expected_reward_per_token,
        DEFAULT_REWARD_PER_SECOND,
    )


@pytest.mark.usefixtures("start_reward_period")
def test_update_staker_reward_one_depositor(
    rewards_utils_wrapper, deployer, depositors
):
    # wait one week before first stake
    chain.sleep(ONE_WEEK)
    chain.mine()

    # stake 1 token by depositor
    depositor = depositors[0]
    stake = Wei("1 ether")
    total_staked = DEFAULT_TOTAL_STAKED + stake
    rewards_utils_wrapper.updateDepositorReward(DEFAULT_TOTAL_STAKED, depositor, 0)

    # wait one week
    chain.sleep(ONE_WEEK)
    chain.mine()

    # validate user reward
    expected_reward = (DEFAULT_REWARD_PER_SECOND * ONE_WEEK * stake) // total_staked
    assert is_almost_equal(
        expected_reward,
        rewards_utils_wrapper.earnedReward(total_staked, depositor, stake),
        DEFAULT_REWARD_PER_SECOND,
    )


@pytest.mark.usefixtures("start_reward_period")
def test_update_staker_reward_two_depositor(
    rewards_utils_wrapper, deployer, depositors
):
    [staker1, staker2] = depositors[0:2]
    stake1, stake2 = Wei("1 ether"), Wei("0.5 ether")

    total_staked = DEFAULT_TOTAL_STAKED
    # update rewards for first staker
    rewards_utils_wrapper.updateDepositorReward(total_staked, staker1, 0)
    total_staked += stake1

    # wait one week before staker2 stake
    chain.sleep(ONE_WEEK)
    chain.mine()

    # update rewards for second staker
    rewards_utils_wrapper.updateDepositorReward(total_staked, staker2, 0)
    total_staked += stake2

    # wait one more week
    chain.sleep(ONE_WEEK)
    chain.mine()

    # validate that first staker received correct amount of rewards
    staker1_expected_reward = (DEFAULT_REWARD_PER_SECOND * ONE_WEEK * stake1) // (
        DEFAULT_TOTAL_STAKED + stake1
    ) + (DEFAULT_REWARD_PER_SECOND * ONE_WEEK * stake1) // total_staked
    staker1_actual_reward = rewards_utils_wrapper.earnedReward(
        total_staked, staker1, stake1
    )
    assert is_almost_equal(
        staker1_actual_reward, staker1_expected_reward, DEFAULT_REWARD_PER_SECOND
    )

    # validate that second staker received correct amount of rewards
    staker2_expected_reward = (
        DEFAULT_REWARD_PER_SECOND * ONE_WEEK * stake2
    ) // total_staked
    staker2_actual_reward = rewards_utils_wrapper.earnedReward(
        total_staked, staker2, stake2
    )
    assert is_almost_equal(
        staker2_actual_reward, staker2_expected_reward, DEFAULT_REWARD_PER_SECOND
    )

    # wait three weeks and validate rewards
    chain.sleep(3 * ONE_WEEK)
    chain.mine()

    staker1_expected_reward += (
        DEFAULT_REWARD_PER_SECOND * 16 * 24 * 60 * 60 * stake1
    ) // total_staked
    staker1_actual_reward = rewards_utils_wrapper.earnedReward(
        total_staked, staker1, stake1
    )
    assert is_almost_equal(
        staker1_actual_reward, staker1_expected_reward, DEFAULT_REWARD_PER_SECOND
    )

    staker2_expected_reward += (
        DEFAULT_REWARD_PER_SECOND * 16 * 24 * 60 * 60 * stake2
    ) // total_staked
    staker2_actual_reward = rewards_utils_wrapper.earnedReward(
        total_staked, staker2, stake2
    )
    assert is_almost_equal(
        staker2_actual_reward, staker2_expected_reward, DEFAULT_REWARD_PER_SECOND
    )


@pytest.mark.usefixtures("start_reward_period")
def test_pay_staker_reward(rewards_utils_wrapper, deployer, depositors):
    [staker1, staker2] = depositors[0:2]
    stake1, stake2 = Wei("1 ether"), Wei("0.5 ether")

    total_staked = DEFAULT_TOTAL_STAKED
    # update rewards for first staker
    rewards_utils_wrapper.updateDepositorReward(total_staked, staker1, 0)
    total_staked += stake1

    # wait one week before staker2 stake
    chain.sleep(ONE_WEEK)
    chain.mine()

    staker1_expected_reward = (
        DEFAULT_REWARD_PER_SECOND * ONE_WEEK * stake1
    ) // total_staked
    staker1_actual_reward = rewards_utils_wrapper.earnedReward(
        total_staked, staker1, stake1
    )
    assert is_almost_equal(
        staker1_actual_reward, staker1_expected_reward, DEFAULT_REWARD_PER_SECOND
    )

    # pay reward to user and validate received reward
    tx = rewards_utils_wrapper.payDepositorReward(total_staked, staker1, stake1)
    assert is_almost_equal(
        tx.return_value, staker1_actual_reward, DEFAULT_REWARD_PER_SECOND
    )
    assert rewards_utils_wrapper.earnedReward(total_staked, staker1, stake1) == 0
