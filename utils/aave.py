from brownie import interface

LENDING_POOL_ADDRESS = "0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9"
LENDING_POOL_CONFIGURATOR_ADDRESS = "0x311Bb771e4F8952E6Da169b425E7e92d6Ac45756"
POOL_ADMIN_ADDRESS = "0xEE56e2B3D491590B5b31738cC34d5232F378a8D5"
WETH9_INTEREST_RATE_STRATEGY_ADDRESS = "0x4ce076b9dD956196b814e54E1714338F18fde3F4"


def lending_pool_configurator(interface=interface):
    return interface.LendingPoolConfigurator(LENDING_POOL_CONFIGURATOR_ADDRESS)


def lending_pool(interface=interface):
    return interface.LendingPool("0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9")
