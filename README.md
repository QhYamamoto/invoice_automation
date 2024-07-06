## 請求書発行、メール作成自動化プログラム

### 概要

Misoca API と Gmail API を使用して、以下の作業を自動化します。

- 月々の請求書発行(と請求書 PDF のダウンロード)
- 請求書送付メールの作成

### おことわり

- Misoca を使用した請求書発行にのみ対応しています。
- Gmail 以外のメールアドレスを使用している場合は請求書発行のみ可能です。
- docker, docker-compose 導入済みの想定です。
- WSL 環境(Ubuntu 22.04.3 LTS)でのみ動作確認をしています。 (コンテナで実行するので Mac でも大丈夫だとは思いますが...)

### 事前準備

#### 環境変数

1. プロジェクトルートで以下のコマンドを実行する。
   ```sh
   cp ./app/.env.example ./app/.env
   ```
2. コメントを参考に API の認証情報以外の変数に適当な値を設定する。

#### Misoca API

1. Misoca API の[公式サイト](https://doc.misoca.jp/)にアクセスし、アプリケーションの登録を行う。
   - `コールバックURL`はなんでも可です。localhost とかにしておくのが無難です。
2. 登録が完了したら以下の情報を.env に設定する。
   1. アプリケーション ID (.env の`MISOCA_CLIENT_ID`)
   2. シークレット (.env の`MISOCA_CLIENT_SECRET`)

#### Gmail API

1. 使用する Gmail アドレスの GCP アカウントがない場合は作成する。
2. GCP の[コンソール](https://console.cloud.google.com/welcome)にアクセスし、プロジェクトを作成する。
3. [API のライブラリ](https://console.cloud.google.com/apis/library)にアクセスし、2 で作成したプロジェクトで Gmail API を有効化する。
4. [OAuth 同意画面](https://console.cloud.google.com/apis/credentials/consent)にアクセスし、同意画面を新規作成する。
5. [認証情報の作成画面](https://console.cloud.google.com/apis/credentials/oauthclient)にアクセスし、認証情報を新規作成する。
   - `アプリケーションの種類`は`ウェブアプリケーション`とする。
   - `承認済みのリダイレクトURI`に適当な URI を指定する。
6. 認証情報の JSON ファイルをダウンロードし、`client_secrets.json`にリネームして`/app/storage/credentials/`に配置する。
7. 5 で指定した`承認済みのリダイレクトURI`を.env の`GCP_REDIRECT_URI`に設定する。
8. 以下のコマンドを順に実行し、CLI に表示されるメッセージに従って認証フローを実行する。
   ```sh
   docker-compose build
   docker-compose run app python3 /app/main.py authenticate_gmail
   ```
   - CLI に表示される認証用 URL に任意のブラウザでアクセスし、Gmail アカウントでログインしてください。
   - ログイン後、`承認済みのリダイレクトURI`にリダイレクトします。クエリパラメータの`code`を`auth_code.txt`にコピペして保存してください。

### コマンド一覧

1. Docker コンテナをビルドする。

   ```sh
   docker-compose build
   ```

2. デフォルト機能(請求書発行 + メール作成)を実行する。

   ```sh
   docker-compose run app
   ```

3. 請求書発行のみを行う。

   ```sh
   docker-compose run app python3 /app/main.py publish_invoice
   ```

4. Gmail API の認証を行う。

   ```sh
   docker-compose run app python3 /app/main.py authenticate_gmail
   ```

5. Gmail API のアクセストークンをリフレッシュする。
   ```sh
   docker-compose run app python3 /app/main.py refresh_gmail_access_token
   ```

### 備考

- ログは`/app/storage/logs/{年}-{月}.log`に出力されます。
  - .env の`APP_ENV`を`debug`に変更すれば標準出力にログが出力されます。デバッグ時にご利用ください。
- cron やタスクスケジューラ等で月初に自動実行するようにしておくといいかもです。

### 注意点

#### Gmail API のトークンについて

- Gmail API 用のアクセストークンは、リフレッシュトークンが有効である場合のみ自動的にリフレッシュされます。
  - 手動でアクセストークンをリフレッシュする場合は以下のコマンドを実行してください。
    ```sh
    docker-compose run app python3 /app/main.py refresh_gmail_access_token
    ```
- [OAuth 同意画面](https://console.cloud.google.com/apis/credentials/consent)のステータスが Testing 状態である場合、リフレッシュトークンは 7 日で無効化されます。
  - とりあえず Production モードにしておいて認証を実行すれば有効期限なしのリフレッシュトークンを取得できる(かも? 今後要確認。)
- リフレッシュトークンが無効化されてしまった場合は事前準備の 8 を再度実行してください。
