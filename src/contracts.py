# src/contracts.py
from web3 import Web3
from src.config import CONFIG
import os

READ_ONLY = os.getenv("READ_ONLY_MODE", "false").lower() == "true"
PRIVATE_KEY = CONFIG["PRIVATE_KEY"]

provider = Web3.HTTPProvider(CONFIG["RPC_URL"])
web3 = Web3(provider)

if not READ_ONLY and PRIVATE_KEY:
    account = web3.eth.account.from_key(bytes.fromhex(PRIVATE_KEY.replace("0x", "")))
else:
    account = None  # no account needed in read-only mode

MARKETPLACE_V1_ABI = [
  {
    "type": "function",
    "name": "takeJob",
    "inputs": [
      { "name": "jobId", "type": "uint256" },
      { "name": "signature", "type": "bytes" }
    ],
    "outputs": []
  },
  {
    "type": "function",
    "name": "deliverResult",
    "inputs": [
      { "name": "jobId", "type": "uint256" },
      { "name": "resultHash", "type": "string" }
    ],
    "outputs": []
  }
]

marketplace_contract = web3.eth.contract(
    address=Web3.to_checksum_address(CONFIG["MARKETPLACE_ADDRESS"]),
    abi=MARKETPLACE_V1_ABI
)

def send_tx(fn, *args):
    if READ_ONLY or not PRIVATE_KEY:
        # Just log and simulate
        from src.utils.logger import logger
        logger.info("Skipping send_tx because READ_ONLY_MODE or no PRIVATE_KEY is set.")
        return None

    tx = fn(*args).build_transaction({
        'from': account.address,
        'nonce': web3.eth.get_transaction_count(account.address),
        'gas': 800000,
        'gasPrice': web3.to_wei('1', 'gwei')
    })
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt
