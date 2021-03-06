from brownie import Wei
from utils import lido, deployment, config, constants


def main():
    deployer = config.get_deployer_account(config.get_is_live())
    print("Deployer:", deployer)
    print("Owner:", lido.AGENT_ADDRESS)
    print("Reward Token:", lido.LDO_ADDRESS)
    print("Rewards Duration:", constants.DEFAULT_REWARDS_DURATION)

    sys.stdout.write("Proceed? [y/n]: ")
    if not config.prompt_bool():
        print("Aborting")
        return

    tx_params = {"from": deployer, "gas_price": Wei("100 gwei")}
    deploy_rewards_manager_and_incentives_controller(tx_params)


def deploy_rewards_manager_and_incentives_controller(tx_params):
    rewards_manager = deployment.deploy_rewards_manager(tx_params=tx_params)
    incentives_controller = deployment.deploy_incentives_controller(
        reward_token=lido.LDO_ADDRESS,
        rewards_distributor=rewards_manager,
        rewards_duration=constants.DEFAULT_REWARDS_DURATION,
        tx_params=tx_params,
    )
    rewards_manager.set_rewards_contract(incentives_controller, tx_params)
    rewards_manager.transfer_ownership(lido.AGENT_ADDRESS, tx_params)
    return (rewards_manager, incentives_controller)
