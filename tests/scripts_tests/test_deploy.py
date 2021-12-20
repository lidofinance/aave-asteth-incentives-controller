from utils import lido, constants
from brownie import ZERO_ADDRESS, chain
from scripts.deploy import deploy_rewards_manager_and_incentives_controller


def test_deploy(deployer):
    (
        rewards_manager,
        incentives_controller,
    ) = deploy_rewards_manager_and_incentives_controller({"from": deployer})

    # validate incentives controller
    assert incentives_controller.owner() == deployer
    assert incentives_controller.periodFinish() == 0
    assert incentives_controller.stakingToken() == ZERO_ADDRESS
    assert incentives_controller.rewardsDistributor() == rewards_manager
    assert incentives_controller.rewardsDuration() == constants.DEFAULT_REWARDS_DURATION

    # validate rewards_manager
    assert rewards_manager.owner() == lido.AGENT_ADDRESS
    assert rewards_manager.rewards_contract() == incentives_controller
    assert rewards_manager.period_finish() == incentives_controller.periodFinish()
    is_rewards_period_finished = (
        chain[-1].timestamp >= incentives_controller.periodFinish()
    )
    assert rewards_manager.is_rewards_period_finished() == is_rewards_period_finished
