// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import { IAStETH } from '../interfaces/IAStETH.sol';

interface IAaveIncentivesController {
    function handleAction(address user, uint256 totalSupply, uint256 userBalance) external;
}

contract AStEthMock is IAStETH {
    uint256 public totalSupply;
    mapping(address => uint256) public balances;
    address public incentivesController;

    function setIncentivesController(address _incentivesController) external {
        incentivesController = _incentivesController;
    }

  /**
   * @dev Returns the scaled balance of the user and the scaled total supply.
   * @param user The address of the user
   * @return The scaled balance of the user
   * @return The scaled balance and the scaled total supply
   **/
  function getInternalUserBalanceAndSupply(address user) external view override returns (uint256, uint256) {
      return (balances[user], totalSupply);
  }

  /**
   * @dev Returns the scaled total supply of the token. Represents sum(debt/index)
   * @return The scaled total supply
   **/
  function internalTotalSupply() external view override returns (uint256) {
      return totalSupply;
  }

  function mint(address user, uint256 amount) external {
      uint256 oldBalance = balances[user];
      uint256 oldTotalSupply = totalSupply;
      IAaveIncentivesController(incentivesController).handleAction(user, oldTotalSupply, oldBalance);
      balances[user] += amount;
      totalSupply += amount;
  }

  function burn(address user, uint256 amount) external {
      uint256 oldBalance = balances[user];
      uint256 oldTotalSupply = totalSupply;
      IAaveIncentivesController(incentivesController).handleAction(user, oldTotalSupply, oldBalance);
      balances[user] -= amount;
      totalSupply += amount;
  }
}