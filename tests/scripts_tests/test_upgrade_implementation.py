from utils import lido, constants
from brownie import ZERO_ADDRESS, chain, Wei, history
from scripts.upgrade_implementation import start_upgrade_implementation_voting


def test_upgrade_implementation_script(
    Contract,
    AaveAStETHIncentivesController,
    deployer,
    incentives_controller,
    steth_reserve,
    rewards_manager,
    ldo,
    agent,
    owner,
):
    incentives_controller.transferOwnership(agent, {"from": owner})
    ldo.transfer(deployer, Wei(10 ** 18), {"from": agent})
    assert ldo.balanceOf(deployer) == Wei(10 ** 18)

    assert incentives_controller.initializedVersion() == 1
    assert incentives_controller.IMPLEMENTATION_VERSION() == 1

    voting_id, voting_tx = start_upgrade_implementation_voting(
        incentives_controller_proxy=incentives_controller,
        staking_token=steth_reserve.atoken,
        rewards_manager=rewards_manager,
        tx_params={"from": deployer},
    )
    lido.execute_voting(voting_id)

    incentives_controller = Contract.from_abi(
        "AaveAStETHIncentivesController",
        incentives_controller,
        AaveAStETHIncentivesController.abi,
    )

    assert incentives_controller.owner() == agent
    assert incentives_controller.initializedVersion() == 2
    assert incentives_controller.IMPLEMENTATION_VERSION() == 2
    assert incentives_controller.rewardsDistributor() == rewards_manager
    assert incentives_controller.rewardsDuration() == constants.DEFAULT_REWARDS_DURATION
