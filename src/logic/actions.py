from src.utils.logger import logger
from src.db import set_job_state
from src.config import CONFIG
from src.contracts import marketplace_contract, send_tx, web3
from src.ipfs_utils import publish_to_ipfs
from eth_abi import encode
from web3.auto import w3

def take_job(job_id: str, revision: int):
    if job_id is None:
        logger.error("No job_id provided, cannot take job.")
        return

    logger.info("Attempting to take job (jobId=%s, revision=%s)", job_id, revision)
    if CONFIG["READ_ONLY_MODE"] or not CONFIG["PRIVATE_KEY"]:
        reason = "READ_ONLY mode" if CONFIG["READ_ONLY_MODE"] else "no private key"
        logger.info("Skipping takeJob action due to %s, simulating action. Job considered taken.", reason)
        set_job_state(job_id, 'taken (simulated)')
        return

    # Encode revision and jobId
    encoded = encode(['uint256', 'uint256'], [revision, int(job_id)])
    hash_ = w3.keccak(encoded)

    # Sign the hash
    signature = web3.eth.account.sign_message(
        w3.toBytes(hexstr=hash_.hex()),
        private_key=CONFIG["PRIVATE_KEY"]
    ).signature

    receipt = send_tx(marketplace_contract.functions.takeJob, int(job_id), signature)
    if receipt:
        logger.info("Job taken successfully on-chain.")
        set_job_state(job_id, 'taken')
    else:
        logger.info("Job take simulated or failed.")

def deliver_job_result(job_id: str, content: str):
    if job_id is None:
        logger.error("No job_id, cannot deliver result.")
        return

    logger.info("Attempting to deliver job result (jobId=%s)", job_id)
    if CONFIG["READ_ONLY_MODE"] or not CONFIG["PRIVATE_KEY"]:
        reason = "READ_ONLY mode" if CONFIG["READ_ONLY_MODE"] else "no private key"
        logger.info("Skipping deliverResult due to %s. Simulating generation and upload.", reason)
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
