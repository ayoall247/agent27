import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    "RPC_URL": os.getenv("ARBITRUM_RPC_URL", ""),
    "PRIVATE_KEY": os.getenv("PRIVATE_KEY", ""),
    "SUBSQUID_URL": os.getenv("SUBSQUID_URL", ""),
    "MARKETPLACE_ADDRESS": os.getenv("MARKETPLACE_ADDRESS", ""),
    "MARKETPLACE_DATA_ADDRESS": os.getenv("MARKETPLACE_DATA_ADDRESS", ""),
    "IPFS_API_URL": os.getenv("IPFS_API_URL", "http://127.0.0.1:5001"),
    "MIN_AMOUNT": float(os.getenv("MIN_AMOUNT", "100"))
}
