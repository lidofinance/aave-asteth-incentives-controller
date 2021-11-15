from functools import partial
from brownie import Wei, chain
from utils import deployment, common
from utils.constants import (
    ONE_WEEK,
    ONE_MONTH,
    DEFAULT_REWARDS_DURATION,
    DEFAULT_TOTAL_REWARD,
    DEFAULT_REWARD_PER_SECOND,
    MAX_UINT256,
)


def test_happy_path(
    incentives_controller,
    incentives_controller_impl,
    steth_reserve,
    owner,
    rewards_manager,
    agent,
    ldo,
    depositors,
):
    is_almost_equal = partial(
        common.is_almost_equal, epsilon=2 * DEFAULT_REWARD_PER_SECOND
    )
    asteth = steth_reserve.atoken
    lending_pool = steth_reserve.lending_pool
    rewards_manager.set_rewards_contract(incentives_controller, {"from": owner})

    # depositor1 send ether into the pool
    depositor1 = depositors[0]
    deposit1 = Wei("1 ether")
    steth_reserve.deposit(depositor1, deposit1)

    # wait one week before second user deposit
    chain.sleep(ONE_WEEK)
    chain.mine()

    # replace stub implementation in incentives controller with working one
    incentives_controller = deployment.upgrade_incentives_controller_to_v2(
        proxy=incentives_controller,
        implementation=incentives_controller_impl,
        owner=owner,
        rewards_distributor=rewards_manager,
        tx_params={"from": owner},
    )

    # set staking token
    incentives_controller.setStakingToken(steth_reserve.atoken, {"from": owner})
    assert incentives_controller.stakingToken() == steth_reserve.atoken

    # depositor2 send ether into the pool
    depositor2 = depositors[1]
    deposit2 = Wei("0.5 ether")
    steth_reserve.deposit(depositor2, deposit2)

    # wait one week before first reward period
    chain.sleep(ONE_WEEK)
    chain.mine()

    # start new rewards period
    ldo.transfer(rewards_manager, DEFAULT_TOTAL_REWARD, {"from": agent})
    rewards_manager.start_next_rewards_period({"from": owner})

    # wait half of the reward period
    chain.sleep(ONE_MONTH // 2)
    chain.mine()

    # validate that both depositors earned rewards according to their parts in reserve
    depositor1_actual_reward = incentives_controller.earned(depositor1)
    depositor1_expected_reward = Wei("333.33333 ether")
    assert is_almost_equal(depositor1_actual_reward, depositor1_expected_reward)

    depositor2_actual_reward = incentives_controller.earned(depositor2)
    depositor2_expected_reward = Wei("166.66666 ether")
    assert is_almost_equal(depositor2_actual_reward, depositor2_expected_reward)

    # wait till the end of the reward period
    chain.sleep(15 * 24 * 60 * 60)
    chain.mine()
    assert rewards_manager.is_rewards_period_finished()

    # validate that both depositors earned rewards according to their parts in reserve
    depositor1_actual_reward = incentives_controller.earned(depositor1)
    depositor1_expected_reward = Wei("666.666666 ether")
    assert is_almost_equal(depositor1_actual_reward, depositor1_expected_reward)

    depositor2_actual_reward = incentives_controller.earned(depositor2)
    depositor2_expected_reward = Wei("333.33333 ether")
    assert is_almost_equal(depositor2_actual_reward, depositor2_expected_reward)

    # depositor1 claims rewards
    assert ldo.balanceOf(depositor1) == 0
    incentives_controller.claimReward({"from": depositor1})
    assert ldo.balanceOf(depositor1) == depositor1_actual_reward
    assert incentives_controller.earned(depositor1) == 0

    # start next rewards period
    ldo.transfer(rewards_manager, DEFAULT_TOTAL_REWARD, {"from": agent})
    rewards_manager.start_next_rewards_period({"from": owner})

    # depositor2 makes another deposit
    steth_reserve.deposit(depositor2, deposit2)

    # wait half of the period
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    # validate that both depositors earned rewards according to their parts in reserve
    depositor1_actual_reward = incentives_controller.earned(depositor1)
    depositor1_expected_reward = Wei("250 ether")
    assert is_almost_equal(depositor1_actual_reward, depositor1_expected_reward)

    depositor2_actual_reward = incentives_controller.earned(depositor2)
    depositor2_expected_reward = Wei("583.33333 ether")
    assert is_almost_equal(depositor2_actual_reward, depositor2_expected_reward)

    # depositor1 extract asteth from reserve
    steth_reserve.withdraw(depositor1)

    # wait till the end of reward period
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()
    assert rewards_manager.is_rewards_period_finished()

    # validate that both depositors earned rewards according to their parts in reserve
    depositor1_actual_reward = incentives_controller.earned(depositor1)
    depositor1_expected_reward = Wei("250 ether")
    assert is_almost_equal(depositor1_actual_reward, depositor1_expected_reward)

    depositor2_actual_reward = incentives_controller.earned(depositor2)
    depositor2_expected_reward = Wei("1083.33333 ether")
    assert is_almost_equal(depositor2_actual_reward, depositor2_expected_reward)

    # depositor2 claims rewards
    assert ldo.balanceOf(depositor2) == 0
    incentives_controller.claimReward({"from": depositor2})
    assert ldo.balanceOf(depositor2) == depositor2_actual_reward
    assert incentives_controller.earned(depositor2) == 0

    # depositor3 send ether into the pool
    depositor3 = depositors[2]
    deposit3 = Wei("1 ether")
    steth_reserve.deposit(depositor3, deposit3)

    # wait one month without rewards
    chain.sleep(ONE_MONTH)
    chain.mine()

    # start next rewards period
    ldo.transfer(rewards_manager, DEFAULT_TOTAL_REWARD, {"from": agent})
    rewards_manager.start_next_rewards_period({"from": owner})

    # Wait two reward periods before reward claiming
    chain.sleep(2 * DEFAULT_REWARDS_DURATION)
    chain.mine()

    # validate that all depositors earned rewards according to their parts in reserve
    depositor1_actual_reward = incentives_controller.earned(depositor1)
    depositor1_expected_reward = Wei("250 ether")
    assert is_almost_equal(depositor1_actual_reward, depositor1_expected_reward)

    depositor2_actual_reward = incentives_controller.earned(depositor2)
    depositor2_expected_reward = Wei("500 ether")
    assert is_almost_equal(depositor2_actual_reward, depositor2_expected_reward)

    depositor3_actual_reward = incentives_controller.earned(depositor3)
    depositor3_expected_reward = Wei("500 ether")
    assert is_almost_equal(depositor3_actual_reward, depositor3_expected_reward)
