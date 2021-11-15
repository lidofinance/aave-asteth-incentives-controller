from pathlib import Path
from brownie import (
    Contract,
    ERC1967Proxy,
    RewardsManager,
    AaveAStETHIncentivesController,
    IncentivesControllerStub,
    config,
    ZERO_ADDRESS,
    project,
)
from utils.common import is_almost_equal
from utils import aave, constants

AAVE_DEPENDENCY_NAME = "lidofinance/aave-protocol-v2@1.0+1"


def add_aave_reserve(
    lending_pool_configurator,
    lending_pool,
    atoken_impl,
    stable_debt_token_impl,
    variable_debt_token_impl,
    underlying_asset,
    pool_admin,
    deployer,
):
    lending_pool_configurator.initReserve(
        atoken_impl,
        stable_debt_token_impl,
        variable_debt_token_impl,
        18,
        aave.WETH9_INTEREST_RATE_STRATEGY_ADDRESS,
        {"from": pool_admin},
    )

    reserve_data = lending_pool.getReserveData(underlying_asset)

    [atoken, stable_debt_token_address, variable_debt_token_address] = reserve_data[
        7:10
    ]

    # get atoken with proxy
    atoken = Contract.from_abi("ATokenProxied", atoken, atoken_impl.abi)

    # initialize atoken reference to debt token
    atoken.initializeDebtToken({"from": deployer})

    # get variable debt token with proxy
    variable_debt_token = Contract.from_abi(
        "VariableDebtTokenProxied",
        variable_debt_token_address,
        variable_debt_token_impl.abi,
    )

    # get stable debt token with proxy
    stable_debt_token = Contract.from_abi(
        "StableDebtTokenProxied", stable_debt_token_address, stable_debt_token_impl.abi
    )
    return AaveReserve(
        lending_pool=lending_pool,
        underlying_asset=underlying_asset,
        atoken=atoken,
        variable_debt_token=variable_debt_token,
        stable_debt_token=stable_debt_token,
    )


def deploy_asteth_impl(lending_pool, steth, incentives_controller, deployer):
    AStETH = DependencyLoader.load(AAVE_DEPENDENCY_NAME, "AStETH")
    return AStETH.deploy(
        lending_pool,  # lending pool,
        steth,  # underlying asset
        ZERO_ADDRESS,  # treasury,
        "AAVE stETH",
        "astETH",
        incentives_controller,
        {"from": deployer},
    )


def deploy_variable_debt_steth_impl(lending_pool, steth, deployer):
    VariableDebtStETH = DependencyLoader.load(AAVE_DEPENDENCY_NAME, "VariableDebtStETH")
    return VariableDebtStETH.deploy(
        lending_pool,  # lending pool,
        steth,  # underlying asset
        "Variable debt stETH",
        "variableDebtStETH",
        ZERO_ADDRESS,
        {"from": deployer},
    )


def deploy_stable_debt_steth_impl(lending_pool, steth, deployer):
    StableDebtStETH = DependencyLoader.load(AAVE_DEPENDENCY_NAME, "StableDebtStETH")
    return StableDebtStETH.deploy(
        lending_pool,  # lending pool,
        steth,  # underlying asset
        "Stable debt stETH",
        "stableDebtStETH",
        ZERO_ADDRESS,
        {"from": deployer},
    )


def deploy_incentives_controller_impl(
    reward_token=ZERO_ADDRESS,
    owner=ZERO_ADDRESS,
    rewards_distributor=ZERO_ADDRESS,
    rewards_duration=constants.DEFAULT_REWARDS_DURATION,
    tx_params=None,
):
    return AaveAStETHIncentivesController.deploy(
        reward_token, owner, rewards_distributor, rewards_duration, tx_params
    )


def upgrade_incentives_controller_to_v2(
    proxy,
    implementation,
    owner,
    rewards_distributor,
    rewards_duration=constants.DEFAULT_REWARDS_DURATION,
    tx_params=None,
):
    upgrade_data = implementation.initialize.encode_input(
        owner, rewards_distributor, rewards_duration
    )
    proxy.upgradeToAndCall(implementation, upgrade_data, tx_params)
    incentives_controller = Contract.from_abi(
        "AaveAStETHIncentivesControllerProxied", proxy, implementation.abi
    )
    assert incentives_controller.IMPLEMENTATION_VERSION() == 2
    assert incentives_controller.version() == 2
    return incentives_controller


def deploy_rewards_manager(tx_params):
    return RewardsManager.deploy(tx_params)


def deploy_proxy(implementation, init_data, tx_params):
    proxy = ERC1967Proxy.deploy(implementation, init_data, tx_params)
    return Contract.from_abi("ProxiedImpl", proxy, implementation.abi)


def deploy_incentives_controller_stub_impl(tx_params):
    return IncentivesControllerStub.deploy(tx_params)


class DependencyLoader(object):
    dependencies = {}

    @staticmethod
    def load(dependency_name, contract_name):
        if dependency_name not in DependencyLoader.dependencies:
            dependency_index = config["dependencies"].index(dependency_name)
            DependencyLoader.dependencies[dependency_name] = project.load(
                Path.home()
                / ".brownie"
                / "packages"
                / config["dependencies"][dependency_index]
            )
        return getattr(DependencyLoader.dependencies[dependency_name], contract_name)


class AaveReserve:
    def __init__(
        self,
        lending_pool,
        underlying_asset,
        atoken,
        variable_debt_token,
        stable_debt_token,
    ):
        self.atoken = atoken
        self.underlying_asset = underlying_asset
        self.stable_debt_token = stable_debt_token
        self.variable_debt_token = variable_debt_token
        self.lending_pool = lending_pool

    def deposit(self, depositor, amount):
        underlying_asset_balance_before_deposit = self.underlying_asset.balanceOf(
            depositor
        )
        atoken_balance_before_deposit = self.atoken.balanceOf(depositor)
        self.underlying_asset.approve(self.lending_pool, amount, {"from": depositor})
        tx = self.lending_pool.deposit(
            self.underlying_asset, amount, depositor, 0, {"from": depositor}
        )
        assert is_almost_equal(
            self.atoken.balanceOf(depositor), atoken_balance_before_deposit + amount
        )
        assert is_almost_equal(
            underlying_asset_balance_before_deposit - amount,
            self.underlying_asset.balanceOf(depositor),
        )
        return tx

    def withdraw(self, depositor, amount=constants.MAX_UINT256, epsilon=100):
        initial_underlying_asset_depositor_balance = self.underlying_asset.balanceOf(
            depositor
        )
        initial_atoken_depositor_balance = self.atoken.balanceOf(depositor)
        tx = self.lending_pool.withdraw(
            self.underlying_asset, amount, depositor, {"from": depositor}
        )
        expected_underlying_asset_depositor_balance = (
            initial_underlying_asset_depositor_balance
            + initial_atoken_depositor_balance
            if amount == constants.MAX_UINT256
            else initial_underlying_asset_depositor_balance + amount
        )
        expected_atoken_depositor_balance = (
            0
            if amount == constants.MAX_UINT256
            else initial_atoken_depositor_balance - amount
        )
        assert is_almost_equal(
            self.underlying_asset.balanceOf(depositor),
            expected_underlying_asset_depositor_balance,
            epsilon,
        )
        assert is_almost_equal(
            self.atoken.balanceOf(depositor), expected_atoken_depositor_balance, epsilon
        )
        return tx

    def transfer(self, sender, recipient, amount, epsilon=100):
        initial_sender_balance = self.atoken.balanceOf(sender)
        initial_recipient_balance = self.atoken.balanceOf(recipient)
        tx = self.atoken.transfer(recipient, amount, {"from": sender})
        expected_sender_balance = initial_sender_balance - amount
        expected_recipient_balance = initial_recipient_balance + amount
        assert is_almost_equal(
            self.atoken.balanceOf(sender), expected_sender_balance, epsilon
        )
        assert is_almost_equal(
            self.atoken.balanceOf(recipient), expected_recipient_balance, epsilon
        )
        return tx
