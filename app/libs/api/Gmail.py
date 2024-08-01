import os
import json
import base64
from email.message import EmailMessage
from os.path import basename
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from libs.Logger import Logger
from libs.api.ApiBase import ApiBase

logger = Logger()


class GmailApi(ApiBase):
    CREDENTIALS_PATH = "/app/storage/credentials"

    def __init__(self) -> None:
        super().__init__()

        self.__scopes = os.environ["GMAIL_API_SCOPES"].split(",")
        self.__client_service = None
        self._secrets_path = f"{self.CREDENTIALS_PATH}/client_secrets.gmail.json"

        try:
            self.__app_flow = InstalledAppFlow.from_client_secrets_file(
                self._secrets_path,
                scopes=self.__scopes,
                redirect_uri=os.environ["GCP_REDIRECT_URI"],
            )
        except Exception as e:
            logger.error(f"Failed to load client_secrets.gmail.json: {str(e)}")
            exit()

        auth_url, _ = self.__app_flow.authorization_url(prompt='consent')
        self._auth_url = auth_url

    ################ 各クラスで実装する処理 ################

    def _refresh_access_token(self):
        """アクセストークンをリフレッシュする

        Args:
            credentials (Credentials): 認証情報
        """
        credentials = self.__get_credentials_instance()

        try:
            credentials.refresh(Request())
            with open(self._credentials_path, "w") as credentials_file:
                credentials_file.write(credentials.to_json())
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            exit()

    def _get_credentials_json(self):
        auth_code = self._indicate_to_set_auth_code()
        self.__app_flow.fetch_token(code=auth_code)
        print("Credentials fetched successfully.")

        return self.__app_flow.credentials.to_json()

    ################ 固有の処理 ################
    def __get_credentials_instance(self):
        """JSONファイルから認証情報を読み込んでCredentialsインスタンスを取得する
        Returns:
            Credentials: 認証情報
        """
        try:
            credentials_dict = self._get_credentials_dict()
            return Credentials.from_authorized_user_info(
                credentials_dict,
                scopes=self.__scopes
            )
        except Exception as e:
            logger.error(f"Failed to load credentials.json: {str(e)}")
            exit()

    def __set_client_service(self):
        """Gmail API用のサービスインスタンスをセットする"""
        # NOTE: 利用する機能を追加する場合は引数でscopesを指定できるようにする
        credentials = self.__get_credentials_instance()

        # トークンが無効な場合はリフレッシュする
        if credentials and credentials.expired and credentials.refresh_token:
            self._refresh_access_token()

        self.__client_service = build("gmail", "v1", credentials=credentials)

    def __attach_pdf(self, message: EmailMessage, attachment_path: str):
        """メールにPDFファイルを添付する"""
        # NOTE: 他の形式のファイルを添付する必要がある場合は改修する必要あり
        try:
            with open(attachment_path, 'rb') as attachment:
                message.add_attachment(
                    attachment.read(),
                    maintype='application',
                    subtype='pdf',
                    filename=basename(attachment_path)
                )
        except Exception as e:
            logger.error(
                f"Failed to attach file {attachment_path}: {str(e)}"
            )
            exit()

    def create_invoice_mail_draft(self, attachment_paths: list[str] | str | None = []):
        """請求書メールの下書きを作成する

        Args:
            attachment_paths (list[str] | str | None): 添付するPDFファイルのパス
        """
        self.__set_client_service()

        if attachment_paths is None:
            attachment_paths = []
        elif type(attachment_paths) is str:
            attachment_paths = [attachment_paths]

        # メールを作成
        message = EmailMessage()

        try:
            with open(os.environ["INVOICE_MAIL_TEMPLATE_PATH"], "r") as template_file:
                message.set_content(template_file.read())
        except Exception as e:
            logger.error(f"Failed to load invoice mail template: {str(e)}")
            exit()

        message["To"] = os.environ["INVOICE_MAIL_TO_ADDRESSES"]
        message["Cc"] = os.environ["INVOICE_MAIL_CC_ADDRESSES"]
        message["From"] = os.environ["INVOICE_MAIL_FROM_ADDRESS"]
        message["Subject"] = os.environ["INVOICE_MAIL_SUBJECT"]

        for attachment_path in attachment_paths:
            self.__attach_pdf(message, attachment_path)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        message = {"message": {"raw": encoded_message}}

        # 下書きを作成
        try:
            draft = (
                self.__client_service
                .users()
                .drafts()
                .create(
                    userId="me",
                    body=message,
                ).execute()
            )
            logger.info(f"Draft created. Draft ID: {draft['id']}")
        except Exception as e:
            logger.error(f"Failed to create draft: {e}")
            exit()
