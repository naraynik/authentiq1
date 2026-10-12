import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "AuthentiQ Unified Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Database Configuration (PostgreSQL ONLY)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/authentiq"
    )

    # Security & JWT Credentials
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-jwt-signing-key-authentiq-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Admin Seed Credentials
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@authentiq.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin@123456")
    
    # Allowed CORS Origins
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*"
    ]

    # Comma-separated list of allowed browser origins (overrides ALLOWED_ORIGINS when set),
    # e.g. "https://authentiq.example.com". Not needed when the website and API share a domain.
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    # Regular expression of allowed origins, e.g. r"https://authentiq-.*\.onrender\.com"
    CORS_ORIGIN_REGEX: str = os.getenv("CORS_ORIGIN_REGEX", "")

    # Block explorer link for transactions, e.g. "https://sepolia.etherscan.io/tx/" (empty = no links)
    EXPLORER_TX_URL: str = os.getenv("EXPLORER_TX_URL", "")

    # Storage Settings
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads/documents")
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg"]

    # Web3 / Blockchain RPC Node Settings (Phase 4 Integration)
    RPC_URL: str = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    CHAIN_ID: int = int(os.getenv("CHAIN_ID", "1337"))
    CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
    CONTRACT_ABI_PATH: str = os.getenv("CONTRACT_ABI_PATH", "app/contracts/ProductVerification.json")
    BLOCKCHAIN_PRIVATE_KEY: str = os.getenv(
        "BLOCKCHAIN_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )

    # Deploy ProductVerification automatically when no contract exists at CONTRACT_ADDRESS
    # (fresh chain). The deployed address is saved in CONTRACT_STATE_FILE and reused.
    AUTO_DEPLOY_CONTRACT: bool = os.getenv("AUTO_DEPLOY_CONTRACT", "True").lower() == "true"
    CONTRACT_STATE_FILE: str = os.getenv("CONTRACT_STATE_FILE", "data/contract.json")

    # AI Models Settings (Phase 4 Integration)
    RF_MODEL_PATH: str = os.getenv("RF_MODEL_PATH", "app/models/rf_advanced_model.joblib")
    GNN_MODEL_PATH: str = os.getenv("GNN_MODEL_PATH", "app/models/gnn_advanced_model.pt")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
