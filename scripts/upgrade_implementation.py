from brownie import Contract, Wei, AaveIncentivesControllerStub
from utils import lido, deployment, config, constants, evm_script


def main():
    deployer = config.get_deployer_account(config.get_is_live())
    incentives_controller_proxy = config.get_env("INCENTIVES_CONTROLLER_PROXY")
    staking_token = config.get_env("STAKING_TOKEN")
    rewards_manager = config.get_env("REWARDS_MANAGER")

    print("Deployer:", deployer)
    print("Owner:", lido.AGENT_ADDRESS)
    print("Staking Token", staking_token)
    print("Rewards Manager:", rewards_manager)
    print("Rewards Duration:", constants.DEFAULT_REWARDS_DURATION)
    print("Incentives Controller Proxy:", incentives_controller_proxy)

    sys.stdout.write("Proceed? [y/n]: ")
    if not config.prompt_bool():
        print("Aborting")
        return

    tx_params = {"from": deployer, "gas_price": Wei("100 gwei")}

    start_upgrade_implementation_voting(
        incentives_controller_proxy=incentives_controller_proxy,
        staking_token=staking_token,
        rewards_manager=rewards_manager,
        tx_params=tx_params,
    )


def start_upgrade_implementation_voting(
    incentives_controller_proxy, staking_token, rewards_manager, tx_params
):
    new_implementation = deployment.deploy_incentives_controller_impl(
        reward_token=lido.LDO_ADDRESS,
        staking_token=staking_token,
        rewards_duration=0,
        tx_params=tx_params,
    )

    upgrade_data = new_implementation.initialize.encode_input(
        lido.AGENT_ADDRESS, rewards_manager, constants.DEFAULT_REWARDS_DURATION
    )
    incentives_controller_proxy = Contract.from_abi(
        "AaveIncentivesControllerStub",
        incentives_controller_proxy,
        AaveIncentivesControllerStub.abi,
    )
    upgrade_implementation_callscript = lido.agent_forward(
        [
            (
                incentives_controller_proxy.address,
                incentives_controller_proxy.upgradeToAndCall.encode_input(
                    new_implementation, upgrade_data
                ),
            )
        ]
    )
    return lido.create_voting(
        evm_script=evm_script.encode_call_script([upgrade_implementation_callscript]),
        description="Update implementation of AAVE Incentives Controller to v2",
        tx_params=tx_params,
    )
