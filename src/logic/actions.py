import os
from web3 import Web3
from eth_account.messages import encode_defunct
from src.utils.logger import logger
from src.db import set_job_state
from src.config import CONFIG
from src.ipfs_utils import publish_to_ipfs
from src.contracts import marketplace_contract, send_tx, web3

READ_ONLY = os.getenv("READ_ONLY_MODE", "false").lower() == "true"
PRIVATE_KEY = CONFIG["PRIVATE_KEY"]

def take_job(job_id: str):
    # If in read-only mode, or no private key is set, simulate taking the job
    if READ_ONLY or not PRIVATE_KEY:
        reason = "READ_ONLY mode" if READ_ONLY else "no private key"
        logger.info({"jobId": job_id}, f"Skipping takeJob action due to {reason}, simulating action.")
        set_job_state(job_id, 'taken (simulated)')
        return

    logger.info({"jobId": job_id}, "Taking job")

    revision = 0
    encoded = web3.codec.encode_abi(['uint256', 'uint256'], [revision, int(job_id)])
    hash_ = Web3.keccak(encoded)
    message = encode_defunct(hexstr=hash_.hex())
    signHash = web3.eth.account.sign_message(message, private_key=web3.eth.account._private_key)

    receipt = send_tx(marketplace_contract.functions.takeJob, int(job_id), signHash.signature)
    logger.info({"jobId": job_id, "txHash": receipt.transactionHash.hex()}, "Job taken")
    set_job_state(job_id, 'taken')


def deliver_job_result(job_id: str):
    # If in read-only mode, or no private key is set, simulate delivering result
    if READ_ONLY or not PRIVATE_KEY:
        reason = "READ_ONLY mode" if READ_ONLY else "no private key"
        logger.info({"jobId": job_id}, f"Skipping deliverResult action due to {reason}, simulating action.")
        set_job_state(job_id, 'delivered (simulated)')
        return

    logger.info({"jobId": job_id}, "Delivering job result")
    result_content = "Placeholder result delivered by MVP agent"
    result_hash = publish_to_ipfs(result_content)
    receipt = send_tx(marketplace_contract.functions.deliverResult, int(job_id), result_hash)
    logger.info({"jobId": job_id, "txHash": receipt.transactionHash.hex()}, "Result delivered")
    set_job_state(job_id, 'delivered')
