import sys
from dotenv import load_dotenv
from Handler import Handler
from libs.Logger import Logger

try:
    load_dotenv()

    command = sys.argv[1] if len(sys.argv) > 1 else "default"

    logger = Logger()
    handler = Handler()
    logger.info("Process started.")

    try:
        getattr(handler, command)()
    except AttributeError as e:
        logger.error(f"Failed to execute Handler method: {str(e)}")
        exit()

except Exception as e:
    logger.error(f"Unexpected error occurred: {str(e)}")
    exit()

logger.info("Process completed successfully.")
