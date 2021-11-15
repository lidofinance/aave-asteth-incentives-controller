// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import { Ownable } from '../dependencies/openzeppelin/Ownable.sol';
import { UUPSUpgradeable } from '../dependencies/openzeppelin/UUPSUpgradable.sol';
import { StorageSlot } from '../dependencies/openzeppelin/StorageSlot.sol';

contract IncentivesControllerStub is Ownable, UUPSUpgradeable {
    error AlreadyInitialized();

    bytes32 private constant VERSION_SLOT = keccak256('AaveAStETHIncentivesController.version');

    uint256 public constant IMPLEMENTATION_VERSION = 1;

    constructor() {
        _initialize(address(0));
    }

    function initialize(address owner) external {
        _initialize(owner);
    }

    function handleAction(address user, uint256 totalSupply, uint256 userBalance) external {}

    function version() external view returns (uint256) {
        return _getVersion();
    }

    function _getVersion() private view returns (uint256) {
        return StorageSlot.getUint256Slot(VERSION_SLOT).value;
    } 

    function _setVersion(uint256 newVersion) private {
        StorageSlot.getUint256Slot(VERSION_SLOT).value = newVersion;
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    function _initialize(address owner) private {
        if (_getVersion() == IMPLEMENTATION_VERSION) {
            revert AlreadyInitialized();
        }
        _setVersion(IMPLEMENTATION_VERSION);
        _transferOwnership(owner);
    }
}