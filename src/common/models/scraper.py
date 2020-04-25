import os
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class ScraperModel:
    """
    webdriverを設定する\n
    共通ロジックを配置する
    """

    def __init__(self, root_url):
        """
        root_url: 最初に開くurlを設定する
        """
        self.root_url = root_url
        chrome_options = webdriver.ChromeOptions()

        # FIXME ローカル環境で実行するときは、ここを書き換える必要がある
        CHROMEDRIVER_PATH = os.environ.get(
            "CHROMEDRIVER_PATH",
            "/Users/senda_y/src/github.com/shisetsu-scraper/chromedriver",
        )
        GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN", "")

        if GOOGLE_CHROME_BIN:
            chrome_options.binary_location = GOOGLE_CHROME_BIN

        # chrome_options.add_argument("--headless")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(
            executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options,
        )

    def exec_next_page_script(self, script):
        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located,)
            time.sleep(5)
            self.driver.execute_script(script)
        except TimeoutException as e:
            print(f"failed to execute script due to timeout. script={script}")
            raise e
        except Exception as e:
            print(f"failed to execute script: {script}")
            raise e

    def clear(self):
        self.driver.quit()
