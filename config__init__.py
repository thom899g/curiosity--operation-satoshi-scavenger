"""
Configuration module for Project Icarus Sentinel Fleet.
Centralized configuration management with validation.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import os
from dotenv import load_dotenv
import json
import logging

# Load environment variables
load_dotenv()

@dataclass
class RPCConfig:
    """Configuration for RPC endpoints with failover priority"""
    endpoints: List[str] = field(default_factory=list)
    active_endpoint: Optional[str] = None
    timeout_ms: int = 5000
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate and prioritize RPC endpoints"""
        self.endpoints = [
            url for url in [
                os.getenv("ALCHEMY_BASE_RPC_URL"),
                os.getenv("QUICKNODE_BASE_RPC_URL"),
                os.getenv("PUBLIC_BASE_RPC_1"),
                os.getenv("PUBLIC_BASE_RPC_2")
            ] if url and url.startswith("http")
        ]
        
        if not self.endpoints:
            raise ValueError("No valid RPC endpoints configured")
        
        self.active_endpoint = self.endpoints[0]
        logging.info(f"Loaded {len(self.endpoints)} RPC endpoints")

@dataclass
class FirebaseConfig:
    """Firebase configuration for real-time data streaming"""
    project_id: str = ""
    database_url: str = ""
    service_account_path: str = ""
    
    def __post_init__(self):
        self.project_id = os.getenv("FIREBASE_PROJECT_ID", "")
        self.database_url = os.getenv("FIREBASE_DATABASE_URL", "")
        self.service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "")
        
        if not all([self.project_id, self.database_url, self.service_account_path]):
            raise ValueError("Firebase configuration incomplete")
        
        # Verify service account file exists
        if not os.path.exists(self.service_account_path):
            raise FileNotFoundError(
                f"Firebase service account file not found: {self.service_account_path}"
            )

@dataclass
class TradeConfig:
    """Trading operation configuration with risk limits"""
    max_trade_value_usd: float = 2.00
    min_trade_value_usd: float = 0.03
    stop_loss_percent: float = 25.0
    max_gas_gwei: int = 50
    max_gas_percent_of_trade: float = 0.20  # 20%
    circuit_breaker_loss_count: int = 3
    circuit_breaker_drawdown_usd: float = 2.50
    
    def __post_init__(self):
        # Validate constraints
        if self.max_gas_percent_of_trade > 0.5:
            raise ValueError("Gas cost cannot exceed 50% of trade value")
        if self.stop_loss_percent > 50:
            logging.warning(f"Stop loss {self.stop_loss_percent}% is very high")

@dataclass
class SentinelConfig:
    """Sentinel fleet configuration"""
    health_check_interval: int = 30  # seconds
    mempool_scan_interval: int = 2  # seconds
    max_pending_tx_age: int = 120  # seconds
    min_contract_age_blocks: int = 1
    max_contract_age_blocks: int = 10
    
    # Factory addresses to monitor (Base L2)
    uniswap_v2_factory: str = "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6"
    sushi_factory: str = "0xc35DADB65012eC5796536bD9864eD8773aBc74C4"
    
    def get_factory_addresses(self) -> List[str]:
        return [self.uniswap_v2_factory, self.sushi_factory]

class Config:
    """Master configuration singleton"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize all configuration components"""
        self.rpc = RPCConfig()
        self.firebase = FirebaseConfig()
        self.trade = TradeConfig()
        self.sentinel = SentinelConfig()
        
        # Log initialization
        logging.info("Project Icarus Configuration loaded successfully")
        logging.info(f"RPC Endpoints: {len(self.rpc.endpoints)} available")
        logging.info(f"Max trade value: ${self.trade.max_trade_value_usd}")
    
    def validate(self) -> bool:
        """Validate all configurations"""
        try:
            # Validate RPC
            assert len(self.rpc.endpoints) >= 2, "Need at least 2 RPC endpoints"
            
            # Validate Firebase
            assert os.path.exists(self.firebase.service_account_path), \
                "Firebase service account file missing"
            
            # Validate trade parameters
            assert 0 < self.trade.max_trade_value_usd <= 2.00, \
                "Trade value out of bounds"
            assert 0 < self.trade.stop_loss_percent <= 50, \
                "Stop loss percentage invalid"
            
            return True
            
        except AssertionError as e:
            logging.error(f"Configuration validation failed: {e}")
            return False

# Global configuration instance
config = Config()