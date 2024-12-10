from src.config import CONFIG

def should_take_job(tags: list[str], amount: float) -> bool:
    # Accept if "DO" in tags and amount >= MIN_AMOUNT
    return "DO" in tags and amount >= CONFIG["MIN_AMOUNT"]
