FROM selenium/standalone-chrome:latest

USER root

RUN apt-get update && apt-get install -y python3-pip

# ChromeDriverの最新バージョンをダウンロード
RUN wget -q -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip \
    && unzip -o /tmp/chromedriver.zip -d /usr/local/bin \
    && rm /tmp/chromedriver.zip

WORKDIR /app

COPY app/ ./

RUN pip3 install -r /app/requirements.txt

CMD ["python3", "/app/main.py"]
