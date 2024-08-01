import json
import os
import time
from libs.Logger import Logger


# TODO: 親クラスとしてもっとまともな実装に改める...

logger = Logger()


class ApiBase:
    """Base class for external Api modules"""

    CREDENTIALS_PATH = "/app/storage/credentials"

    def __init__(self) -> None:
        infix = self.__class__.__name__.lower().replace('api', '')
        self._credentials_path = f"{self.CREDENTIALS_PATH}/credentials.{infix}.json"
        self._auth_url = ""

    ################ 共通処理 ################
    def _is_token_expired(self) -> bool:
        """トークンが期限切れかどうかを判定する
        Returns:
            bool: 期限切れかどうかを示すフラグ
        """
        with open(self._credentials_path, 'r') as credentials_file:
            token_data = json.load(credentials_file)

        expires_in = token_data.get("expires_in")
        created_at = token_data.get("created_at")

        if expires_in is None or created_at is None:
            logger.error(
                "Invalid token data: 'expires_in' or 'created_at' missing."
            )

        expiration_time = created_at + expires_in
        current_time = time.time()

        return current_time > expiration_time

    def _indicate_to_set_auth_code(self):
        """認証用URLを提示し、認証コードがセットするように指示する
        Returns:
            str: セットされた認証コード
        """
        print(
            f"Please go to this URL and authorize the application: {self._auth_url}"
        )

        # ファイルに保存するよう指示
        auth_code_file_path = os.environ["AUTH_CODE_TEMP_FILE_PATH"]
        with open(auth_code_file_path, "w"):
            pass
        os.chmod(auth_code_file_path, 0o777)

        print(
            f"Please save the authorization code in {auth_code_file_path} file"
        )
        print(
            f"Waiting for the authorization code to be saved in {auth_code_file_path}..."
        )

        # 認証コードがファイルに保存されるまで待機
        is_code_set = False
        while not is_code_set:
            with open(auth_code_file_path, 'r') as file:
                if code := file.read().strip():
                    is_code_set = True
            time.sleep(1)

        # ファイルを削除する
        os.remove(auth_code_file_path)

        return code

    def _authenticate(self):
        """oAuth2で経由で認証し、Credentials情報をStorageに保存する"""
        credentials_json = self._get_credentials_json()
        # 認証情報をJSONファイルに保存
        with open(self._credentials_path, 'w') as credentials_file:
            credentials_file.write(credentials_json)

    def _get_credentials_dict(self) -> dict:
        """認証情報のJSONファイルを読み取って辞書形式で返却する
        Returns:
            dict: 認証情報の辞書
        """
        with open(self._credentials_path, "r") as credentials_json:
            return json.load(credentials_json)

    ################ 各クラスで実装する処理 ################
    def _get_credentials_json(self) -> str:
        """Credentials情報を取得してJSON文字列にして返す
        Returns:
            str: Credentials情報のJSON文字列
        """
        print("test")
        return ""

    def _refresh_access_token(self):
        """アクセストークンをリフレッシュする"""
        pass
