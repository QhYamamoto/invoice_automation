import calendar
import json
import requests
import os
import urllib.parse
from urllib3.connection import datetime
from libs.Logger import Logger
from typing import Any
from libs.api.ApiBase import ApiBase

logger = Logger()


class MisocaApi(ApiBase):
    def __init__(self) -> None:
        super().__init__()

        self._auth_url = self.__generate_url("/oauth2/authorize", {
            "response_type": "code",
            "client_id": os.environ["MISOCA_CLIENT_ID"],
            "redirect_uri": os.environ["MISOCA_REDIRECT_URI"],
            "scope": "write",
        })

    ################ 各クラスで実装する処理 ################
    def _get_credentials_json(self):
        auth_code = self._indicate_to_set_auth_code()

        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": os.environ["MISOCA_REDIRECT_URI"],
            "client_id": os.environ["MISOCA_CLIENT_ID"],
            "client_secret": os.environ["MISOCA_CLIENT_SECRET"],
        }

        try:
            token_response = requests.post(
                self.__generate_url("/oauth2/token"),
                data=token_data,
            )

            token_response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get Access token: {str(e)}")
            exit()

        print("Credentials fetched successfully.")

        return json.dumps(token_response.json())

    def _refresh_access_token(self):
        """アクセストークンをリフレッシュする

        Args:
            credentials (Credentials): 認証情報
        """
        credentials_dict = self._get_credentials_dict()
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": credentials_dict["refresh_token"],
            "redirect_uri": os.environ["MISOCA_REDIRECT_URI"],
            "client_id": os.environ["MISOCA_CLIENT_ID"],
            "client_secret": os.environ["MISOCA_CLIENT_SECRET"],
        }

        try:
            token_response = requests.post(
                self.__generate_url("/oauth2/token"),
                data=token_data,
            )

            token_response.raise_for_status()

            with open(self._credentials_path, "w") as credentials_file:
                credentials_file.write(json.dumps(token_response.json()))
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            exit()

    ################ 固有の処理 ################
    def __generate_url(self, path: str, query_params: dict[str, str] | None = None):
        """ApiのURLを生成する

        Args:
            path (str): APIのパス
            query_params (dict | None): クエリパラメータ

        Returns:
            str: 生成されたURL
        """
        base_url = os.environ['MISOCA_BASE_URL']
        path = path.strip("/")
        url = f"{base_url}/{path}"

        return (
            url if query_params is None
            else f"{url}?{urllib.parse.urlencode(query_params)}"
        )

    def __get_authorization_header(self) -> dict[str, str]:
        credentials_dict = self._get_credentials_dict()

        if self._is_token_expired():
            self._refresh_access_token()
            credentials_dict = self._get_credentials_dict()

        return {"Authorization": f"Bearer {credentials_dict["access_token"]}"}

    def get_all_invoices(self) -> list[dict[str, Any]]:
        """請求書を全件取得する

        Returns:
            list[dict[str, Any]]: 請求書のリスト
        """
        logger.info(f"Trying to get invoices...")

        try:
            response = requests.get(
                self.__generate_url("/api/v3/invoices"),
                headers=self.__get_authorization_header(),
            )

            response.raise_for_status()
            logger.info(f"Succeeded to get invoices.")
        except Exception as e:
            logger.error(f"Failed to get invoices: {str(e)}")
            exit()

        return sorted(response.json(), key=lambda x: x["created_at"], reverse=True)

    def publish_invoice(self) -> None:
        """請求書を発行する"""
        dt_now = datetime.datetime.now()
        dt_last_month = dt_now.replace(month=dt_now.month - 1)
        dt_last_date_of_current_month = dt_now.replace(
            day=calendar.monthrange(dt_now.year, dt_now.month)[1]
        )

        subject = os.environ["INVOICE_SUBJECT"]
        recipient_name = os.environ["INVOICE_RECIPIENT_NAME"]
        recipient_title = os.environ["INVOICE_RECIPIENT_TITLE"]
        contact_id = os.environ["INVOICE_CONTACT_ID"]
        sender_name = os.environ["INVOICE_SENDER_NAME"]
        sender_tel = os.environ["INVOICE_SENDER_TEL"]
        sender_email = os.environ["INVOICE_SENDER_EMAIL"]
        notes = os.environ["INVOICE_NOTES"]
        bank_account = os.environ["INVOICE_BANK_ACCOUNT"]
        item_name = os.environ["INVOICE_ITEM_NAME"]
        hourly_wage = os.environ["INVOICE_HOURLY_WAGE"]
        total_working_hours = os.environ["INVOICE_TOTAL_WORKING_HOURS"]

        data = {
            "invoice_number": dt_now.strftime(f"%Y%m%d-001"),
            "issue_date": dt_last_date_of_current_month.strftime("%Y-%m-%d"),
            "subject": dt_last_month.strftime(subject),
            "recipient_name": recipient_name,
            "recipient_title": recipient_title,
            "contact_id": int(contact_id),
            "body": {
                "sender_name1": sender_name,
                "sender_tel": sender_tel,
                "sender_email": sender_email,
                "tax_option": "INCLUDE",
                "tax_rounding_policy": "FLOOR",
                "notes": notes,
                "bank_accounts": [
                    {
                        "detail": bank_account,
                    }
                ],
            },
            "items": [
                {
                    "name": item_name,
                    "quantity": 1.0,
                    "unit_price": float(hourly_wage) * float(total_working_hours),
                    "tax_type": "STANDARD_TAX_10",
                    "excluding_withholding_tax": False,
                },
            ],
        }

        logger.info(f"Trying to publish invoice...")
        try:
            response = requests.post(
                self.__generate_url("/api/v3/invoice"),
                headers=self.__get_authorization_header(),
                json=data,
            )

            response.raise_for_status()
            logger.info(f"Succeeded to publish invoice.")
        except Exception as e:
            logger.error(f"Failed to publish invoice: {str(e)}")
            exit()

    def download_invoice_pdf(self, id: int) -> str:
        """請求書のPDFファイルをダウンロードする

        Args:
            id (int): 請求書ID

        Returns:
            str: ダウンロードしたPDFファイルへのパス
        """
        logger.info(f"Trying to download invoice PDF...")
        try:
            response = requests.get(
                self.__generate_url(f"/api/v3/invoice/{id}/pdf"),
                headers=self.__get_authorization_header(),
            )

            response.raise_for_status()

            dt_now = datetime.datetime.now()
            dt_last_month = dt_now.replace(month=dt_now.month - 1)
            pdf_filename = os.environ["INVOICE_PDF_FILENAME"]
            pdf_file_path = f"/app/storage/invoices/{dt_last_month.strftime(pdf_filename)}.pdf"

            with open(pdf_file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"Succeeded to download invoice PDF.")

            return pdf_file_path
        except Exception as e:
            logger.error(f"Failed to download invoice PDF: {str(e)}")
            exit()
