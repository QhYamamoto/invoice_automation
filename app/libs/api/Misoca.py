import calendar
import requests
import os
import urllib.parse
from urllib.parse import urlparse, parse_qs
from urllib3.connection import datetime
from libs.Logger import Logger
from libs.VirtualBrowser import VirtualBrowser
from selenium.webdriver.support import expected_conditions as EC
from typing import Any

logger = Logger()


def check_access_token(func):
    def wrapper(self, *args, **kwargs):
        try:
            if not getattr(self, '_MisocaApiHandler__access_token', None):
                raise Exception()
        except Exception as e:
            logger.error("Access token is not set.")
            exit()
        result = func(self, *args, **kwargs)  # オリジナルのメソッドを呼び出す
        return result
    return wrapper


class MisocaApi:
    def __init__(self) -> None:
        self.__client_id = os.environ["MISOCA_CLIENT_ID"]
        self.__client_secret = os.environ["MISOCA_CLIENT_SECRET"]
        self.__redirect_uri = os.environ["MISOCA_REDIRECT_URI"]
        self.__base_url = os.environ["MISOCA_BASE_URL"]
        self.__email = os.environ["MISOCA_EMAIL"]
        self.__password = os.environ["MISOCA_PASSWORD"]
        self.__access_token = self.__get_access_token()

    def __generate_url(self, path: str, query_params: dict[str, str] | None = None):
        """ApiのURLを生成する

        Args:
            path (str): APIのパス
            query_params (dict | None): クエリパラメータ

        Returns:
            str: 生成されたURL
        """
        path = path.strip("/")
        url = f"{self.__base_url}/{path}"

        return (
            url if query_params is None
            else f"{url}?{urllib.parse.urlencode(query_params)}"
        )

    def __get_access_token(self):
        """oAuth2でMisocaにログインしてアクセストークンを取得する

        Returns:
            str: アクセストークン
        """

        virtual_browser = VirtualBrowser()
        driver = virtual_browser.get_driver()

        logger.info("Trying to loggin to Misoca...")

        # 仮想ブラウザで認証画面を開く
        try:
            auth_request_url = self.__generate_url("/oauth2/authorize", {
                "response_type": "code",
                "client_id": self.__client_id,
                "redirect_uri": self.__redirect_uri,
                "scope": "write"
            })
            driver.get(auth_request_url)

            # 次の画面へのaタグを取得
            a_tag = virtual_browser.get_element(
                ".c-btn--l.c-btn--yayoi.c-btn--block.u-margin-bottom--small"
            )
            a_tag.click()

            # ID(メールアドレス)入力画面
            yayoi_id_field = virtual_browser.get_element("#yayoi_id_input")
            yayoi_id_field.send_keys(self.__email)
            next_button = virtual_browser.get_element("#next_btn")
            next_button.click()

            # パスワード入力画面
            password_field = virtual_browser.get_element("#password_input")
            password_field.send_keys(self.__password)
            login_button = virtual_browser.get_element("#login_btn")
            login_button.click()

            # リダイレクトされたURLから認証コードを抽出
            virtual_browser.wait_until(EC.url_contains("code="))
            current_url = driver.current_url
            driver.quit()
        except Exception as e:
            logger.error(f"Failed to loggin: {str(e)}")
            exit()

        logger.info("Succeeded to loggin.")

        logger.info("Trying to get Access token for Misoca...")
        # 認証コードを用いてトークンを取得する
        auth_code = parse_qs(urlparse(current_url).query)["code"][0]
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.__redirect_uri,
            "client_id": self.__client_id,
            "client_secret": self.__client_secret
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

        logger.info("Succeeded to get Access token.")

        parsed_response = token_response.json()
        return parsed_response["access_token"]

    def __get_authorization_header(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.__access_token}"}

    @check_access_token
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

    @check_access_token
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
            "invoice_number": dt_last_month.strftime(f"%Y%m%d-001"),
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

    @check_access_token
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
