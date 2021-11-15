// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import {Ownable} from "../dependencies/openzeppelin/Ownable.sol";
import {UUPSUpgradeable} from "../dependencies/openzeppelin/UUPSUpgradable.sol";
import {StorageSlot} from "../dependencies/openzeppelin/StorageSlot.sol";

import {IAaveIncentivesController} from "../interfaces/IAaveIncentivesController.sol";

import {UnstructuredStorageVersionised} from "./UnstructuredStorageVersionised.sol";

contract AaveIncentivesControllerStub is UnstructuredStorageVersionised, IAaveIncentivesController {
    uint256 private constant _IMPLEMENTATION_VERSION = 1;

    constructor() UnstructuredStorageVersionised(_IMPLEMENTATION_VERSION) {
        _initialize(address(0));
    }

    function initialize(address owner) external {
        _initialize(owner);
    }

    function handleAction(
        address user,
        uint256 totalSupply,
        uint256 userBalance
    ) external override {}
}