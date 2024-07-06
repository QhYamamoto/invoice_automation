from libs.api.Gmail import GmailApi
from libs.api.Misoca import MisocaApi


class Handler:
    def __init__(self) -> None:
        self.__misoca_api = MisocaApi()
        self.__gmail_api = GmailApi()

    def default(self):
        """デフォルト処理(請求書発行 → 請求書PDFダウンロード → メール作成)"""
        self.__misoca_api.set_access_token()

        self.__misoca_api.publish_invoice()

        invoices = self.__misoca_api.get_all_invoices()
        latest_invoice = invoices[0]

        path_to_invoice_pdf = self.__misoca_api.download_invoice_pdf(
            latest_invoice["id"]
        )

        self.__gmail_api.create_invoice_mail_draft(path_to_invoice_pdf)

    def authenticate_gmail(self):
        """ブラウザを使用してGmailの認証処理を手動で行う"""
        self.__gmail_api.authenticate()

    def refresh_gmail_access_token(self):
        """GmailAPI用のアクセストークンを初期化する"""
        self.__gmail_api.refresh_access_token()
