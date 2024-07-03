from dotenv import load_dotenv
from handlers.MisocaApiHandler import MisocaApiHandler

load_dotenv()

misoca_api = MisocaApiHandler()
misoca_api.publish_invoice()

invoices = misoca_api.get_all_invoices()
print(invoices[0])
