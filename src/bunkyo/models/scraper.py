import enum
import logging
import os
import time

import dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

dotenv.load_dotenv()
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN", "")

logger = logging.getLogger(__name__)


class ReservationStatus(enum.Enum):
    INVALID = "RESERVATION_STATUS_INVALID"
    OK = "RESERVATION_STATUS_OK"
    NG = "RESERVATION_STATUS_NG"
    KIKANGAI = "RESERVATION_STATUS_KIKANGAI"
    OPEN = "RESERVATION_STATUS_OPEN"


class BunkyoScraperModel:
    """
    scraper model for bunkyo-ku
    """

    ROOT_URL = "https://www.yoyaku.city.bunkyo.lg.jp/reselve/k_index.do"

    OK_GIF = "kimg_ptnw_ok.gif"
    NG_GIF = "kimg_ptnw_ng.gif"
    KIKANGAIS_GIF = "kimg_ptnw_de.gif"
    OPEN_GIF = "kimg_ptnw_open.gif"

    INSTITUTE_IDS_1 = [
        {"T1": ["T1", "T2", "T3"]},
        {"T2": ["T1", "T2"]},
        # {"T3": ["T1"]},
        # {"T4": ["T1"]},
        {"T5": ["T1", "T2", "T3"]},
        {"T6": ["T1", "T2", "T3"]},
        {"T7": ["T1"]},
        {"T8": ["T1", "T2"]},
        {"T9": ["T1", "T2"]},
    ]
    INSTITUTE_IDS_2 = [
        {"T1": ["T1", "T2", "T3"]},
        {"T2": ["T1"]},
        {"T3": ["T1"]},
    ]

    NEXT_INSTITUTE_ID = "VS1"
    BACK_TO_INSTITUTE_ID = "FOOT5BTN"

    def __init__(self, start_date, reservation_model):
        self.start_date = start_date
        self.reservation_model = reservation_model

        chrome_options = webdriver.ChromeOptions()

        if GOOGLE_CHROME_BIN:
            chrome_options.binary_location = GOOGLE_CHROME_BIN
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--disable-application-cache")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--hide-scrollbars")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument('--proxy-server="direct://"')
        chrome_options.add_argument("--proxy-bypass-list=*")
        chrome_options.add_argument("--start-maximized")

        self.driver = webdriver.Chrome(
            executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options,
        )
        self.driver.implicitly_wait(30)

    def clear(self):
        self.driver.quit()

    def get_status_from_img_src(self, img_src):
        if self.OK_GIF in img_src:
            return ReservationStatus.OK.value
        elif self.NG_GIF in img_src:
            return ReservationStatus.NG.value
        elif self.KIKANGAIS_GIF in img_src:
            return ReservationStatus.KIKANGAI.value
        elif self.OPEN_GIF in img_src:
            return ReservationStatus.OPEN.value
        else:
            return ReservationStatus.INVALID.value

    def to_rows(self, table):
        res = []
        header = (
            table.find_element_by_id("BAR0").find_elements_by_css_selector("td")[0].text
        )
        year = header.split("年")[0]
        for j in range(7):
            row = table.find_element_by_id(f"DAY{j + 1}")
            day = row.find_elements_by_css_selector("table")[0]
            [date, day_of_week] = day.find_element_by_class_name("DAYTX").text.split(
                "\n"
            )
            status = row.find_elements_by_css_selector("table")[1]
            divs = [
                x.text
                for x in status.find_elements_by_css_selector("tr")[
                    0
                ].find_elements_by_css_selector("td")
            ]
            imgs = [
                x.get_attribute("src")
                for x in status.find_elements_by_css_selector("tr")[
                    1
                ].find_elements_by_css_selector("img")
            ]
            res.append(
                [
                    year,
                    date,
                    day_of_week,
                    divs,
                    [self.get_status_from_img_src(img) for img in imgs],
                ]
            )
        return res

    def get_element_by_id(self, id):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.ID, id))
        )
        return self.driver.find_element_by_id(id)

    def get_element_by_class_name(self, class_name):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        return self.driver.find_elements_by_class_name(class_name)[0]

    def prepare_for_scraping(self):
        self.driver.get(self.ROOT_URL)
        self.get_element_by_id("BB1").click()  # 施設の空き状況を見る
        self.get_element_by_id("BB0").click()  # 利用目的から施設を探す
        self.get_element_by_id("T10").click()  # 趣味文化活動
        self.get_element_by_id("T3").click()  # ピアノ等

    def scraping(self):
        # このメソッドを実行するときは、施設選択画面を開いている必要がある
        institute_ids = self.INSTITUTE_IDS_1 + self.INSTITUTE_IDS_2
        for i, ids in enumerate(institute_ids):
            parent, children = list(ids.keys())[0], list(ids.values())[0]
            for j, child in enumerate(children):
                if i > len(self.INSTITUTE_IDS_1) - 1:
                    self.get_element_by_id(self.NEXT_INSTITUTE_ID).click()
                time.sleep(1)  # これがあると安定する
                self.get_element_by_id(parent).click()
                time.sleep(0.5)  # これがあると安定する
                self.get_element_by_id(child).click()

                # 建物名・施設名取得
                title = self.get_element_by_class_name("HEADINFO").text.split(" ")
                building, institute = title[1], title[3]

                # その施設の空き状況を繰り返し取得する
                for k in range(26):
                    # テーブルデータ取得
                    table = self.get_element_by_id("CONTID")
                    rows = self.to_rows(table)

                    # データ保存
                    self.reservation_model.append(building, institute, rows, k + 1)

                    if k != 25:
                        table.find_element_by_id("NEXTWEEK").click()

                self.get_element_by_id(self.BACK_TO_INSTITUTE_ID).click()
