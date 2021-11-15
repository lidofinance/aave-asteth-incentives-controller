# AAVE Incentives Controller For AStETH Asset

This repository contains an implementation of incentives controller for AStETH token in AAVE protocol.
AAVE protocol allows the use of incentives controllers in their AToken, VariableDebtToken, and StableDebtToken
contracts to distribute rewards on a token mint, burn or transfer. Lido's integration in AAVE uses a custom
implementation of AToken - AStETH. This repo contains two types of incentives controller implementation that
can be used with AStETH - `AaveIncentivesControllerStub` and `AaveAStETHIncentivesController`. AStETH token
doesn't allow to change incentives controller after deployment. To allow update implementation of incentives
controller for AStETH both `AaveIncentivesControllerStub` and `AaveAStETHIncentivesController` inherit
`UUPSUpgradable` and `Ownable` contracts and would be deployed behind `ERC1967Proxy` contract, from the
`OpenZeppelin` package.

## Core Contracts

### UnstructuredStorageVersionised.sol

This contract encapsulates the logic for initializing and upgrades proxied contracts on a versioned
basis by the dedicated owner. It inherits from the OpenZeppelin's `Ownable` and `UUPSUpgradable` contracts.

### AaveIncentivesControllerStub.sol

Contains logic with empty implementation of `IAaveIncentivesController`'s `handleAction()` method.
This contract will be used as implementation on the initial deployment of the AStETH token. In the
future implementation will be upgraded to `AaveAStETHIncentivesController` contract. Inherits from
`UnstructuredStorageVersionised.sol` contract.

### AaveAStETHIncentivesController.sol

Contains logic to the linear distribution of reward tokens across holders of AStETH, proportional to
the number of tokens the user hold. Contract inherits from `UnstructuredStorageVersionised.sol` contract
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
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements-dev.txt
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

Contains script to deploy `RewardsManager` and `ERC1967Proxy` with `AaveIncentivesControllerStub`
as implementation.
