from typing import Any
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver as _WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class VirtualBrowser():
    def __init__(self) -> None:
        # WebDriverをセットアップ
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.__driver: _WebDriver = webdriver.Chrome(options=options)

    def get_driver(self) -> _WebDriver:
        """WebDriverを取得する"""
        return self.__driver

    def get_element(self, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10) -> WebElement:
        """画面上の要素を取得する

        Args:
            selector (str): セレクタ
            by (str): セレクタの種類
            timeout (int): 最大待機時間

        Returns:
            WebElement: 取得した要素
        """
        return WebDriverWait(self.__driver, timeout).until(EC.presence_of_element_located((by, selector)), timeout)

    def wait_until(self, condition: Any, timeout: int = 10) -> None:
        """仮想ブラウザで特定の条件が満たされるまで待機する

        Args:
            condition (Any): 条件
            timeout (int): 最大待機時間
        """
        WebDriverWait(self.__driver, timeout).until(condition)
