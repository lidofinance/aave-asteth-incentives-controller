import pytest
from brownie import reverts, ZERO_ADDRESS, Wei
from brownie.network import history, chain
from utils.common import is_almost_equal
from utils.constants import DEFAULT_REWARDS_DURATION, DEFAULT_TOTAL_REWARD
from utils import deployment, common


@pytest.fixture(scope="function")
def set_incentives_controller(incentives_controller, asteth_mock, deployer):
    asteth_mock.setIncentivesController(incentives_controller, {"from": deployer})


@pytest.fixture(scope="function")
def initialize_incentives_controller(incentives_controller, asteth_mock, deployer):
    incentives_controller.initialize(asteth_mock, {"from": deployer})


def test_deploy(incentives_controller, rewards_manager, ldo, deployer):
    assert incentives_controller.owner() == deployer
    assert incentives_controller.REWARD_TOKEN() == ldo
    assert incentives_controller.stakingToken() == ZERO_ADDRESS
    assert incentives_controller.rewardsDuration() == DEFAULT_REWARDS_DURATION
    assert incentives_controller.rewardsDistributor() == rewards_manager


def test_initialization_by_stranger(stranger, incentives_controller, asteth_mock):
    # validate that can't initialize version twice
    with reverts("Ownable: caller is not the owner"):
        incentives_controller.initialize(asteth_mock, {"from": stranger})


def test_initialization_staking_token_is_not_contract(
    incentives_controller, deployer, stranger
):
    # validate that can't initialize version twice
    with reverts(common.typed_solidity_error("StakingTokenIsNotContractError()")):
        incentives_controller.initialize(stranger, {"from": deployer})


def test_initialize(incentives_controller, deployer, asteth_mock):
    assert incentives_controller.stakingToken() == ZERO_ADDRESS
    tx = incentives_controller.initialize(asteth_mock, {"form": deployer})
    assert incentives_controller.stakingToken() == asteth_mock

    assert tx.events["Initialized"]["stakingToken"] == asteth_mock


@pytest.mark.usefixtures("initialize_incentives_controller")
def test_repeated_initialization(incentives_controller, asteth_impl, deployer):
    # validate that can't initialize version twice
    with reverts(common.typed_solidity_error("AlreadyInitializedError()")):
        incentives_controller.initialize(asteth_impl, {"from": deployer})


def test_set_rewards_distributor(
    incentives_controller, stranger, rewards_distributor, rewards_manager, deployer
):
    # must revert when called by stranger
    with reverts("Ownable: caller is not the owner"):
        incentives_controller.setRewardsDistributor(stranger, {"from": stranger})

    # must set new rewards distributor when called by owner
    assert incentives_controller.rewardsDistributor() == rewards_manager
    tx = incentives_controller.setRewardsDistributor(
        rewards_distributor, {"from": deployer}
    )
    assert incentives_controller.rewardsDistributor() == rewards_distributor
    assert (
        tx.events["RewardsDistributorChanged"]["oldRewardsDistributor"]
        == rewards_manager
    )
    assert (
        tx.events["RewardsDistributorChanged"]["newRewardsDistributor"]
        == rewards_distributor
    )

    # when called with same rewards distributor address must not trigger RewardsDistributorChanged event
    tx = incentives_controller.setRewardsDistributor(
        rewards_distributor, {"from": deployer}
    )
    assert incentives_controller.rewardsDistributor() == rewards_distributor
    assert "RewardsDistributorChanged" not in tx.events


@pytest.mark.usefixtures("initialize_incentives_controller")
def test_set_rewards_duration(
    incentives_controller, stranger, deployer, agent, ldo, rewards_manager
):
    # must revert when called by stranger
    with reverts("Ownable: caller is not the owner"):
        incentives_controller.setRewardsDuration(
            DEFAULT_REWARDS_DURATION, {"from": stranger}
        )

    # must set rewards duration when called by owner and prev rewards period are finished
    assert incentives_controller.rewardsDuration() == DEFAULT_REWARDS_DURATION
    new_rewards_duration = DEFAULT_REWARDS_DURATION
    tx = incentives_controller.setRewardsDuration(
        new_rewards_duration, {"from": deployer}
    )
    assert incentives_controller.rewardsDuration() == new_rewards_duration
    assert tx.events["RewardsDurationUpdated"]["newDuration"] == new_rewards_duration

    # must revert if called by owner if previous reward hasn't finished yet
    ldo.approve(incentives_controller, DEFAULT_TOTAL_REWARD, {"from": agent})
    incentives_controller.setRewardsDistributor(rewards_manager, {"from": deployer})
    incentives_controller.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_manager}
    )
    assert incentives_controller.periodFinish() >= chain[-1].timestamp
    with reverts(common.typed_solidity_error("RewardsPeriodNotFinishedError()")):
        incentives_controller.setRewardsDuration(
            DEFAULT_REWARDS_DURATION, {"from": deployer}
        )


@pytest.mark.usefixtures("initialize_incentives_controller")
def test_notify_reward_amount(
    incentives_controller, ldo, agent, stranger, rewards_manager
):
    # must revert when called not by rewards distributor
    with reverts(common.typed_solidity_error("NotRewardsDistributorError()")):
        incentives_controller.notifyRewardAmount(
            DEFAULT_TOTAL_REWARD, agent, {"from": stranger}
        )

    # must calculate rewards correct when called on ended reward period
    ldo.approve(incentives_controller, DEFAULT_TOTAL_REWARD, {"from": agent})
    tx = incentives_controller.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_manager}
    )
    assert (
        incentives_controller.periodFinish()
        == chain[-1].timestamp + DEFAULT_REWARDS_DURATION
    )
    assert (
        incentives_controller.rewardPerSecond()
        == DEFAULT_TOTAL_REWARD // DEFAULT_REWARDS_DURATION
    )
    assert tx.events["RewardAdded"]["rewardAmount"] == DEFAULT_TOTAL_REWARD

    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    # must calculate rewards correct when called on not ended reward period
    assert incentives_controller.periodFinish() > chain[-1].timestamp
    ldo.approve(incentives_controller, DEFAULT_TOTAL_REWARD, {"from": agent})
    tx = incentives_controller.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_manager}
    )
    expected_reward_per_second = (
        DEFAULT_TOTAL_REWARD + DEFAULT_TOTAL_REWARD // 2
    ) // DEFAULT_REWARDS_DURATION
    assert is_almost_equal(
        incentives_controller.rewardPerSecond(),
        expected_reward_per_second,
        epsilon=Wei("1 gwei"),
    )
    assert (
        incentives_controller.periodFinish()
        == chain[-1].timestamp + DEFAULT_REWARDS_DURATION
    )


def test_recover_erc20(incentives_controller, deployer, stranger, ldo, agent):
    # must revert when called by stranger
    recover_amount = Wei("500 ether")
    with reverts("Ownable: caller is not the owner"):
        incentives_controller.recoverERC20(ldo, recover_amount, {"from": stranger})

    ldo.transfer(incentives_controller, DEFAULT_TOTAL_REWARD, {"from": agent})
    assert ldo.balanceOf(incentives_controller) == DEFAULT_TOTAL_REWARD

    # must transfer recover amount to owner address
    assert ldo.balanceOf(deployer) == 0
    tx = incentives_controller.recoverERC20(ldo, recover_amount, {"from": deployer})
    assert ldo.balanceOf(incentives_controller) == DEFAULT_TOTAL_REWARD - recover_amount
    assert ldo.balanceOf(deployer) == recover_amount
    assert tx.events["Recovered"]["token"] == ldo
    assert tx.events["Recovered"]["amount"] == recover_amount


@pytest.mark.usefixtures(
    "initialize_incentives_controller", "set_incentives_controller"
)
def test_update_period_finish(
    incentives_controller,
    ldo,
    agent,
    rewards_manager,
    depositors,
    asteth_mock,
    deployer,
):
    ldo.approve(incentives_controller, DEFAULT_TOTAL_REWARD, {"from": agent})
    incentives_controller.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_manager}
    )

    depositor = depositors[0]
    deposit = Wei("1 ether")
    asteth_mock.mint(depositor, deposit, {"from": depositor})

    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    depositor_reward_before = incentives_controller.earned(depositor)
    assert is_almost_equal(
        depositor_reward_before,
        Wei(500 * 10 ** 18),
        incentives_controller.rewardPerSecond(),
    )

    # set end to next block
    new_period_finish = chain[-1].timestamp + 1
    incentives_controller.updatePeriodFinish(new_period_finish, {"from": deployer})
    assert incentives_controller.periodFinish() == new_period_finish

    # wait some time after updating of period finish
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    depositor_reward_after = incentives_controller.earned(depositor)
    assert is_almost_equal(
        depositor_reward_before,
        depositor_reward_after,
        incentives_controller.rewardPerSecond(),
    )


@pytest.mark.usefixtures(
    "initialize_incentives_controller", "set_incentives_controller"
)
def test_handle_action(
    incentives_controller, asteth_mock, rewards_manager, depositors, ldo, agent
):
    # start new rewards period
    ldo.approve(incentives_controller, DEFAULT_TOTAL_REWARD, {"from": agent})
    tx = incentives_controller.notifyRewardAmount(
        DEFAULT_TOTAL_REWARD, agent, {"from": rewards_manager}
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
        incentives_controller.earned(depositor1),
        Wei("500 ether"),
        incentives_controller.rewardPerSecond(),
    )

    # simulate withdraw
    tx = asteth_mock.burn(depositor1, deposit1)
    chain.sleep(DEFAULT_REWARDS_DURATION // 2)
    chain.mine()

    assert tx.events["RewardsAccrued"]["depositor"] == depositor1
    assert is_almost_equal(
        tx.events["RewardsAccrued"]["earnedRewards"],
        Wei("500 ether"),
        incentives_controller.rewardPerSecond(),
    )

    # must do nothing when called not by staking token
    tx = incentives_controller.handleAction(
        depositor1, Wei("1 ether"), Wei("1 ether"), {"from": depositor1}
    )
    assert "RewardsAccrued" not in tx.events
