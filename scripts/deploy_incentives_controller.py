from brownie import Wei
from utils import lido, deployment, config, constants


def main():
    deployer = config.get_deployer_account(config.get_is_live())
    rewards_manager = config.get_env("REWARDS_MANAGER")

    print("Deployer:", deployer)
    print("Rewards Manager:", rewards_manager)
    print("Rewards Duration:", constants.DEFAULT_REWARDS_DURATION)

    sys.stdout.write("Proceed? [y/n]: ")
    if not config.prompt_bool():
        print("Aborting")
        return

    tx_params = {"from": deployer, "gas_price": Wei("100 gwei")}

    deploy_incentives_controller(rewards_manager, tx_params)


def deploy_incentives_controller(rewards_distributor, tx_params):
    incentives_controller = deployment.deploy_incentives_controller(
        reward_token=lido.LDO_ADDRESS,
        rewards_distributor=rewards_distributor,
        rewards_duration=constants.DEFAULT_REWARDS_DURATION,
        tx_params=tx_params,
    )
    return incentives_controller
