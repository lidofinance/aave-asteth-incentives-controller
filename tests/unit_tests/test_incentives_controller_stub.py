from brownie import ZERO_ADDRESS, reverts
from utils import constants, common


def test_incentives_controller_stub_implementation_deploy(
    AaveIncentivesControllerStub, deployer, stranger
):
    incentives_controller_stub_impl = AaveIncentivesControllerStub.deploy(
        {"from": deployer}
    )
    assert incentives_controller_stub_impl.owner() == ZERO_ADDRESS
    assert incentives_controller_stub_impl.initializedVersion() == 1
    assert incentives_controller_stub_impl.IMPLEMENTATION_VERSION() == 1

    # must revert on attempt to initialize it second time
    with reverts(common.typed_solidity_error("AlreadyInitializedError()")):
        incentives_controller_stub_impl.initialize(stranger, {"from": stranger})

    # must fail on attempt to call upgrade on implementation
    new_incentives_controller_stub_impl = AaveIncentivesControllerStub.deploy(
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
    AaveIncentivesControllerStub,
    incentives_controller_stub_implementation,
    owner,
    deployer,
):
    data = incentives_controller_stub_implementation.initialize.encode_input(owner)
    proxy = ERC1967Proxy.deploy(
        incentives_controller_stub_implementation, data, {"from": deployer}
    )
    incentives_controller_proxied = Contract.from_abi(
        "AaveIncentivesControllerStub", proxy, AaveIncentivesControllerStub.abi
    )

    assert incentives_controller_proxied.owner() == owner
    assert incentives_controller_proxied.initializedVersion() == 1
    assert incentives_controller_proxied.IMPLEMENTATION_VERSION() == 1


def test_upgrade(
    incentives_controller,
    incentives_controller_stub_implementation,
    incentives_controller_impl,
    rewards_manager,
    owner,
    stranger,
):
    # must revert when called by stranger
    initialize_data = incentives_controller_impl.initialize.encode_input(
        owner, rewards_manager, constants.DEFAULT_REWARDS_DURATION
    )
    with reverts("Ownable: caller is not the owner"):
        incentives_controller.upgradeToAndCall(
            incentives_controller_impl, initialize_data, {"from": stranger}
        )

    # must revert when called by owner with same version of implementation
    stub_initialize_data = (
        incentives_controller_stub_implementation.initialize.encode_input(owner)
    )
    with reverts(common.typed_solidity_error("AlreadyInitializedError()")):
        incentives_controller.upgradeToAndCall(
            incentives_controller_stub_implementation,
            stub_initialize_data,
            {"from": owner},
        )

    # must pass when called by owner with new version of implementation
    assert incentives_controller.owner() == owner
    assert incentives_controller.initializedVersion() == 1
    assert incentives_controller.IMPLEMENTATION_VERSION() == 1
    incentives_controller.upgradeToAndCall(
        incentives_controller_impl, initialize_data, {"from": owner}
    )
    assert incentives_controller.owner() == owner
    assert incentives_controller.initializedVersion() == 2
    assert incentives_controller.IMPLEMENTATION_VERSION() == 2


def test_handle_action(incentives_controller, stranger):
    # must not fail
    incentives_controller.handleAction(ZERO_ADDRESS, 0, 0, {"from": stranger})
