# AAVE Incentives Controller For AStETH Asset

This repository contains an implementation of incentives controller for AStETH token in AAVE protocol.
AAVE protocol allows the use of incentives controllers in their AToken, VariableDebtToken, and StableDebtToken
contracts to distribute rewards on a token mint, burn or transfer. Lido's integration in AAVE uses a custom
implementation of AToken - AStETH.

## Core Contracts

### AaveAStETHIncentivesController.sol

Contains logic to the linear distribution of reward tokens across holders of AStETH, proportional to
the number of tokens the user hold. Contract inherits from the OpenZeppelin's `Ownable` contract
and implements Unstructured Storage pattern to simplify future updates of incentivization logic.
The contract uses `RewardsUtils` library to reusable and convenient work with rewards

### RewardsUtils.sol

Provides structs and a library for convenient work with staking rewards distributed in a time-based manner.

## Project Setup

To use the tools provided by this project, please pull the repository from GitHub and install
its dependencies as follows. It is recommended to use a Python virtual environment.

```bash
git clone https://github.com/lidofinance/aave-asteth-incentives-controller.git
cd aave-asteth-incentives-controller
npm install
poetry install
poetry shell
```

Compile the smart contracts:

```bash
brownie compile # add `--size` to see contract compiled sizes
```

## Testing

The fastest way to run the tests is:

```bash
brownie test
```

Run tests with coverage and gas profiling:

```bash
brownie test --coverage --gas
```

## Scripts

### `deploy.py`

Contains script to deploy and setup `RewardsManager` and `AaveAStETHIncentivesController` contracts. Deployed `RewardsManager` used as rewards distributor in the `AaveAStETHIncentivesController` contract.

### `initialize_staking_token.py`

Contains script to finalize deployment of `AaveAStETHIncentivesController`. This script must be run after deployment of AStETH token, to set address of `stakingToken`. As part of the initialization transfers ownership to Lido's Agent.
