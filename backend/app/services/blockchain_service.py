import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound

from app.core.config import settings

logger = logging.getLogger(__name__)

# Smart contract ProductStatus enum mapping:
# 0 = GENUINE, 1 = SUSPICIOUS, 2 = RECALLED
STATUS_MAP = {
    "GENUINE": 0,
    "REGISTERED": 0,
    "SUSPICIOUS": 1,
    "RECALLED": 2
}

REVERSE_STATUS_MAP = {
    0: "GENUINE",
    1: "SUSPICIOUS",
    2: "RECALLED"
}

class BlockchainService:
    def __init__(self):
        self.rpc_url = settings.RPC_URL
        self.chain_id = settings.CHAIN_ID
        self.contract_address = settings.CONTRACT_ADDRESS
        self.abi_path = settings.CONTRACT_ABI_PATH
        self.private_key = settings.BLOCKCHAIN_PRIVATE_KEY
        
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.contract = None
        self.account = None
        self._contract_ready = False  # set by ensure_contract() once code is confirmed on chain

        self._initialize()

    def _initialize(self):
        """Initialize Web3 connection, account, and contract contract instance."""
        try:
            if self.private_key:
                try:
                    self.account = self.w3.eth.account.from_key(self.private_key)
                except Exception as e:
                    logger.warning(f"Could not initialize account from private key: {e}")
            
            abi = self._load_abi()
            if abi and self.contract_address:
                checksum_addr = Web3.to_checksum_address(self.contract_address)
                self.contract = self.w3.eth.contract(address=checksum_addr, abi=abi)
                logger.info(f"Loaded contract at {checksum_addr}")
        except Exception as e:
            logger.error(f"Error initializing BlockchainService: {e}")

    def _load_abi(self) -> Optional[List[Dict[str, Any]]]:
        """Load contract ABI from configured path or fallback file."""
        paths_to_try = [
            self.abi_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts", "ProductVerification.json"),
            "app/contracts/ProductVerification.json"
        ]
        
        for path in paths_to_try:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "abi" in data:
                            return data["abi"]
                        elif isinstance(data, list):
                            return data
                except Exception as e:
                    logger.error(f"Error loading ABI from {path}: {e}")
        return None

    def _has_code(self, address: Optional[str]) -> bool:
        try:
            return bool(address) and len(self.w3.eth.get_code(Web3.to_checksum_address(address))) > 0
        except Exception:
            return False

    def _use_address(self, address: str) -> None:
        abi = self._load_abi()
        self.contract_address = Web3.to_checksum_address(address)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=abi)
        self._contract_ready = True

    # The deployed address is remembered per chain in the database (app_state), so hosts
    # with temporary disks (e.g. Render) do not deploy a new contract on every restart.
    def _state_key(self) -> str:
        return f"contract_address:{self.w3.eth.chain_id}"

    def _db_saved_address(self) -> Optional[str]:
        try:
            from app.database.database import SessionLocal
            from app.models.app_state import AppState
            with SessionLocal() as db:
                row = db.get(AppState, self._state_key())
                return row.value if row else None
        except Exception as e:
            logger.warning(f"Could not read saved contract address: {e}")
            return None

    def _db_save_address(self, address: str) -> None:
        try:
            from app.database.database import SessionLocal
            from app.models.app_state import AppState
            with SessionLocal() as db:
                row = db.get(AppState, self._state_key()) or AppState(key=self._state_key())
                row.value = address
                db.merge(row)
                db.commit()
        except Exception as e:
            logger.warning(f"Could not save contract address to the database: {e}")

    def _retry_contract(self) -> None:
        """ensure_contract(), at most once a minute (health checks call this often)."""
        import time
        now = time.monotonic()
        if now - getattr(self, "_last_contract_attempt", -1e9) >= 60:
            self._last_contract_attempt = now
            self.ensure_contract()

    def _require_contract(self) -> None:
        """Retry the contract check lazily (e.g. the chain came up after the API)."""
        if not self._contract_ready:
            self.ensure_contract()
        if not self.contract or not self._contract_ready:
            reason = getattr(self, "_last_contract_error", None) or "Is the blockchain node running?"
            raise RuntimeError(f"Blockchain contract is not available: {reason}")

    def ensure_contract(self) -> Dict[str, Any]:
        """Make sure a ProductVerification contract is live on the chain.

        Order: CONTRACT_ADDRESS (if it has code) -> address saved in CONTRACT_STATE_FILE
        (if it has code) -> deploy a new one from the compiled artifact (when
        AUTO_DEPLOY_CONTRACT is on) and save its address. Safe to call on every start.
        """
        try:
            if not self.w3.is_connected():
                logger.warning(f"Blockchain RPC {self.rpc_url} not reachable; contract check skipped")
                return {"status": "rpc_unreachable"}
            if self._has_code(self.contract_address):
                self._use_address(self.contract_address)
                return {"status": "configured", "address": self.contract_address}
            saved_db = self._db_saved_address()
            if self._has_code(saved_db):
                self._use_address(saved_db)
                logger.info(f"Using contract saved in the database: {saved_db}")
                return {"status": "saved", "address": self.contract_address}
            state_file = settings.CONTRACT_STATE_FILE
            if os.path.exists(state_file):
                with open(state_file, "r", encoding="utf-8") as f:
                    saved = json.load(f).get("address")
                if self._has_code(saved):
                    self._use_address(saved)
                    logger.info(f"Using contract from {state_file}: {saved}")
                    return {"status": "saved", "address": self.contract_address}
            if not settings.AUTO_DEPLOY_CONTRACT:
                logger.error("No contract found on chain and AUTO_DEPLOY_CONTRACT is off")
                return {"status": "missing"}
            artifact_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "contracts", "ProductVerification.json")
            with open(artifact_path, "r", encoding="utf-8") as f:
                artifact = json.load(f)
            if not artifact.get("bytecode") or not self.account:
                logger.error("Cannot deploy contract: bytecode or signing key missing")
                return {"status": "missing"}
            factory = self.w3.eth.contract(abi=artifact["abi"], bytecode=artifact["bytecode"])
            tx = factory.constructor(self.account.address).build_transaction({
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "chainId": self.w3.eth.chain_id,
                "gasPrice": self.w3.eth.gas_price,
            })
            signed = self.account.sign_transaction(tx)
            receipt = self.w3.eth.wait_for_transaction_receipt(self.w3.eth.send_raw_transaction(signed.raw_transaction))
            if receipt.status != 1:
                raise RuntimeError("Contract deployment transaction failed")
            self._use_address(receipt.contractAddress)
            os.makedirs(os.path.dirname(state_file) or ".", exist_ok=True)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump({"address": self.contract_address, "chain_id": self.w3.eth.chain_id,
                           "block": receipt.blockNumber}, f)
            self._db_save_address(self.contract_address)
            logger.info(f"Deployed ProductVerification at {self.contract_address} (saved to the database and {state_file})")
            return {"status": "deployed", "address": self.contract_address}
        except Exception as e:
            logger.error(f"Contract check/deploy failed: {e}")
            self._last_contract_error = str(e)
            return {"status": "error", "error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        """Verify RPC connection, Chain ID, latest block, contract accessibility."""
        try:
            is_connected = self.w3.is_connected()
            if not is_connected:
                return {
                    "status": "UNHEALTHY",
                    "rpc_reachable": False,
                    "chain_id": None,
                    "latest_block": None,
                    "contract_address": self.contract_address,
                    "contract_accessible": False,
                    "wallet_address": self.account.address if self.account else None,
                    "error": "RPC node unreachable"
                }

            chain_id = self.w3.eth.chain_id
            latest_block = self.w3.eth.block_number
            
            contract_accessible = False
            if self.contract:
                try:
                    # Test read function: get MANUFACTURER_ROLE
                    self.contract.functions.MANUFACTURER_ROLE().call()
                    contract_accessible = True
                except Exception as e:
                    logger.warning(f"Contract accessibility check failed: {e}")

            wallet_balance = None
            if self.account:
                try:
                    wallet_balance = float(self.w3.from_wei(self.w3.eth.get_balance(self.account.address), "ether"))
                except Exception:
                    pass
            if not contract_accessible and not self._contract_ready:
                # e.g. the chain came back or the wallet was funded since start-up
                self._retry_contract()
                contract_accessible = self._contract_ready

            return {
                "status": "HEALTHY" if is_connected and contract_accessible else "PARTIAL",
                "wallet_balance_eth": wallet_balance,
                "rpc_reachable": is_connected,
                "chain_id": chain_id,
                "latest_block": latest_block,
                "contract_address": self.contract_address,
                "contract_accessible": contract_accessible,
                "wallet_address": self.account.address if self.account else None,
                "error": None
            }
        except Exception as e:
            return {
                "status": "UNHEALTHY",
                "rpc_reachable": False,
                "chain_id": None,
                "latest_block": None,
                "contract_address": self.contract_address,
                "contract_accessible": False,
                "wallet_address": self.account.address if self.account else None,
                "error": str(e)
            }

    def generate_product_hash(
        self,
        product_id: str,
        manufacturer_name: str,
        batch_number: str,
        m_timestamp: int,
        e_timestamp: int
    ) -> bytes:
        """
        Derive deterministic product hash (bytes32).
        SHA-256 string input -> 32 bytes hex.
        """
        raw_str = f"{product_id}:{manufacturer_name}:{batch_number}:{m_timestamp}:{e_timestamp}"
        hash_hex = Web3.solidity_keccak(
            ["string", "string", "string", "uint256", "uint256"],
            [product_id, manufacturer_name, batch_number, m_timestamp, e_timestamp]
        )
        return hash_hex

    def product_exists(self, product_id: str) -> bool:
        """Check if product exists on-chain."""
        self._require_contract()
        return self.contract.functions.productExists(product_id).call()

    def register_product(
        self,
        product_id: str,
        manufacturer_name: str,
        batch_number: str,
        manufacturing_date: datetime,
        expiry_date: Optional[datetime],
        current_location: str,
        next_location: str,
        custom_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Register product on ProductVerification smart contract.
        Returns tx receipt details.
        """
        self._require_contract()

        m_ts = int(manufacturing_date.timestamp())
        e_ts = int(expiry_date.timestamp()) if expiry_date else 0
        product_hash = self.generate_product_hash(product_id, manufacturer_name, batch_number, m_ts, e_ts)

        account = self.account
        if custom_private_key:
            account = self.w3.eth.account.from_key(custom_private_key)
        
        if not account:
            raise ValueError("No authorized wallet private key provided for transaction signing")

        # Build transaction
        nonce = self.w3.eth.get_transaction_count(account.address)
        tx_func = self.contract.functions.registerProduct(
            product_id,
            manufacturer_name,
            batch_number,
            m_ts,
            e_ts,
            product_hash,
            current_location,
            next_location
        )

        try:
            gas_estimate = tx_func.estimate_gas({"from": account.address})
        except Exception as e:
            logger.error(f"Gas estimation failed for registerProduct: {e}")
            raise e

        tx = tx_func.build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id if self.w3.is_connected() else self.chain_id
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise RuntimeError(f"Transaction reverted on-chain (tx_hash: {tx_hash.hex()})")

        return {
            "success": True,
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "product_hash": product_hash.hex(),
            "is_onchain": True
        }

    def register_product_batch(
        self,
        product_ids: List[str],
        manufacturer_name: str,
        batch_number: str,
        manufacturing_date: datetime,
        expiry_date: Optional[datetime],
        current_location: str,
        next_location: str,
        custom_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register batch of products on-chain."""
        self._require_contract()

        m_ts = int(manufacturing_date.timestamp())
        e_ts = int(expiry_date.timestamp()) if expiry_date else 0

        product_hashes = [
            self.generate_product_hash(pid, manufacturer_name, batch_number, m_ts, e_ts)
            for pid in product_ids
        ]

        account = self.account
        if custom_private_key:
            account = self.w3.eth.account.from_key(custom_private_key)

        if not account:
            raise ValueError("No authorized wallet private key provided for transaction signing")

        nonce = self.w3.eth.get_transaction_count(account.address)
        tx_func = self.contract.functions.registerProductBatch(
            product_ids,
            manufacturer_name,
            batch_number,
            m_ts,
            e_ts,
            product_hashes,
            current_location,
            next_location
        )

        gas_estimate = tx_func.estimate_gas({"from": account.address})
        tx = tx_func.build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id if self.w3.is_connected() else self.chain_id
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise RuntimeError(f"Batch transaction reverted on-chain (tx_hash: {tx_hash.hex()})")

        return {
            "success": True,
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "count": len(product_ids),
            "is_onchain": True
        }

    def verify_product(self, product_id: str) -> Dict[str, Any]:
        """Read and verify product status from smart contract."""
        self._require_contract()

        onchain_data = self.contract.functions.verifyProduct(product_id).call()
        # onchain_data is a tuple: (productId, manufacturerName, batchNumber, manufacturingDate, expiryDate, currentLocation, nextLocation, productHash, registrationTimestamp, status, isRegistered)
        
        status_code = onchain_data[9]
        status_name = REVERSE_STATUS_MAP.get(status_code, "UNKNOWN")

        return {
            "product_id": onchain_data[0],
            "manufacturer_name": onchain_data[1],
            "batch_number": onchain_data[2],
            "manufacturing_date": datetime.fromtimestamp(onchain_data[3]) if onchain_data[3] else None,
            "expiry_date": datetime.fromtimestamp(onchain_data[4]) if onchain_data[4] else None,
            "current_location": onchain_data[5],
            "next_location": onchain_data[6],
            "product_hash": "0x" + onchain_data[7].hex() if isinstance(onchain_data[7], bytes) else str(onchain_data[7]),
            "registration_timestamp": datetime.fromtimestamp(onchain_data[8]) if onchain_data[8] else None,
            "status": status_name,
            "status_code": status_code,
            "is_registered": onchain_data[10],
            "is_onchain": True
        }

    def update_next_location(
        self,
        product_id: str,
        new_next_location: str,
        details: str,
        custom_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update product next location on-chain."""
        self._require_contract()

        account = self.account
        if custom_private_key:
            account = self.w3.eth.account.from_key(custom_private_key)

        if not account:
            raise ValueError("No authorized wallet private key provided for transaction signing")

        nonce = self.w3.eth.get_transaction_count(account.address)
        tx_func = self.contract.functions.updateNextLocation(product_id, new_next_location, details)
        gas_estimate = tx_func.estimate_gas({"from": account.address})

        tx = tx_func.build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id if self.w3.is_connected() else self.chain_id
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise RuntimeError(f"Location update transaction reverted on-chain (tx_hash: {tx_hash.hex()})")

        return {
            "success": True,
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "product_id": product_id,
            "new_next_location": new_next_location
        }

    def update_product_status(
        self,
        product_id: str,
        new_status: str,
        custom_private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update product status (GENUINE, SUSPICIOUS, RECALLED) on-chain."""
        self._require_contract()

        status_code = STATUS_MAP.get(new_status.upper())
        if status_code is None:
            raise ValueError(f"Invalid status value: {new_status}. Must be one of {list(STATUS_MAP.keys())}")

        account = self.account
        if custom_private_key:
            account = self.w3.eth.account.from_key(custom_private_key)

        if not account:
            raise ValueError("No authorized wallet private key provided for transaction signing")

        nonce = self.w3.eth.get_transaction_count(account.address)
        tx_func = self.contract.functions.updateProductStatus(product_id, status_code)
        gas_estimate = tx_func.estimate_gas({"from": account.address})

        tx = tx_func.build_transaction({
            "from": account.address,
            "nonce": nonce,
            "gas": int(gas_estimate * 1.2),
            "gasPrice": self.w3.eth.gas_price,
            "chainId": self.w3.eth.chain_id if self.w3.is_connected() else self.chain_id
        })

        signed_tx = account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            raise RuntimeError(f"Status update transaction reverted on-chain (tx_hash: {tx_hash.hex()})")

        return {
            "success": True,
            "transaction_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "product_id": product_id,
            "new_status": new_status
        }

    def get_location_history(self, product_id: str) -> List[Dict[str, Any]]:
        """Get on-chain location history for product."""
        self._require_contract()

        raw_history = self.contract.functions.getLocationHistory(product_id).call()
        history = []
        for record in raw_history:
            # record is tuple: (locationName, details, timestamp, updatedBy)
            history.append({
                "location_name": record[0],
                "details": record[1],
                "timestamp": datetime.fromtimestamp(record[2]) if record[2] else None,
                "updated_by": record[3]
            })
        return history

    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Fetch transaction details by hash."""
        receipt = self.w3.eth.get_transaction_receipt(tx_hash)
        return {
            "transaction_hash": receipt.transactionHash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "status": receipt.status,
            "from": receipt["from"],
            "to": receipt["to"]
        }


blockchain_service = BlockchainService()
