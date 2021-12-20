from scripts.deploy_incentives_controller import deploy_incentives_controller
from scripts.initialize_staking_token import initialize_and_transfer_ownership
from utils import lido, constants
from brownie import ZERO_ADDRESS


def test_deploy(deployer, rewards_distributor, asteth_mock, owner):

    incentives_controller = deploy_incentives_controller(
        rewards_distributor=rewards_distributor, tx_params={"from": deployer}
    )
    initialize_and_transfer_ownership(
        incentives_controller,
        staking_token=asteth_mock,
        owner=owner,
        tx_params={"from": deployer},
    )

    # validate incentives controller
    assert incentives_controller.stakingToken() == asteth_mock
    assert incentives_controller.owner() == owner
