"""
Mempool Monitor - Core component of Sentinel fleet
Monitors Base L2 mempool for new contract deployments and liquidity events
"""
import asyncio
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from web3 import Web3
from web3.types import TxData, BlockData, HexBytes