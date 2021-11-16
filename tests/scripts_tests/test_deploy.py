from scripts.deploy import deploy_stub_incentives_controller
from utils import lido
from brownie import ZERO_ADDRESS


def test_deploy(deployer):
    (
        incentives_controller_stub_impl,
        proxied_incentives_controller,
    ) = deploy_stub_incentives_controller(tx_params={"from": deployer})

    # validate incentives controller implementation
    assert incentives_controller_stub_impl.periodFinish() == 0
    assert incentives_controller_stub_impl.owner() == ZERO_ADDRESS
    assert incentives_controller_stub_impl.initializedVersion() == 1
    assert incentives_controller_stub_impl.IMPLEMENTATION_VERSION() == 1

    # validate incentives controller
    assert proxied_incentives_controller.periodFinish() == 0
    assert proxied_incentives_controller.owner() == lido.AGENT_ADDRESS
    assert proxied_incentives_controller.initializedVersion() == 1
    assert proxied_incentives_controller.IMPLEMENTATION_VERSION() == 1
