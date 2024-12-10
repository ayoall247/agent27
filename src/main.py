import time
from src.utils.logger import logger
from src.logic.sync import sync_jobs
from src.db import get_jobs_to_deliver
from src.logic.actions import deliver_job_result

def main_loop():
    try:
        sync_jobs()
        deliverables = get_jobs_to_deliver()
        for d in deliverables:
            deliver_job_result(d["job_id"])
    except Exception as e:
        logger.error(f"Error in main loop: {e}")

def main():
    logger.info("Agent service started")
    # Run every 30 seconds
    while True:
        main_loop()
        time.sleep(30)

if __name__ == "__main__":
    main()
