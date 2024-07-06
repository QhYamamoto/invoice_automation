from libs.api.Misoca import MisocaApi
from dotenv import load_dotenv
from libs.Logger import Logger

load_dotenv()
logger = Logger()

logger.info("Process started.")

misoca_api = MisocaApi()
misoca_api.publish_invoice()

invoices = misoca_api.get_all_invoices()
latest_invoice = invoices[0]

path_to_invoice_pdf = misoca_api.download_invoice_pdf(latest_invoice["id"])

print(path_to_invoice_pdf)

logger.info("Process completed successfully.")
