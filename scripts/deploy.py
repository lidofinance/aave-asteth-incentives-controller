from brownie import Wei
from utils import lido, deployment, config, constants


def main():
    deployer = config.get_deployer_account(config.get_is_live())

    print("Deployer:", deployer)
    print("Owner:", lido.AGENT_ADDRESS)
    print("Rewards Duration:", constants.DEFAULT_REWARDS_DURATION)

    sys.stdout.write("Proceed? [y/n]: ")
    if not config.prompt_bool():
        print("Aborting")
        return

    tx_params = {"from": deployer, "gas_price": Wei("100 gwei")}

    rewards_manager = deployment.deploy_rewards_manager(tx_params=tx_params)
    incentives_controller_stub = deployment.deploy_incentives_controller_stub_impl(
        tx_params=tx_params
    )
    proxied_incentives_controller = deployment.deploy_proxy(
        implementation=incentives_controller_stub,
        init_data=incentives_controller_stub.initialize.encode_input(
            lido.AGENT_ADDRESS
        ),
        tx_params=tx_params,
    )
    rewards_manager.set_rewards_contract(proxied_incentives_controller, tx_params)
    rewards_manager.transfer_ownership(lido.AGENT_ADDRESS, tx_params)
