from typing import Any
from selenium.webdriver.support import expected_conditions as EC
import requests
import os
import urllib.parse
from urllib.parse import urlparse, parse_qs
from libs.VirtualBrowser import VirtualBrowser


class MisocaApiHandler:
    def __init__(self) -> None:
        self.__client_id = os.environ['MISOCA_CLIENT_ID']
        self.__client_secret = os.environ['MISOCA_CLIENT_SECRET']
        self.__redirect_uri = os.environ['MISOCA_REDIRECT_URI']
        self.__base_url = os.environ['MISOCA_BASE_URL']
        self.__email = os.environ['MISOCA_EMAIL']
        self.__password = os.environ['MISOCA_PASSWORD']
        self.__access_token = self.__get_access_token()

    def __generate_url(self, path: str, query_params: dict[str, str] | None = None):
        """ApiのURLを生成する

        Args:
            path (str): APIのパス
            query_params (dict | None): クエリパラメータ

        Returns:
            str: 生成されたURL
        """
        path = path.strip('/')
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

        # 仮想ブラウザで認証画面を開く
        auth_request_url = self.__generate_url('/oauth2/authorize', {
            'response_type': 'code',
            'client_id': self.__client_id,
            'redirect_uri': self.__redirect_uri,
            'scope': 'write'
        })
        driver.get(auth_request_url)

        # 次の画面へのaタグを取得
        a_tag = virtual_browser.get_element(
            '.c-btn--l.c-btn--yayoi.c-btn--block.u-margin-bottom--small'
        )
        a_tag.click()

        # ID(メールアドレス)入力画面
        yayoi_id_field = virtual_browser.get_element('#yayoi_id_input')
        yayoi_id_field.send_keys(self.__email)
        next_button = virtual_browser.get_element('#next_btn')
        next_button.click()

        # パスワード入力画面
        password_field = virtual_browser.get_element('#password_input')
        password_field.send_keys(self.__password)
        login_button = virtual_browser.get_element('#login_btn')
        login_button.click()

        # リダイレクトされたURLから認証コードを抽出
        virtual_browser.wait_until(EC.url_contains("code="))
        current_url = driver.current_url
        driver.quit()

        # 認証コードを用いてトークンを取得する
        auth_code = parse_qs(urlparse(current_url).query)['code'][0]
        token_data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.__redirect_uri,
            'client_id': self.__client_id,
            'client_secret': self.__client_secret
        }
        token_response = requests.post(
            self.__generate_url('/oauth2/token'),
            data=token_data,
        )

        parsed_response = token_response.json()
        return parsed_response['access_token']

    def __get_authorization_header(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.__access_token}'}

    def __check_access_token(self) -> None:
        if not self.__access_token:
            raise Exception('Access token is not set.')

    def get_all_invoices(self) -> list[dict[str, Any]]:
        """請求書を全件取得する

        Returns:
            list[dict[str, Any]]: 請求書のリスト
        """
        self.__check_access_token()

        response = requests.get(
            self.__generate_url('/api/v3/invoices'),
            headers=self.__get_authorization_header(),
        )
        return response.json()
