// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import {IAStETH} from "../interfaces/IAStETH.sol";
import {IAaveIncentivesController} from "../interfaces/IAaveIncentivesController.sol";

/// @author psirex
/// @notice Mock of AStETH for testing purposes
contract AStEthMock is IAStETH {
    uint256 public totalSupply;
    mapping(address => uint256) public balances;
    address public incentivesController;

    function setIncentivesController(address _incentivesController) external {
        incentivesController = _incentivesController;
    }

    function getInternalUserBalanceAndSupply(address user)
        external
        view
        override
        returns (uint256, uint256)
    {
        return (balances[user], totalSupply);
    }

    function internalTotalSupply() external view override returns (uint256) {
        return totalSupply;
    }

    function mint(address user, uint256 amount) external {
        uint256 oldBalance = balances[user];
        uint256 oldTotalSupply = totalSupply;
        IAaveIncentivesController(incentivesController).handleAction(
            user,
            oldTotalSupply,
            oldBalance
        );
        balances[user] += amount;
        totalSupply += amount;
    }

    function burn(address user, uint256 amount) external {
        uint256 oldBalance = balances[user];
        uint256 oldTotalSupply = totalSupply;
        IAaveIncentivesController(incentivesController).handleAction(
            user,
            oldTotalSupply,
            oldBalance
        );
        balances[user] -= amount;
        totalSupply += amount;
    }
}
