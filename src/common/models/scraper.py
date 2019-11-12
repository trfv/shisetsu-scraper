# coding: utf-8
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class ScraperModel:
    """
    base scraper model
    """

    def __init__(self, root_url):
        self.root_url = root_url
        # PATH = "/mnt/d/MSAT/chromedriver/chromedriver.exe"
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

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
