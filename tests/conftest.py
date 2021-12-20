import pytest
from utils import lido, aave, deployment


@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    """Snapshot ganache before every test function call."""
    pass


############
# EOA
############


@pytest.fixture(scope="module")
def deployer(accounts):
    return accounts[0]


@pytest.fixture(scope="module")
def owner(accounts):
    return accounts[1]


@pytest.fixture(scope="module")
def depositors(accounts, steth):
    depositors = accounts[2:5]
    for depositor in depositors:
        depositor.transfer(steth, "1 ether")
    return depositors


@pytest.fixture(scope="module")
def stranger(accounts):
    return accounts[6]


@pytest.fixture(scope="module")
def pool_admin(accounts):
    return accounts.at(aave.POOL_ADMIN_ADDRESS, force=True)


@pytest.fixture(scope="module")
def rewards_distributor(accounts):
    return accounts[5]


@pytest.fixture(scope="module")
def agent(accounts):
    return accounts.at(lido.AGENT_ADDRESS, force=True)


############
# CONTRACTS
############


@pytest.fixture(scope="module")
def rewards_utils_wrapper(RewardsUtilsWrapper, deployer):
    return RewardsUtilsWrapper.deploy({"from": deployer})


@pytest.fixture(scope="module")
def rewards_manager(owner):
    return deployment.deploy_rewards_manager({"from": owner})


@pytest.fixture(scope="module")
def incentives_controller(ldo, owner, deployer, rewards_manager):
    return deployment.deploy_incentives_controller(
        reward_token=ldo,
        rewards_distributor=rewards_manager,
        tx_params={"from": deployer},
    )


@pytest.fixture(scope="module")
def ldo(interface):
    return lido.ldo(interface)


@pytest.fixture(scope="module")
def steth(interface):
    return lido.steth(interface)


@pytest.fixture(scope="module")
def lending_pool(interface):
    return aave.lending_pool(interface)


@pytest.fixture(scope="module")
def lending_pool_configurator(interface):
    return aave.lending_pool_configurator(interface)


@pytest.fixture(scope="module")
def asteth_impl(Contract, incentives_controller, lending_pool, steth, deployer):
    return deployment.deploy_asteth_impl(
        lending_pool=lending_pool,
        steth=steth,
        incentives_controller=incentives_controller,
        deployer=deployer,
    )


@pytest.fixture(scope="module")
def variable_debt_steth_impl(lending_pool, steth, deployer):
    return deployment.deploy_variable_debt_steth_impl(
        lending_pool=lending_pool, steth=steth, deployer=deployer
    )


@pytest.fixture(scope="module")
def stable_debt_steth_impl(lending_pool, steth, deployer):
    return deployment.deploy_stable_debt_steth_impl(
        lending_pool=lending_pool, steth=steth, deployer=deployer
    )


@pytest.fixture(scope="module")
def steth_reserve(
    lending_pool,
    lending_pool_configurator,
    asteth_impl,
    stable_debt_steth_impl,
    variable_debt_steth_impl,
    incentives_controller,
    pool_admin,
    steth,
    deployer,
):
    reserve = deployment.add_aave_reserve(
        lending_pool_configurator=lending_pool_configurator,
        lending_pool=lending_pool,
        atoken_impl=asteth_impl,
        stable_debt_token_impl=stable_debt_steth_impl,
        variable_debt_token_impl=variable_debt_steth_impl,
        underlying_asset=steth,
        pool_admin=pool_admin,
        deployer=deployer,
    )
    incentives_controller.initialize(reserve.atoken, {"from": deployer})
    return reserve


@pytest.fixture(scope="module")
def asteth_mock(AStEthMock, deployer):
    return AStEthMock.deploy({"from": deployer})
