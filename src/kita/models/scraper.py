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


class ReservationStatus(enum.Enum):
    INVALID = "RESERVATION_STATUS_INVALID"
    VACANT = "RESERVATION_STATUS_VACANT"
    OCCUPIED = "RESERVATION_STATUS_OCCUPIED"
    KEEP = "RESERVATION_STATUS_KEEP"
    CLOSED = "RESERVATION_STATUS_CLOSED"
    QUESTIION = "RESERVATION_STATUS_QUESTION"


class KitaScraperModel:
    """
    scraper model for kita-ku
    """

    ROOT_URL = "https://yoyaku.city.kita.tokyo.jp/shisetsu/reserve/gin_menu"

    OK_GIF = "icon_timetable_O.gif"
    NG_GIF = "icon_timetable_X.gif"
    MAINTE_GIF = "icon_timetable_mainte.gif"
    CLOSE_GIF = "icon_timetable_close.gif"
    QUESTION_GIF = "icon_timetable_question.gif"

    SEARCH_EASY_NAME = "RiyosyaForm"
    SEARCH_VACANT_XPATH = '//*[@id="check_status"]/dd/ul/form'
    SEARCH_KAIKAN_ID = "button0"
    SEARCH_MUSIC_XPATH = (
        '//*[@id="inner-contents"]/form/ul/div/div/div/div/div/div/div/li/a'
    )

    INSTITUTE_IDS = [
        {
            "id0": [
                "button0",
                "button1",
                "button2",
                "button3",
                "button4",
                "button5",
                "button6",
                "button7",
                "button8",
                "button9",
                "button10",
            ]
        },
        {
            "id1": [
                "button0",
                "button1",
                "button2",
                "button3",
                "button4",
                "button5",
                "button6",
                "button7",
            ]
        },
        {"id2": ["button0", "button1"]},
    ]

    FACILITY_CLASS_NAME = "facilities"
    TABLE_ID = "11"
    OK_BUTTON_ID = "btnOK"
    CHANGE_MULTIPLE_DATE_XPATH = '//*[@id="buttons-navigation"]/ul/li[1]/a'
    NEXT_WEEK_XPATH = '//*[@id="timetable"]/ul/li[6]/input'
    BACK_TO_INSTITUTE_XPATH = '//*[@id="path"]/font[3]/a'

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
        elif self.MAINTE_GIF in img_src:
            return ReservationStatus.KEEP.value
        elif self.CLOSE_GIF in img_src:
            return ReservationStatus.CLOSED.value
        elif self.QUESTION_GIF in img_src:
            return ReservationStatus.QUESTIION.value
        else:
            return ReservationStatus.INVALID.value

    def to_rows(self, table):
        res = []
        divs = [
            th.text
            for th in table.find_elements_by_css_selector("thead")[
                0
            ].find_elements_by_css_selector("th")[1:]
        ]
        for tbody in table.find_elements_by_css_selector("tbody"):
            day = tbody.find_elements_by_css_selector("th")[0].text.split("(")
            date, day_of_week = day[0], day[1][0]
            imgs = [
                td.find_elements_by_css_selector("img")[0].get_attribute("src")
                for td in tbody.find_elements_by_css_selector("td")
            ]
            res.append(
                [
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

    def get_element_by_name(self, name):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.NAME, name))
        )
        return self.driver.find_elements_by_name(name)[0]

    def get_element_by_class_name(self, class_name):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        return self.driver.find_elements_by_class_name(class_name)[0]

    def get_element_by_xpath(self, xpath):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return self.driver.find_element_by_xpath(xpath)

    def prepare_for_scraping(self):
        self.driver.get(self.ROOT_URL)
        self.get_element_by_name(self.SEARCH_EASY_NAME).click()  # 簡単操作
        self.get_element_by_xpath(self.SEARCH_VACANT_XPATH).click()  # 空き状況確認
        self.get_element_by_id(self.SEARCH_KAIKAN_ID).click()  # 会館
        self.get_element_by_xpath(self.SEARCH_MUSIC_XPATH).click()  # 音楽

    def scraping(self):
        # このメソッドを実行するときは、施設選択画面を開いている必要がある
        for ids in self.INSTITUTE_IDS:
            parent, children = list(ids.keys())[0], list(ids.values())[0]
            for child in children:
                self.get_element_by_id(parent).click()
                self.get_element_by_id(child).click()
                self.get_element_by_id(self.OK_BUTTON_ID).click()
                self.get_element_by_xpath(self.CHANGE_MULTIPLE_DATE_XPATH).click()

                # 建物名・施設名取得
                title = self.get_element_by_class_name(
                    self.FACILITY_CLASS_NAME
                ).text.split()
                building, institute = title[0], title[1].split("（")[0]

                # その施設の空き状況を繰り返し取得する
                for i in range(26):  # TODO
                    # テーブルデータ取得
                    table = self.get_element_by_id(self.TABLE_ID)
                    rows = self.to_rows(table)

                    # データ保存
                    self.reservation_model.append(building, institute, rows, i + 1)

                    # 次の週へ
                    if i != 25:
                        try:
                            self.driver.implicitly_wait(0)
                            next = self.get_element_by_xpath(
                                self.NEXT_WEEK_XPATH
                            ).click()
                        except NoSuchElementException:
                            logger.info("no next data")
                            self.driver.implicitly_wait(30)
                            break
                        else:
                            self.driver.implicitly_wait(30)

                self.get_element_by_xpath(self.BACK_TO_INSTITUTE_XPATH).click()
