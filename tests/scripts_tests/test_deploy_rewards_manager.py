from scripts.deploy_rewards_manager import deploy_and_setup_rewards_manager
from utils import lido
from brownie import ZERO_ADDRESS, chain


def test_deploy_rewards_manager(deployer, incentives_controller):
    rewards_manager = deploy_and_setup_rewards_manager(
        incentives_controller=incentives_controller, tx_params={"from": deployer}
    )

    assert rewards_manager.owner() == lido.AGENT_ADDRESS
    assert rewards_manager.rewards_contract() == incentives_controller
    assert rewards_manager.period_finish() == incentives_controller.periodFinish()
    is_rewards_period_finished = (
        chain[-1].timestamp >= incentives_controller.periodFinish()
    )
    assert rewards_manager.is_rewards_period_finished() == is_rewards_period_finished
