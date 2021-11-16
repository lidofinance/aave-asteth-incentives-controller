from typing import Tuple, Sequence
from brownie import interface, chain, accounts
from utils.evm_script import encode_call_script

LDO_ADDRESS = "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32"
STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
AGENT_ADDRESS = "0x3e40D73EB977Dc6a537aF587D48316feE66E9C8c"
VOTING_ADDRESS = "0x2e59a20f205bb85a89c53f1936454680651e618e"
TOKEN_MANAGER_ADDRESS = "0xf73a1260d222f447210581ddf212d915c09a3249"


def ldo(interface=interface):
    return interface.ERC20(LDO_ADDRESS)


def steth(interface=interface):
    return interface.StETH(STETH_ADDRESS)


def voting(interface=interface):
    return interface.Voting(VOTING_ADDRESS)


def token_manager(interface=interface):
    return interface.TokenManager(TOKEN_MANAGER_ADDRESS)


def agent_forward(call_script: Sequence[Tuple[str, str]]) -> Tuple[str, str]:
    agent = interface.Agent(AGENT_ADDRESS)
    return (
        AGENT_ADDRESS,
        agent.forward.encode_input(encode_call_script(call_script)),
    )


def create_voting(evm_script, description, tx_params):
    voting_tx = token_manager().forward(
        encode_call_script(
            [
                (
                    VOTING_ADDRESS,
                    voting().newVote.encode_input(evm_script, description),
                )
            ]
        ),
        tx_params,
    )
    return voting_tx.events["StartVote"]["voteId"], voting_tx


def execute_voting(voting_id):
    # agent = contracts()["dao"]["agent"]
    # voting = contracts()["dao"]["voting"]
    if voting().getVote(voting_id)["executed"]:
        return
    voting().vote(voting_id, True, False, {"from": AGENT_ADDRESS})
    chain.sleep(3 * 60 * 60 * 24)
    chain.mine()
    assert voting().canExecute(voting_id)
    voting().executeVote(voting_id, {"from": accounts[0]})
