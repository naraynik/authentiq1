// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title ProductVerification
 * @dev Smart contract for registering authentic products, declaring manufacturer supply chain target locations,
 * and maintaining immutable provenance and route history for the AuthentiQ anti-counterfeit system.
 */
contract ProductVerification is AccessControl {
    // Role definitions using keccak256 hashes
    bytes32 public constant MANUFACTURER_ROLE = keccak256("MANUFACTURER_ROLE");
    bytes32 public constant INSPECTOR_ROLE = keccak256("INSPECTOR_ROLE");

    // Enums for product status tracking
    enum ProductStatus { GENUINE, SUSPICIOUS, RECALLED }

    // Struct representing an individual location/destination record in the declared route history
    struct LocationRecord {
        string locationName;
        string details;
        uint256 timestamp;
        address updatedBy;
    }

    // Struct representing a registered product's digital birth certificate
    struct Product {
        string productId;
        string manufacturerName;
        string batchNumber;
        uint256 manufacturingDate;
        uint256 expiryDate;
        string currentLocation;
        string nextLocation;
        bytes32 productHash;
        uint256 registrationTimestamp;
        ProductStatus status;
        bool isRegistered;
    }

    // Storage mappings
    mapping(string => Product) private products;
    mapping(string => LocationRecord[]) private locationHistories;

    // Events for indexed logging and Web3 tracking
    event ProductRegistered(
        string indexed productId,
        string manufacturerName,
        string batchNumber,
        address indexed manufacturer,
        string currentLocation,
        string nextLocation,
        bytes32 productHash,
        uint256 registrationTimestamp
    );

    event LocationUpdated(
        string indexed productId,
        string previousLocation,
        string nextLocation,
        address indexed updatedBy,
        uint256 timestamp
    );

    event ProductStatusUpdated(
        string indexed productId,
        ProductStatus oldStatus,
        ProductStatus newStatus,
        address indexed updatedBy,
        uint256 timestamp
    );

    // Custom gas-efficient errors
    error ProductAlreadyExists(string productId);
    error ProductDoesNotExist(string productId);
    error InvalidLocationName();
    error InvalidProductId();
    error BatchArrayMismatch();

    /**
     * @notice Phase 1: Admin Setup & Governance
     * @dev Constructor grants DEFAULT_ADMIN_ROLE, MANUFACTURER_ROLE, and INSPECTOR_ROLE to deployer.
     * @param defaultAdmin Address of initial admin (defaults to msg.sender if address(0))
     */
    constructor(address defaultAdmin) {
        address admin = defaultAdmin == address(0) ? msg.sender : defaultAdmin;
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MANUFACTURER_ROLE, admin);
        _grantRole(INSPECTOR_ROLE, admin);
    }

    /**
     * @notice Phase 2: Manufacturer Product Registration with Declared Route
     * @dev Registers a new product on the blockchain ledger with initial location and next intended destination.
     * Restricted to MANUFACTURER_ROLE.
     */
    function registerProduct(
        string calldata productId,
        string calldata manufacturerName,
        string calldata batchNumber,
        uint256 manufacturingDate,
        uint256 expiryDate,
        bytes32 productHash,
        string calldata currentLocation,
        string calldata nextLocation
    ) external onlyRole(MANUFACTURER_ROLE) {
        if (bytes(productId).length == 0) revert InvalidProductId();
        if (products[productId].isRegistered) revert ProductAlreadyExists(productId);
        if (bytes(currentLocation).length == 0 || bytes(nextLocation).length == 0) revert InvalidLocationName();

        products[productId] = Product({
            productId: productId,
            manufacturerName: manufacturerName,
            batchNumber: batchNumber,
            manufacturingDate: manufacturingDate,
            expiryDate: expiryDate,
            currentLocation: currentLocation,
            nextLocation: nextLocation,
            productHash: productHash,
            registrationTimestamp: block.timestamp,
            status: ProductStatus.GENUINE,
            isRegistered: true
        });

        locationHistories[productId].push(LocationRecord({
            locationName: currentLocation,
            details: string(abi.encodePacked("Registered at origin. Next target: ", nextLocation)),
            timestamp: block.timestamp,
            updatedBy: msg.sender
        }));

        emit ProductRegistered(
            productId,
            manufacturerName,
            batchNumber,
            msg.sender,
            currentLocation,
            nextLocation,
            productHash,
            block.timestamp
        );
    }

    /**
     * @notice Phase 2: Batch Registration with Target Destinations (Gas Optimized)
     * @dev Registers multiple products in a single transaction with declared initial and next locations.
     */
    function registerProductBatch(
        string[] calldata productIds,
        string calldata manufacturerName,
        string calldata batchNumber,
        uint256 manufacturingDate,
        uint256 expiryDate,
        bytes32[] calldata productHashes,
        string calldata currentLocation,
        string calldata nextLocation
    ) external onlyRole(MANUFACTURER_ROLE) {
        if (productIds.length != productHashes.length) revert BatchArrayMismatch();
        if (bytes(currentLocation).length == 0 || bytes(nextLocation).length == 0) revert InvalidLocationName();

        for (uint256 i = 0; i < productIds.length; i++) {
            if (bytes(productIds[i]).length == 0) revert InvalidProductId();
            if (products[productIds[i]].isRegistered) revert ProductAlreadyExists(productIds[i]);

            products[productIds[i]] = Product({
                productId: productIds[i],
                manufacturerName: manufacturerName,
                batchNumber: batchNumber,
                manufacturingDate: manufacturingDate,
                expiryDate: expiryDate,
                currentLocation: currentLocation,
                nextLocation: nextLocation,
                productHash: productHashes[i],
                registrationTimestamp: block.timestamp,
                status: ProductStatus.GENUINE,
                isRegistered: true
            });

            locationHistories[productIds[i]].push(LocationRecord({
                locationName: currentLocation,
                details: string(abi.encodePacked("Batch registered at origin. Next target: ", nextLocation)),
                timestamp: block.timestamp,
                updatedBy: msg.sender
            }));

            emit ProductRegistered(
                productIds[i],
                manufacturerName,
                batchNumber,
                msg.sender,
                currentLocation,
                nextLocation,
                productHashes[i],
                block.timestamp
            );
        }
    }

    /**
     * @notice Phase 3: Manufacturer Declares Next Target Location
     * @dev Updates the product's current location and sets the next intended destination location on-chain.
     * Restricted to MANUFACTURER_ROLE or INSPECTOR_ROLE.
     */
    function updateNextLocation(
        string calldata productId,
        string calldata newNextLocation,
        string calldata details
    ) external onlyRole(MANUFACTURER_ROLE) {
        if (!products[productId].isRegistered) revert ProductDoesNotExist(productId);
        if (bytes(newNextLocation).length == 0) revert InvalidLocationName();

        string memory previousLocation = products[productId].nextLocation;
        products[productId].currentLocation = previousLocation;
        products[productId].nextLocation = newNextLocation;

        locationHistories[productId].push(LocationRecord({
            locationName: previousLocation,
            details: bytes(details).length > 0 ? details : string(abi.encodePacked("Route updated. Next target: ", newNextLocation)),
            timestamp: block.timestamp,
            updatedBy: msg.sender
        }));

        emit LocationUpdated(productId, previousLocation, newNextLocation, msg.sender, block.timestamp);
    }

    /**
     * @notice Inspector / Fraud Management: Status Flagging
     * @dev Updates product status (GENUINE, SUSPICIOUS, RECALLED). Restricted to INSPECTOR_ROLE or DEFAULT_ADMIN_ROLE.
     */
    function updateProductStatus(string calldata productId, ProductStatus newStatus)
        external
        onlyRole(INSPECTOR_ROLE)
    {
        if (!products[productId].isRegistered) revert ProductDoesNotExist(productId);

        ProductStatus oldStatus = products[productId].status;
        products[productId].status = newStatus;

        emit ProductStatusUpdated(productId, oldStatus, newStatus, msg.sender, block.timestamp);
    }

    /**
     * @notice Phase 4: Customer Verification Query (Free Read Query)
     * @dev View function retrieving full product digital birth certificate metadata including target location.
     */
    function verifyProduct(string calldata productId)
        external
        view
        returns (Product memory)
    {
        if (!products[productId].isRegistered) revert ProductDoesNotExist(productId);
        return products[productId];
    }

    /**
     * @notice Phase 4: Customer Route History Query (Free Read Query)
     * @dev View function retrieving full declared location and route history.
     */
    function getLocationHistory(string calldata productId)
        external
        view
        returns (LocationRecord[] memory)
    {
        if (!products[productId].isRegistered) revert ProductDoesNotExist(productId);
        return locationHistories[productId];
    }

    /**
     * @notice Helper view function checking registration status.
     */
    function productExists(string calldata productId) external view returns (bool) {
        return products[productId].isRegistered;
    }
}
