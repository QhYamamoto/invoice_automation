FROM selenium/standalone-chrome:latest

USER root

RUN apt-get update && apt-get install -y python3-pip python3-venv

# ChromeDriverの最新バージョンをダウンロード
RUN wget -q -O /tmp/chromedriver.zip https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/116.0.5845.96/linux64/chromedriver-linux64.zip \
    && unzip -o /tmp/chromedriver.zip -d /usr/local/bin \
    && rm /tmp/chromedriver.zip

WORKDIR /app

COPY app/ ./

# install packages inside venv
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# copy entrypoint.sh
COPY entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh

# execute command
ENTRYPOINT ["entrypoint.sh"]
CMD ["python3", /app/main.py"]
