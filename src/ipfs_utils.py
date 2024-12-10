import ipfshttpclient
from src.config import CONFIG

client = ipfshttpclient.connect(CONFIG["IPFS_API_URL"])

def publish_to_ipfs(content: str) -> str:
    res = client.add_bytes(content.encode('utf-8'))
    return res

def get_from_ipfs(cid: str) -> str:
    data = client.cat(cid)
    return data.decode('utf-8')
