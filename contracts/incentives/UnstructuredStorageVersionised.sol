// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.8.10;

import {Ownable} from "../dependencies/openzeppelin/Ownable.sol";
import {UUPSUpgradeable} from "../dependencies/openzeppelin/UUPSUpgradable.sol";
import {StorageSlot} from "../dependencies/openzeppelin/StorageSlot.sol";

contract UnstructuredStorageVersionised is Ownable, UUPSUpgradeable {
    error AlreadyInitialized();

    bytes32 internal constant VERSION_SLOT =
        keccak256("Lido.UnstructuredStorageVersionised.version");

    uint256 public immutable IMPLEMENTATION_VERSION;

    constructor(uint256 _implementationVersion) {
        IMPLEMENTATION_VERSION = _implementationVersion;
    }

    function version() external view returns (uint256) {
        return _getVersion();
    }

    function _getVersion() private view returns (uint256) {
        return StorageSlot.getUint256Slot(VERSION_SLOT).value;
    }

    function _updateVersion(uint256 newVersion) private {
        if (_getVersion() == IMPLEMENTATION_VERSION) {
            revert AlreadyInitialized();
        }
        StorageSlot.getUint256Slot(VERSION_SLOT).value = newVersion;
    }

    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    function _initialize(address owner) internal {
        _updateVersion(IMPLEMENTATION_VERSION);
        _transferOwnership(owner);
    }
}
