from dotenv import load_dotenv
from handlers.MisocaApiHandler import MisocaApiHandler
from libs.Logger import Logger

load_dotenv()
logger = Logger()

logger.info("Process started.")

misoca_api = MisocaApiHandler()
misoca_api.publish_invoice()

invoices = misoca_api.get_all_invoices()
print(invoices[0])

logger.info("Process completed successfully.")
