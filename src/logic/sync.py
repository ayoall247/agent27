import requests
from src.utils.logger import logger
from src.db import get_last_processed_timestamp
from src.config import CONFIG

# This query may or may not reflect the current contract events.
# Adjust if the subsquid indexing changed or if different fields are needed.
JOB_CREATED_QUERY = """
query($fromTimestamp: Int!) {
  jobEvents(
    filter: {
      type_: {equalTo: 0},
      timestamp_: {gt: $fromTimestamp}
    },
    orderBy: timestamp_ASC,
    first: 50
  ) {
    jobId
    timestamp_
    details {
      ... on JobCreatedEvent {
        title
        tags
        amount
        token
        maxTime
        contentHash
        multipleApplicants
        deliveryMethod
        arbitrator
        whitelistWorkers
      }
    }
  }
}
"""

def sync_jobs():
    from_timestamp = get_last_processed_timestamp()
    logger.info("Fetching new created jobs from Subsquid fromTimestamp=%s", from_timestamp)

    response = requests.post(CONFIG["SUBSQUID_URL"], json={
        "query": JOB_CREATED_QUERY,
        "variables": {"fromTimestamp": from_timestamp}
    })
    data = response.json()
    events = data.get("data", {}).get("jobEvents", [])

    logger.info("Received %d events from subsquid", len(events))
    return events
