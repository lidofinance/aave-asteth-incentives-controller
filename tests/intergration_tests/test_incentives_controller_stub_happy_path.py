from brownie import Wei, chain
from utils.constants import ONE_WEEK


def test_incentives_controller_stub(
    incentives_controller, steth_reserve, lending_pool, steth, depositors
):
    # depositor1 send ether into the pool
    depositor1 = depositors[0]
    deposit1 = Wei("1 ether")
    steth_reserve.deposit(depositor1, deposit1)

    # depositor2 send ether into the pool
    depositor2 = depositors[1]
    deposit2 = Wei("0.5 ether")
    steth_reserve.deposit(depositor2, deposit2)

    # wait one week before transfer
    chain.sleep(ONE_WEEK)
    chain.mine()

    # depositor1 sends 0.5 ether to the depositor2
    steth_reserve.transfer(depositor1, depositor2, deposit2)

    # wait one more week before depositor1 withdraws
    chain.sleep(ONE_WEEK)
    chain.mine()

    # depositor1 withdraws all his steth from reserve
    steth_reserve.withdraw(depositor1)

    # wait one more week before depositor2 withdraws
    chain.sleep(ONE_WEEK)
    chain.mine()

    # depositor2 withdraws half of his steth from reserve
    steth_reserve.withdraw(depositor2, deposit2)

    # depositor2 withdraws other half of his steth from reserve
    steth_reserve.withdraw(depositor2, deposit2)
