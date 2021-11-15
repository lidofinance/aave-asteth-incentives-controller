import pytest
from brownie import reverts, ZERO_ADDRESS, Wei
from brownie.network import history, chain
from utils.common import is_almost_equal
from utils.constants import DEFAULT_REWARDS_DURATION, DEFAULT_TOTAL_REWARD


@pytest.fixture(scope="function")
def set_staking_token(incentives_controller_impl, asteth_mock, owner):
    incentives_controller_impl.setStakingToken(asteth_mock, {"from": owner})


def test_deploy(
    incentives_controller_impl,
    rewards_manager,
    ldo,
    stranger,
    owner,
    rewards_distributor,
):
    assert incentives_controller_impl.owner() == owner
    assert incentives_controller_impl.REWARD_TOKEN() == ldo
    assert incentives_controller_impl.version() == 2
    assert incentives_controller_impl.rewardsDuration() == DEFAULT_REWARDS_DURATION
    assert incentives_controller_impl.rewardsDistributor() == rewards_distributor

    # validate that can't initialize version twice
    with reverts("ALREADY_INITIALIZED"):
        incentives_controller_impl.initialize(
            stranger, ZERO_ADDRESS, 0, {"from": stranger}
        )


def test_set_rewards_distributor(
    incentives_controller_impl, stranger, rewards_distributor, rewards_manager, owner
):
    # must revert when called by stranger
    with reverts("Ownable: caller is not the owner"):
        incentives_controller_impl.setRewardsDistributor(stranger, {"from": stranger})

    # must set new rewards distributor when called by owner
    assert incentives_controller_impl.rewardsDistributor() == rewards_distributor
    tx = incentives_controller_impl.setRewardsDistributor(
        rewards_manager, {"from": owner}
    )
    assert incentives_controller_impl.rewardsDistributor() == rewards_manager
    assert (
        tx.events["RewardsDistributorChanged"]["oldRewardsDistributor"]
        == rewards_distributor
    )
    assert (
        tx.events["RewardsDistributorChanged"]["newRewardsDistributor"]
        == rewards_manager
    )

    # when called with same rewards distributor address must not trigger RewardsDistributorChanged event
    tx = incentives_controller_impl.setRewardsDistributor(
        rewards_manager, {"from": owner}
    )
    assert incentives_controller_impl.rewardsDistributor() == rewards_manager
    assert "RewardsDistributorChanged" not in tx.events


def test_set_staking_token(incentives_controller_impl, owner, stranger, asteth_mock):
    # must revert when called by stranger
    with reverts("Ownable: caller is not the owner"):
        incentives_controller_impl.setStakingToken(asteth_mock, {"from": stranger})

    # must set staking token when called by owner
    assert incentives_controller_impl.stakingToken() == ZERO_ADDRESS
    tx = incentives_controller_impl.setStakingToken(asteth_mock, {"from": owner})
    assert incentives_controller_impl.stakingToken() == asteth_mock
    assert tx.events["StakingTokenChanged"]["oldStakingToken"] == ZERO_ADDRESS
    assert tx.events["StakingTokenChanged"]["newStakingToken"] == asteth_mock

    # when called with same address of staking token must not trigger StakingTokenChanged event
    tx = incentives_controller_impl.setStakingToken(asteth_mock, {"from": owner})
    assert incentives_controller_impl.stakingToken() == asteth_mock
    assert "StakingTokenChanged" not in tx.events


@pytest.mark.usefixtures("set_staking_token")
def test_set_rewards_duration(
    incentives_controller_impl,
    stranger,
    owner,
    ldo,
    agent,
    rewards_distributor,
    asteth_mock,
):
    # must revert when called by stranger
    with reverts("Ownable: caller is not the owner"):
        incentives_controller_impl.setRewardsDuration(
            DEFAULT_REWARDS_DURATION, {"from": stranger}
        )

    # must set rewards duration when called by owner and prev rewards period are finished
    assert incentives_controller_impl.rewardsDuration() == DEFAULT_REWARDS_DURATION
    new_rewards_duration = DEFAULT_REWARDS_DURATION
    tx = incentives_controller_impl.setRewardsDuration(
        new_rewards_duration, {"from": owner}
    )
    assert incentives_controller_impl.rewardsDuration() == new_rewards_duration
    assert tx.events["RewardsDurationUpdated"]["newDuration"] == new_rewards_duration

    # must revert if called by owner if previous reward hasn't finished yet
    ldo.approve(incentives_controller_impl, DEFAULT_TOTAL_REWARD, {"from": agent})
    incentives_controller_impl.setRewardsDistributor(
        rewards_distributor, {"from": owner}
    )
    incentives_controller_impl.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_distributor}
    )
    assert incentives_controller_impl.periodFinish() >= chain[-1].timestamp
    with reverts("REWARD_PERIOD_NOT_FINISHED"):
        incentives_controller_impl.setRewardsDuration(
            DEFAULT_REWARDS_DURATION, {"from": owner}
        )


@pytest.mark.usefixtures("set_staking_token")
def test_notify_reward_amount(
    incentives_controller_impl, ldo, agent, owner, stranger, rewards_distributor
):
    # must revert when called not by rewards distributor
    with reverts("NOT_REWARDS_DISTRIBUTOR"):
        incentives_controller_impl.notifyRewardAmount(
            DEFAULT_TOTAL_REWARD, agent, {"from": stranger}
        )

    # must calculate rewards correct when called on ended reward period
    ldo.approve(incentives_controller_impl, DEFAULT_TOTAL_REWARD, {"from": agent})
    tx = incentives_controller_impl.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_distributor}
    )
    assert (
        incentives_controller_impl.periodFinish()
        == chain[-1].timestamp + DEFAULT_REWARDS_DURATION
    )
    assert (
        incentives_controller_impl.rewardPerSecond()
        == DEFAULT_TOTAL_REWARD // DEFAULT_REWARDS_DURATION
    )
    assert tx.events["RewardAdded"]["rewardAmount"] == DEFAULT_TOTAL_REWARD

    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    # must calculate rewards correct when called on not ended reward period
    assert incentives_controller_impl.periodFinish() > chain[-1].timestamp
    ldo.approve(incentives_controller_impl, DEFAULT_TOTAL_REWARD, {"from": agent})
    tx = incentives_controller_impl.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_distributor}
    )
    expected_reward_per_second = (
        DEFAULT_TOTAL_REWARD + DEFAULT_TOTAL_REWARD // 2
    ) // DEFAULT_REWARDS_DURATION
    assert is_almost_equal(
        incentives_controller_impl.rewardPerSecond(),
        expected_reward_per_second,
        epsilon=Wei("1 gwei"),
    )
    assert (
        incentives_controller_impl.periodFinish()
        == chain[-1].timestamp + DEFAULT_REWARDS_DURATION
    )


def test_recover_erc20(incentives_controller_impl, owner, stranger, ldo, agent):
    # must revert when called by stranger
    recover_amount = Wei("500 ether")
    with reverts("Ownable: caller is not the owner"):
        incentives_controller_impl.recoverERC20(ldo, recover_amount, {"from": stranger})

    ldo.transfer(incentives_controller_impl, DEFAULT_TOTAL_REWARD, {"from": agent})
    assert ldo.balanceOf(incentives_controller_impl) == DEFAULT_TOTAL_REWARD

    # must transfer recover amount to owner address
    assert ldo.balanceOf(owner) == 0
    tx = incentives_controller_impl.recoverERC20(ldo, recover_amount, {"from": owner})
    assert (
        ldo.balanceOf(incentives_controller_impl)
        == DEFAULT_TOTAL_REWARD - recover_amount
    )
    assert ldo.balanceOf(owner) == recover_amount
    assert tx.events["Recovered"]["token"] == ldo
    assert tx.events["Recovered"]["amount"] == recover_amount


@pytest.mark.usefixtures("set_staking_token")
def test_update_period_finish(
    incentives_controller_impl,
    ldo,
    agent,
    rewards_distributor,
    depositors,
    lending_pool,
    steth,
    asteth_mock,
    owner,
):
    ldo.approve(incentives_controller_impl, DEFAULT_TOTAL_REWARD, {"from": agent})
    incentives_controller_impl.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_distributor}
    )

    depositor = depositors[0]
    deposit = Wei("1 ether")
    asteth_mock.mint(depositor, deposit, {"from": depositor})

    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    depositor_reward_before = incentives_controller_impl.earned(depositor)
    assert is_almost_equal(
        depositor_reward_before,
        Wei(500 * 10 ** 18),
        incentives_controller_impl.rewardPerSecond(),
    )

    # set end to next block
    new_period_finish = chain[-1].timestamp + 1
    incentives_controller_impl.updatePeriodFinish(new_period_finish, {"from": owner})
    assert incentives_controller_impl.periodFinish() == new_period_finish

    # wait some time after updating of period finish
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    depositor_reward_after = incentives_controller_impl.earned(depositor)
    assert is_almost_equal(
        depositor_reward_before,
        depositor_reward_after,
        incentives_controller_impl.rewardPerSecond(),
    )


@pytest.mark.usefixtures("set_staking_token")
def test_handle_action(
    incentives_controller_impl,
    owner,
    asteth_mock,
    rewards_distributor,
    depositors,
    ldo,
    agent,
):
    # start new rewards period
    ldo.approve(incentives_controller_impl, DEFAULT_TOTAL_REWARD, {"from": agent})
    tx = incentives_controller_impl.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_distributor}
    )

    depositor1 = depositors[0]
    deposit1 = Wei("1 ether")
    tx = asteth_mock.mint(depositor1, deposit1)
    # on first deposit earned reward must be equal to zero
    assert "RewardsAccrued" not in tx.events

    # wait half of the reward period
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    assert is_almost_equal(
        incentives_controller_impl.earned(depositor1),
        Wei("500 ether"),
        incentives_controller_impl.rewardPerSecond(),
    )

    # simulate withdraw
    tx = asteth_mock.burn(depositor1, deposit1)
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    assert tx.events["RewardsAccrued"]["depositor"] == depositor1
    assert is_almost_equal(
        tx.events["RewardsAccrued"]["earnedRewards"],
        Wei("500 ether"),
        incentives_controller_impl.rewardPerSecond(),
    )

    # must do nothing when called not by staking token
    tx = incentives_controller_impl.handleAction(
        depositor1, Wei("1 ether"), Wei("1 ether"), {"from": depositor1}
    )
    assert "RewardsAccrued" not in tx.events