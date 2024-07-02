from dotenv import load_dotenv
from handlers.MisocaApiHandler import MisocaApiHandler

load_dotenv()

misoca_api = MisocaApiHandler()

invoices = misoca_api.get_all_invoices()
print(invoices)
