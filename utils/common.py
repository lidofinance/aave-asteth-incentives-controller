from brownie import web3


def is_almost_equal(a, b, epsilon=100):
    return abs(a - b) <= epsilon


def typed_solidity_error(error_signature):
    return f"typed error: {web3.keccak(text=error_signature)[:4].hex()}"
