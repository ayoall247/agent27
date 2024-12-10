import os
from src.utils.logger import logger
from src.db import set_job_state
from src.config import CONFIG
from src.contracts import marketplace_contract, send_tx, web3
from src.ipfs_utils import publish_to_ipfs
from eth_account.messages import encode_defunct

READ_ONLY = CONFIG["READ_ONLY_MODE"]
PRIVATE_KEY = CONFIG["PRIVATE_KEY"]

def take_job(job_id: str, revision: int):
    logger.info("Attempting to take job (jobId=%s, revision=%s)", job_id, revision)
    if READ_ONLY or not PRIVATE_KEY:
        reason = "READ_ONLY mode" if READ_ONLY else "no private key"
        logger.info("Skipping takeJob action due to %s, simulating action. Job considered taken.", reason)
        set_job_state(job_id, 'taken (simulated)')
        return

    encoded = web3.codec.encode_abi(['uint256', 'uint256'], [revision, int(job_id)])
    hash_ = web3.keccak(encoded)
    message = encode_defunct(hexstr=hash_.hex())
    signHash = web3.eth.account.sign_message(message, private_key=web3.eth.account._private_key)

    receipt = send_tx(marketplace_contract.functions.takeJob, int(job_id), signHash.signature)
    if receipt:
        logger.info("Job taken successfully on-chain.")
        set_job_state(job_id, 'taken')
    else:
        logger.info("Job take simulated or failed.")

def deliver_job_result(job_id: str, content: str):
    logger.info("Attempting to deliver job result (jobId=%s)", job_id)
    if READ_ONLY or not PRIVATE_KEY:
        reason = "READ_ONLY mode" if READ_ONLY else "no private key"
        logger.info("Skipping deliverResult due to %s. Simulating generation and upload.", reason)
        # We can simulate by just logging
        cid = publish_to_ipfs(content)
        logger.info("Simulated delivery: content uploaded at cid=%s. Would call deliverResult(%s, %s)", cid, job_id, cid)
        set_job_state(job_id, 'delivered (simulated)')
        return

    cid = publish_to_ipfs(content)
    receipt = send_tx(marketplace_contract.functions.deliverResult, int(job_id), cid)
    if receipt:
        logger.info("Result delivered on-chain with cid=%s", cid)
        set_job_state(job_id, 'delivered')
    else:
        logger.info("Delivery simulated or failed.")
