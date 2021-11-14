from brownie import interface

LDO_ADDRESS = "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32"
STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
AGENT_ADDRESS = "0x3e40D73EB977Dc6a537aF587D48316feE66E9C8c"


def ldo(interface=interface):
    return interface.ERC20(LDO_ADDRESS)


def steth(interface=interface):
    return interface.StETH(STETH_ADDRESS)
