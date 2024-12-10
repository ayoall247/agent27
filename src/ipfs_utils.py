import ipfshttpclient
from src.config import CONFIG
from src.utils.logger import logger

logger.info("Connecting to IPFS via %s", CONFIG["IPFS_API_URL"])
client = ipfshttpclient.connect(CONFIG["IPFS_API_URL"])

def publish_to_ipfs(content: str) -> str:
    logger.info("Publishing content to IPFS...")
    res = client.add_bytes(content.encode('utf-8'))
    logger.info("Content published, cid=%s", res)
    return res

def get_from_ipfs(cid: str) -> str:
    logger.info("Fetching content from IPFS cid=%s", cid)
    data = client.cat(cid)
    return data.decode('utf-8')
