from web3 import Web3
from src.config import CONFIG
from src.utils.logger import logger
import json

READ_ONLY = CONFIG["READ_ONLY_MODE"]
PRIVATE_KEY = CONFIG["PRIVATE_KEY"]

provider = Web3.HTTPProvider(CONFIG["RPC_URL"])
web3 = Web3(provider)

if not READ_ONLY and PRIVATE_KEY:
    account = web3.eth.account.from_key(bytes.fromhex(PRIVATE_KEY.replace("0x", "")))
    logger.info("Using provided private key for real transactions on network: %s", CONFIG["RPC_URL"])
else:
    account = None
    logger.info("No private key or READ_ONLY mode enabled. Transactions will be simulated.")

# Load the actual ABI from a JSON file or a verified source
# Suppose you have the actual ABI from the repo in 'marketplace_abi.json'
with open('marketplace_abi.json', 'r') as f:
    MARKETPLACE_V1_ABI = json.load(f)

if not CONFIG["MARKETPLACE_ADDRESS"]:
    logger.error("MARKETPLACE_ADDRESS not set. Exiting.")
    raise SystemExit("MARKETPLACE_ADDRESS not defined")

marketplace_contract = web3.eth.contract(address=Web3.to_checksum_address(CONFIG["MARKETPLACE_ADDRESS"]), abi=MARKETPLACE_V1_ABI)

def send_tx(fn, *args):
    if READ_ONLY or not PRIVATE_KEY or account is None:
        logger.info("Skipping send_tx due to READ_ONLY_MODE or no PRIVATE_KEY. Simulating action.")
        return None
    try:
        tx = fn(*args).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 800000,
            'gasPrice': web3.to_wei('1', 'gwei')
        })
        signed = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Transaction mined at block %s, tx hash: %s", receipt.blockNumber, receipt.transactionHash.hex())
        return receipt
    except Exception as e:
        logger.error("Error sending transaction: %s", str(e))
        return None
