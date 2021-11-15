// SPDX-FileCopyrightText: 2021 Lido <info@lido.fi>
// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.10;

import {Ownable} from "../dependencies/openzeppelin/Ownable.sol";
import {UUPSUpgradeable} from "../dependencies/openzeppelin/UUPSUpgradable.sol";
import {StorageSlot} from "../dependencies/openzeppelin/StorageSlot.sol";

/// @author psirex
/// @notice Contains logic for versionized upgredability of the contracts
contract UnstructuredStorageVersionised is Ownable, UUPSUpgradeable {
    error AlreadyInitializedError();

    /// @notice Storage slot with number of currently initialized version
    bytes32 internal constant INITIALIZED_VERSION_SLOT =
        keccak256("Lido.UnstructuredStorageVersionised.initializedVersion");

    /// @notice Version of code of implementaiton
    /// @dev New implementation must be deployed with value
    ///     different from initializedVersion value
    uint256 public immutable IMPLEMENTATION_VERSION;

    /// @param _implementationVersion Version of the implementation
    constructor(uint256 _implementationVersion) {
        IMPLEMENTATION_VERSION = _implementationVersion;
    }

    /// @notice Returns number of currently initialized version
    function initializedVersion() external view returns (uint256) {
        return _getInitializedVersion();
    }

    function _getInitializedVersion() private view returns (uint256) {
        return StorageSlot.getUint256Slot(INITIALIZED_VERSION_SLOT).value;
    }

    /// @notice Sets value of initialized version to value stored
    ///     in IMPLEMENTATION_VERSION if it wasn't initialized.
    /// @dev If initialized version is equal to IMPLEMENTATION_VERSION
    ///     reverts with AlreadyInitializedError()
    function _updateVersion() private {
        if (_getInitializedVersion() == IMPLEMENTATION_VERSION) {
            revert AlreadyInitializedError();
        }
        StorageSlot.getUint256Slot(INITIALIZED_VERSION_SLOT).value = IMPLEMENTATION_VERSION;
    }

    /// @notice Allows implementaiton upgrade only to owner of the contract
    function _authorizeUpgrade(address newImplementation) internal override onlyOwner {}

    /// @notice Updates initializedVersion and transfer ownership to owner
    function _initialize(address owner) internal {
        _updateVersion();
        _transferOwnership(owner);
    }
}
