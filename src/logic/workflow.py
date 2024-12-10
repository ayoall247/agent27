import sys
from src.utils.logger import logger
from src.db import add_job
from src.ipfs_utils import publish_to_ipfs
from src.config import CONFIG
from src.contracts import marketplace_contract, send_tx, web3
from web3.auto import w3
from src.logic.filters import shouldTakeJob
from src.logic.generation import simulate_generation_and_upload
from src.logic.actions import take_job, deliver_job_result
from src.logic.sync import sync_jobs

def create_job(title: str, content: str, tags: list[str], amount: float):
    logger.info("Creating a new job: title=%s, amount=%f", title, amount)
    contentHash = w3.keccak(text=content)
    multipleApplicants = True
    arbitrator = "0x0000000000000000000000000000000000000000"
    deadline = 3600
    delivery = "ipfs"
    whitelist = []
    token = "0x0000000000000000000000000000000000000000"
    amountWei = web3.to_wei(amount, 'ether')

    cid = publish_to_ipfs(content)
    logger.info("Have IPFS cid=%s, but contract expects a bytes32 hash. Using contentHash from keccak.", cid)

    if CONFIG["READ_ONLY_MODE"] or not CONFIG["PRIVATE_KEY"]:
        logger.info("Simulating job creation due to read-only/no private key.")
        job_id = "123"
        add_job(job_id)
        logger.info("Simulated job created with jobId=%s", job_id)
        return job_id
    else:
        confirm = input("You are about to create a job on a live network. This costs real ETH. Proceed? (y/n): ")
        if confirm.lower() != 'y':
            logger.info("Aborted job creation.")
            sys.exit(0)

        receipt = send_tx(
            marketplace_contract.functions.publishJobPost,
            title,
            contentHash,
            multipleApplicants,
            tags,
            token,
            amountWei,
            deadline,
            delivery,
            arbitrator,
            whitelist
        )

        if receipt:
            logger.info("Job creation transaction sent. Check explorer or wait for subsquid indexing to confirm job.")
            # We don't have the jobId directly. We wait for subsquid to index.
            return None
        else:
            logger.info("Job publishing failed or simulated.")
            return None

def run_workflow():
    # Attempt to fetch newly created jobs from subsquid
    events = sync_jobs()

    if not events:
        logger.info("No created jobs found, let's create a new one.")
        create_job("Test AI Content Generation Job", "Minimal cost description.", ["DO"], 0.0001)
        # No jobId known yet. On next run, if subsquid indexes it, we may see it in events.
    else:
        # If we have events, pick the first one as an example
        ev = events[0]
        job_id = str(ev["jobId"])
        logger.info("Found job with jobId=%s (from subsquid)", job_id)
        add_job(job_id)

        # Check if we want to take this job
        # Extract tags and amount from event details if available
        details = ev.get("details", {})
        tags = details.get("tags", [])
        amount_str = details.get("amount", "0")
        # Convert amount_str to float if needed. It's a big number likely in wei, 
        # you may need to convert depending on how subsquid returns it.
        # For simplicity, assume 'amount' is a float in normal units (If not, adjust the logic.)
        try:
            amount_float = float(amount_str)
        except ValueError:
            amount_float = 0.0

        # Decide if we should take the job
        if shouldTakeJob(tags, amount_float):
            logger.info("This job meets our criteria, attempting to take it.")

            # Attempt to take the job if we have private key and not read-only
            if not CONFIG["READ_ONLY_MODE"] and CONFIG["PRIVATE_KEY"]:
                # Using revision=0 as example, depends on contract logic
                take_job(job_id, 0)

                # Once taken, we can simulate generation and deliver result
                job_details = {
                    "title": details.get("title", "Untitled Job"),
                    "content": "This is the job description from subsquid event"
                }
                simulate_generation_and_upload(job_id, job_details)

                # Attempt to deliver result
                content = "Final Result Content"
                deliver_job_result(job_id, content)
            else:
                logger.info("Cannot take job due to read-only mode or missing PRIVATE_KEY.")
        else:
            logger.info("This job does not meet our criteria to take or we choose not to take it.")

    logger.info("Main loop iteration complete")
