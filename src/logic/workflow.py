from src.utils.logger import logger
from src.logic.sync import sync_jobs
from src.logic.actions import take_job, deliver_job_result
from src.db import add_job, set_job_state
from src.logic.filters import shouldTakeJob
from src.config import CONFIG
from src.contracts import marketplace_contract, send_tx, web3
from src.ipfs_utils import publish_to_ipfs
from src.logic.generation import simulate_generation_and_upload

def create_job(title: str, content: str, tags: list[str], amount: float):
    logger.info("Creating a new job: title=%s, amount=%f", title, amount)
    # For simplicity, use a fake token from config or a known token
    token = "0x0000000000000000000000000000000000000000"
    contentCid = publish_to_ipfs(content)
    logger.info("Content hash: %s", contentCid)
    multipleApplicants = True
    arbitrator = "0x0000000000000000000000000000000000000000"
    deadline = 3600
    delivery = "ipfs"
    whitelist = []
    # Convert amount to wei if needed. Assume 18 decimals
    amountWei = web3.to_wei(amount, 'ether')

    if CONFIG["READ_ONLY_MODE"] or not CONFIG["PRIVATE_KEY"]:
        logger.info("Simulating job creation due to read-only or no private key. Would call publishJobPost.")
        # Just log and pretend we got jobId=123
        job_id = "123"
        add_job(job_id)
        logger.info("Simulated job created with jobId=%s", job_id)
        return "123"
    else:
        # Actual tx
        tx = send_tx(marketplace_contract.functions.publishJobPost,
                     title, contentCid, multipleApplicants, tags, token, amountWei,
                     deadline, delivery, arbitrator, whitelist)
        if tx:
            # parse logs to find jobId if possible
            logger.info("Job published. Checking logs for JobEvent.")
            # In a real scenario, parse logs
            # Simulate jobId=0
            job_id = "0"
            add_job(job_id)
            return job_id
        else:
            logger.info("Job publishing failed or simulated.")
            return None

def run_workflow():
    # 1. Sync jobs
    events = sync_jobs()
    job_id = None
    if not events:
        logger.info("No created jobs found, let's create a new one.")
        job_id = create_job("Test AI Content Generation Job", "This is a sample job description for testing all features.", ["DO"], 200)
    else:
        ev = events[0]
        job_id = ev["jobId"]
        logger.info("Found job with jobId=%s (from subsquid)", job_id)
        add_job(job_id)

    # 2. Check if we should take the job
    # Simulate we know tags and amount from event or from a guess
    # In a real scenario, we'd have more complex logic
    tags = ["DO"]
    amount = 200.0
    if shouldTakeJob(tags, amount):
        logger.info("Criteria met, attempting to take jobId=%s", job_id)
        revision = 0  # for simplicity
        take_job(job_id, revision)
        set_job_state(job_id, 'taken')
    else:
        logger.info("Criteria not met for jobId=%s, skipping take", job_id)

    # 3. Deliver result (simulated or real)
    # If read-only, simulate generation and upload
    if CONFIG["READ_ONLY_MODE"] or not CONFIG["PRIVATE_KEY"]:
        logger.info("Read-only mode or no private key, simulating content generation and delivery.")
        job_details = {"title": "Test AI Content Generation Job", "content": "Sample job desc."}
        simulate_generation_and_upload(job_id, job_details)
        set_job_state(job_id, 'delivered (simulated)')
    else:
        logger.info("Delivering a real result for jobId=%s", job_id)
        content = "Real deliverable content"
        deliver_job_result(job_id, content)

    # 4. Dispute logic (simulate)
    logger.info("Simulating dispute on jobId=%s (no on-chain call in read-only)", job_id)
    logger.info("Would call dispute(jobId, encryptedSessionKey, encryptedContent) if we had keys and reason.")
    # Just log for now

    # 5. Approve result or finalize
    logger.info("In a real scenario, we could now approveResult or raise a dispute on-chain.")

    # 6. Done
    logger.info("Workflow completed for jobId=%s", job_id)
