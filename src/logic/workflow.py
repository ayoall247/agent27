import sys
from src.utils.logger import logger
from src.db import add_job
from src.ipfs_utils import publish_to_ipfs
from src.config import CONFIG
from src.contracts import marketplace_contract, send_tx, web3
from eth_abi import encode
from web3.auto import w3

def create_job(title: str, content: str, tags: list[str], amount: float):
    logger.info("Creating a new job: title=%s, amount=%f", title, amount)

    contentHash = w3.keccak(text=content)  # bytes32
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
            logger.info("Decoding events from receipt...")
            job_id_found = None

            # Attempt to decode the known event: JobEvent (assuming this is the event name)
            # If event name differs, replace "JobEvent" with the actual event name from the ABI.
            try:
                job_events = marketplace_contract.events.JobEvent().process_receipt(receipt)
                if job_events and len(job_events) > 0:
                    job_id_found = job_events[0].args.get('jobId')
            except AttributeError:
                # If JobEvent isn't defined, we must try another event or inspect the ABI.
                pass
            except Exception as e:
                logger.debug("Error decoding JobEvent: %s", e)

            if not job_id_found:
                logger.info("No JobEvent found. Trying all events from ABI...")
                for abi_entry in marketplace_contract.abi:
                    if abi_entry.get('type') == 'event':
                        event_name = abi_entry.get('name')
                        event_class = getattr(marketplace_contract.events, event_name, None)
                        if event_class:
                            try:
                                decoded = event_class().process_receipt(receipt)
                                if decoded and len(decoded) > 0:
                                    logger.info("Decoded event %s: %s", event_name, decoded[0].args)
                                    # Check if this event has something like a jobId
                                    # For example:
                                    # job_id_found = decoded[0].args.get('jobId') or decoded[0].args.get('id')
                                    # if job_id_found:
                                    #     break
                            except Exception as ev_e:
                                logger.debug("Could not decode event %s: %s", event_name, ev_e)
                # If we still don't find job_id_found, maybe the event isn't emitted at all.

            if job_id_found:
                job_id_str = str(job_id_found)
                add_job(job_id_str)
                logger.info("Job created on-chain with jobId=%s. Check explorer for event.", job_id_str)
                return job_id_str
            else:
                logger.info("No recognized event found that includes jobId.")
                return None
        else:
            logger.info("Job publishing failed or simulated.")
            return None


def run_workflow():
    from src.logic.sync import sync_jobs
    events = sync_jobs()
    if not events:
        logger.info("No created jobs found, let's create a new one.")
        job_id = create_job("Test AI Content Generation Job", "Minimal cost test job description.", ["DO"], 0.0001)
    else:
        ev = events[0]
        job_id = ev["jobId"]
        logger.info("Found job with jobId=%s (from subsquid)", job_id)
        add_job(job_id)

    if job_id is None:
        logger.info("No job_id determined, cannot proceed with take or deliver steps.")
        logger.info("Main loop iteration complete")
        return

    # If we had a job_id, proceed with take_job, deliver_result, etc.
    logger.info("Main loop iteration complete")
