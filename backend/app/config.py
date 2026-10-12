import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AuthentiQ API Gateway"
    
    # DB URL: defaults to local PostgreSQL or docker-compose db
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./authentiq.db"
    )
    
    # Web3 / Ethereum local blockchain RPC
    RPC_URL: str = os.getenv("RPC_URL", "http://localhost:8545")
    
    # Smart contract address and ABI location
    CONTRACT_ADDRESS: str = os.getenv(
        "CONTRACT_ADDRESS", 
        "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0" # Hardhat default deploy address for updated ERC-721 contract
    )
    CONTRACT_ABI_PATH: str = os.getenv(
        "CONTRACT_ABI_PATH",
        "app/contracts/AuthentiQRegistry.json"
    )
    
    # AI Model paths - Dual model architecture
    RF_MODEL_PATH: str = os.getenv("RF_MODEL_PATH", "app/models/rf_advanced_model.joblib")
    GNN_MODEL_PATH: str = os.getenv("GNN_MODEL_PATH", "app/models/gnn_advanced_model.pt")
    
    # Legacy model path (for backward compatibility)
    MODEL_PATH: str = os.getenv("MODEL_PATH", "app/models/rf_advanced_model.joblib")
    
    class Config:
        case_sensitive = True

settings = Settings()
