from brownie import ZERO_ADDRESS, reverts, web3
from utils import constants


def typed_solidity_error(error_signature):
    return f"typed error: {web3.keccak(text=error_signature)[:4].hex()}"


def test_incentives_controller_stub_implementation_deploy(
    IncentivesControllerStub, deployer, stranger
):
    incentives_controller_stub_impl = IncentivesControllerStub.deploy(
        {"from": deployer}
    )
    assert incentives_controller_stub_impl.owner() == ZERO_ADDRESS
    assert incentives_controller_stub_impl.version() == 1
    assert incentives_controller_stub_impl.IMPLEMENTATION_VERSION() == 1

    # must revert on attempt to initialize it second time
    with reverts(typed_solidity_error("AlreadyInitialized()")):
        incentives_controller_stub_impl.initialize(stranger, {"from": stranger})

    # must fail on attempt to call upgrade on implementation
    new_incentives_controller_stub_impl = IncentivesControllerStub.deploy(
        {"from": deployer}
    )
    with reverts("Function must be called through delegatecall"):
        incentives_controller_stub_impl.upgradeTo(
            new_incentives_controller_stub_impl, {"from": stranger}
        )

    init_data = new_incentives_controller_stub_impl.initialize.encode_input(stranger)
    with reverts("Function must be called through delegatecall"):
        incentives_controller_stub_impl.upgradeToAndCall(
            new_incentives_controller_stub_impl, init_data, {"from": stranger}
        )


def test_incentives_controller_proxied_deploy(
    Contract,
    ERC1967Proxy,
    IncentivesControllerStub,
    incentives_controller_stub_implementation,
    owner,
    deployer,
):
    data = incentives_controller_stub_implementation.initialize.encode_input(owner)
    proxy = ERC1967Proxy.deploy(
        incentives_controller_stub_implementation, data, {"from": deployer}
    )
    incentives_controller_proxied = Contract.from_abi(
        "IncentivesControllerStub", proxy, IncentivesControllerStub.abi
    )

    assert incentives_controller_proxied.owner() == owner
    assert incentives_controller_proxied.version() == 1
    assert incentives_controller_proxied.IMPLEMENTATION_VERSION() == 1


def test_handle_action(incentives_controller, stranger):
    # must not fail
    incentives_controller.handleAction(ZERO_ADDRESS, 0, 0, {"from": stranger})
