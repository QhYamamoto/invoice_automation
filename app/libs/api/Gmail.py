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

logger = Logger()


class GmailApi:
    CREDENTIALS_PATH = "/app/storage/credentials"

    def __init__(self) -> None:
        self.__scopes = os.environ["GMAIL_API_SCOPES"].split(",")
        self.__credentials_path = f"{self.CREDENTIALS_PATH}/credentials.json"
        self.__secrets_path = f"{self.CREDENTIALS_PATH}/client_secrets.json"
        self.__client_service = None

    def authenticate(self):
        """oAuth2で経由で認証する"""
        flow = InstalledAppFlow.from_client_secrets_file(
            self.__secrets_path,
            scopes=self.__scopes,
        )

        port = int(os.environ["GCP_REDIRECT_URI_PORT"])
        credentials = flow.run_local_server(
            redirect_uri_trailing_slash=False,
            port=port
        )

        # 認証情報をJSONファイルに保存
        with open(self.__credentials_path, "w") as credentials_file:
            credentials_file.write(credentials.to_json())

    def __get_credentials(self):
        """JSONファイルから認証情報を読み込んでCredentialsインスタンスを取得する
        Returns:
            Credentials: 認証情報
        """
        try:
            with open(self.__credentials_path, "r") as token_file:
                token_info = json.load(token_file)
                return Credentials.from_authorized_user_info(
                    token_info,
                    scopes=self.__scopes
                )
        except Exception as e:
            logger.error(f"Failed to load credentials.json: {str(e)}")
            exit()

    def refresh_access_token(self, credentials=None):
        """アクセストークンをリフレッシュする

        Args:
            credentials (Credentials): 認証情報
        """
        if credentials is None:
            credentials = self.__get_credentials()

        try:
            credentials.refresh(Request())
            with open(self.__credentials_path, "w") as token_file:
                token_file.write(credentials.to_json())
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            exit()

    def __set_client_service(self):
        """Gmail API用のサービスインスタンスをセットする"""
        # NOTE: 利用する機能を追加する場合は引数でscopesを指定できるようにする
        credentials = self.__get_credentials()

        # トークンが無効な場合はリフレッシュする
        if credentials and credentials.expired and credentials.refresh_token:
            self.refresh_access_token(credentials)

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
