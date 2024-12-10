from src.utils.logger import logger
from src.logic.workflow import run_workflow

def main():
    logger.info("Agent service started")
    run_workflow()
    logger.info("Main loop iteration complete")

if __name__ == "__main__":
    main()
