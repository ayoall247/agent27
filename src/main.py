from src.utils.logger import logger
from src.logic.workflow import run_workflow

def main():
    logger.info("Agent service started")
    run_workflow()

if __name__ == "__main__":
    main()
