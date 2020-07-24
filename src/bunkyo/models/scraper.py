import enum
import logging
import os
import time

import dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

dotenv.load_dotenv()
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "")
GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN", "")

logger = logging.getLogger(__name__)

DEFAULT_UUID = "00000000-0000-0000-0000-000000000000"


class ReservationStatus(enum.Enum):
    INVALID = "RESERVATION_STATUS_INVALID"
    VACANT = "RESERVATION_STATUS_VACANT"
    OCCUPIED = "RESERVATION_STATUS_OCCUPIED"
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

    SEARCH_VACANT_ID = "BB1"
    SEARCH_BY_PURPOSE_ID = "BB0"
    SET_PURPOSE_ID = "T10"
    SET_CATEGORY_ID = "T3"

    INSTITUTE_IDS_1 = [
        {
            "T1": [  # 駒込地域活動センター
                ("T1", "0f6eb962-3058-4151-b665-80afaf47c10f"),  # ホールA
                ("T2", "1987bb5f-7cd4-4509-83b5-18f0dc71d832"),  # ホールB
                ("T3", "7cd39244-2d6b-4b5c-9530-cee07bdef83e"),  # ホールA＋B
            ]
        },
        {
            "T2": [  # 不忍通りふれあい館
                ("T1", "701cff5b-4cbc-48b6-9547-b8b2f1733d82"),  # ホール
                ("T2", "7d0d649a-9919-46f2-a94d-f2618cf93f6b"),  # ホール＋スタジオ
            ]
        },
        # {"T3": [("T1", "")]},  # シビックホール大ホール：大ホール
        # {"T4": [("T1", "")]},  # シビックホール小ホール：小ホール
        {
            "T5": [  # シビックホールその他施設
                ("T1", "e07754db-d586-4cf4-be43-2381d64988c5"),  # 多目的室
                ("T2", "020e4cc8-8a12-496e-8963-e93369ddf18a"),  # 練習室1
                ("T3", "f48c4b7e-afa5-4868-9e4f-c6a924b11e59"),  # 練習室2
            ]
        },  # シビックホールその他施設：多目的室、練習室1、練習室2
        {
            "T6": [  # アカデミー文京
                ("T1", "98571d5c-1721-43d5-8f69-89ea2f1f17bc"),  # レクリエーションホール
                ("T2", "6291a051-569d-49cc-bafc-4207a1599880"),  # 音楽室A
                ("T3", "45ab483a-d863-48c8-b63d-1b1fa7077813"),  # 音楽室B
            ]
        },
        {"T7": [("T1", "10152058-ca39-4125-b065-58b3b3a2d211")]},  # アカデミー湯島：視聴覚室
        {
            "T8": [  # アカデミー音羽
                ("T1", "24b9e01e-a268-455b-8d6d-25c74d7710ff"),  # 多目的ホール
                ("T2", "ce7ea8eb-11bf-4643-94c6-583084be3f71"),  # 多目的ホール＋洋室A
            ]
        },
        {
            "T9": [  # アカデミー茗台
                ("T1", "7728c4f9-ab10-43a7-9954-b6c5395905de"),  # レクリエーションホールA
                ("T2", "cbaad24e-a6ea-4063-b9cc-abd9dc38c0d9"),  # レクリエーションホールB
            ]
        },
    ]
    INSTITUTE_IDS_2 = [
        {
            "T1": [  # アカデミー向丘
                ("T1", "5e191f9d-c353-4708-b87a-176ef436ef2f"),  # レクリエーションホール
                ("T2", "bc0a6231-0eae-4414-bee4-ba1c71c79a65"),  # 学習室
                ("T3", "451d926e-aa05-4980-bb4c-d8cb7bbedab7"),  # 音楽室
            ]
        },
        {"T2": [("T1", "f270e13d-be4e-430b-b6d8-451247c4dd39")]},  # 福祉センター江戸川橋：視聴覚室
        {"T3": [("T1", DEFAULT_UUID)]},  # 勤労福祉会館：第3洋室
    ]

    TABLE_HEADER_INFO_ID = "HEADINFO"
    TABLE_HEADER_ID = "BAR0"
    TABLE_ID = "CONTID"
    NEXT_WEEK_ID = "NEXTWEEK"
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
            return ReservationStatus.VACANT.value
        elif self.NG_GIF in img_src:
            return ReservationStatus.OCCUPIED.value
        elif self.KIKANGAIS_GIF in img_src:
            return ReservationStatus.KIKANGAI.value
        elif self.OPEN_GIF in img_src:
            return ReservationStatus.OPEN.value
        else:
            return ReservationStatus.INVALID.value

    def to_rows(self, table):
        res = []
        header = (
            table.find_element_by_id(self.TABLE_HEADER_ID)
            .find_elements_by_css_selector("td")[0]
            .text
        )
        year = int(header.split("年")[0])  # 1月1日の行からは加算される
        for j in range(7):
            row = table.find_element_by_id(f"DAY{j + 1}")
            day = row.find_elements_by_css_selector("table")[0]
            [date, day_of_week] = day.find_element_by_class_name("DAYTX").text.split(
                "\n"
            )
            if date == "1月1日":
                year = year + 1
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
        self.get_element_by_id(self.SEARCH_VACANT_ID).click()  # 施設の空き状況を見る
        self.get_element_by_id(self.SEARCH_BY_PURPOSE_ID).click()  # 利用目的から施設を探す
        self.get_element_by_id(self.SET_PURPOSE_ID).click()  # 趣味文化活動
        self.get_element_by_id(self.SET_CATEGORY_ID).click()  # ピアノ等

    def scraping(self):
        # このメソッドを実行するときは、施設選択画面を開いている必要がある
        institute_ids = self.INSTITUTE_IDS_1 + self.INSTITUTE_IDS_2
        for i, ids in enumerate(institute_ids):
            parent, children = list(ids.keys())[0], list(ids.values())[0]
            for j, child_with_id in enumerate(children):
                child = child_with_id[0]
                institution_id = child_with_id[1]
                if i > len(self.INSTITUTE_IDS_1) - 1:
                    time.sleep(1)  # これがあると安定する
                    self.get_element_by_id(self.NEXT_INSTITUTE_ID).click()
                time.sleep(1)  # これがあると安定する
                self.get_element_by_id(parent).click()
                time.sleep(1)  # これがあると安定する
                self.get_element_by_id(child).click()

                # 建物名・施設名取得
                time.sleep(1)  # これがあると安定する
                title = self.get_element_by_class_name(
                    self.TABLE_HEADER_INFO_ID
                ).text.split(" ")
                building, institute = title[1], title[3]

                # その施設の空き状況を繰り返し取得する
                for k in range(20):
                    # テーブルデータ取得
                    table = self.get_element_by_id(self.TABLE_ID)
                    rows = self.to_rows(table)

                    # データ保存
                    self.reservation_model.append(
                        building, institute, rows, institution_id, k + 1
                    )

                    # 次の週へ
                    if k != 19:
                        try:
                            self.driver.implicitly_wait(0)
                            table.find_element_by_id(self.NEXT_WEEK_ID).click()
                        except NoSuchElementException:
                            logger.info("no next data")
                            self.driver.implicitly_wait(30)
                            break
                        else:
                            self.driver.implicitly_wait(30)

                self.get_element_by_id(self.BACK_TO_INSTITUTE_ID).click()
