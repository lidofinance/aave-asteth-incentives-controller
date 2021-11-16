from brownie import Wei
from utils import lido, deployment, config, constants


def main():
    deployer = config.get_deployer_account(config.get_is_live())

    incentives_controller = config.get_env("INCENTIVES_CONTROLLER")
    print("Deployer:", deployer)
    print("Owner:", lido.AGENT_ADDRESS)
    print("Incentives Controller Proxy:", incentives_controller)

    sys.stdout.write("Proceed? [y/n]: ")
    if not config.prompt_bool():
        print("Aborting")
        return

    tx_params = {"from": deployer, "gas_price": Wei("100 gwei")}
    deploy_and_setup_rewards_manager(incentives_controller, tx_params)


def deploy_and_setup_rewards_manager(incentives_controller, tx_params):
    rewards_manager = deployment.deploy_rewards_manager(tx_params=tx_params)
    rewards_manager.set_rewards_contract(incentives_controller, tx_params)
    rewards_manager.transfer_ownership(lido.AGENT_ADDRESS, tx_params)
    return rewards_manager
