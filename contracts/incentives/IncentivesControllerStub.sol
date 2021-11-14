// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import { Ownable } from '../dependencies/openzeppelin/Ownable.sol';
import { UUPSUpgradeable } from '../dependencies/openzeppelin/UUPSUpgradable.sol';


contract IncentivesControllerStub is Ownable, UUPSUpgradeable {
    error AlreadyInitialized();

    uint8 public constant IMPLEMENTATION_VERSION = 1;
    uint8 public version;

    constructor() {
        _initialize(address(0));
    }

    function initialize(address owner) external {
        _initialize(owner);
    }

    function handleAction(address user, uint256 totalSupply, uint256 userBalance) external {}

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    function _initialize(address owner) private {
        if (version == IMPLEMENTATION_VERSION) {
            revert AlreadyInitialized();
        }
        version = IMPLEMENTATION_VERSION;
        _transferOwnership(owner);
    }
}