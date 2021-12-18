from brownie import Wei, AaveAStETHIncentivesController
from utils import lido, config


def main():
    deployer = config.get_deployer_account(config.get_is_live())

    staking_token = config.get_env("STAKING_TOKEN")
    incentives_controller_address = config.get_env("INCENTIVES_CONTROLLER")

    print("Deployer:", deployer)
    print("Owner", lido.AGENT_ADDRESS)
    print("Staking Token:", staking_token)
    print("Incentives Controller:", incentives_controller_address)

    sys.stdout.write("Proceed? [y/n]: ")
    if not config.prompt_bool():
        print("Aborting")
        return

    tx_params = {"from": deployer, "gas_price": Wei("100 gwei")}

    incentives_controller = AaveAStETHIncentivesController.at(
        incentives_controller_address
    )
    initialize_and_transfer_ownership(
        incentives_controller=incentives_controller,
        staking_token=staking_token,
        owner=lido.AGENT_ADDRESS,
        tx_params=tx_params,
    )


def initialize_and_transfer_ownership(
    incentives_controller, staking_token, owner, tx_params
):
    incentives_controller.initialize(staking_token, tx_params)
    incentives_controller.transferOwnership(owner, tx_params)
