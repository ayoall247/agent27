# Stub encryption logic
def encrypt_utf8_data(data: str, key: str) -> bytes:
    return data.encode('utf-8')

def encrypt_binary_data(data: bytes, key: str) -> bytes:
    return data
