from web3 import Web3
from src.config import CONFIG
from src.utils.logger import logger

READ_ONLY = CONFIG["READ_ONLY_MODE"]
PRIVATE_KEY = CONFIG["PRIVATE_KEY"]

provider = Web3.HTTPProvider(CONFIG["RPC_URL"])
web3 = Web3(provider)

if not READ_ONLY and PRIVATE_KEY:
    account = web3.eth.account.from_key(bytes.fromhex(PRIVATE_KEY.replace("0x", "")))
    logger.info("Using provided private key for real transactions.")
else:
    account = None
    logger.info("No private key or READ_ONLY mode enabled. Transactions will be simulated.")

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
  },
  {
    "type":"function",
    "name":"publishJobPost",
    "inputs":[
      {"name":"title","type":"string"},
      {"name":"contentHash","type":"bytes32"},
      {"name":"multipleApplicants","type":"bool"},
      {"name":"tags","type":"string[]"},
      {"name":"token","type":"address"},
      {"name":"amount","type":"uint256"},
      {"name":"maxTime","type":"uint256"},
      {"name":"deliveryMethod","type":"string"},
      {"name":"arbitrator","type":"address"},
      {"name":"whitelist","type":"address[]"}
    ],
    "outputs":[]
  }
]

if not CONFIG["MARKETPLACE_ADDRESS"]:
    logger.error("MARKETPLACE_ADDRESS not set in .env. Exiting.")
    raise SystemExit("MARKETPLACE_ADDRESS not defined")

marketplace_contract = web3.eth.contract(address=Web3.to_checksum_address(CONFIG["MARKETPLACE_ADDRESS"]), abi=MARKETPLACE_V1_ABI)

def send_tx(fn, *args):
    if READ_ONLY or not PRIVATE_KEY or account is None:
        logger.info("Skipping send_tx because READ_ONLY_MODE or no PRIVATE_KEY is set. Simulating action.")
        return None
    try:
        tx = fn(*args).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': 800000,
            'gasPrice': web3.to_wei('1', 'gwei')
        })
        signed = account.sign_transaction(tx)
        tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        logger.info("Transaction mined at block %s, tx hash: %s", receipt.blockNumber, receipt.transactionHash.hex())
        return receipt
    except Exception as e:
        logger.error("Error sending transaction: %s", str(e))
        return None
