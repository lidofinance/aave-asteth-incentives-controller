# AAVE Incentives Controller For AStETH Asset

This repo contains implementation of incentives controller for AStETH token in AAVE protocol. AAVE protocol allows to use incentives controllers in their ATokens, VariableDebtTokens and StableDebtTokens to distribute rewards when user receives, transfer or destroy his corresponding tokens. Lido's integration in AAVE uses custom implementation of AToken - AStETH. This repo contains two types of incentives controller implementation can be used with AStETH - `AaveIncentivesControllerStub` and `AaveAStETHIncentivesController`. AStETH token doesn't allow to change incentives controller after deploy. To allow update implementation of incentives controller for AStETH both `AaveIncentivesControllerStub` and `AaveAStETHIncentivesController` inherit `UUPSUpgradable` and `Ownable` contracts and would be deployed under `ERC1967Proxy` contract. Source code for `UUPSUpgradable`, `Ownable` and `ERC1967Proxy` contracts were taken from `OpenZeppelin` package without any changes.

## Core Contracts

### AaveIncentivesControllerStub.sol

Contains logic with empty implementation of `IAaveIncentivesController` interface. This contract will be used on initial deploy of AStETH token and might updated in the future to `AaveAStETHIncentivesController` or might replace it when incentivization of AStETH will be ended, to reduce gas costs on operations with tokens from users.

### AaveAStETHIncentivesController.sol

Contains logic to linear distribution of reward token across holders of AStETH, proportional to amount of tokens user hold. Contract inherits from `UUPSUpgradable` and `Ownable` contracts, and uses Unstructured Storage pattern to simplify future updates of incentivization logic. Contract uses `RewardsUtils` library to reusable and convenient work with rewards.

### RewardsUtils.sol

Provides structures and library for convenient work with staking rewards distributed in a time-based manner.

## Project Setup

To use the tools provided by this project, please pull the repository from GitHub and install its dependencies as follows. It is recommended to use a Python virtual environment.

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

Contains script to deploy `RewardsManager` and `ERC1967Proxy` with `AaveIncentivesControllerStub` as implementation.
