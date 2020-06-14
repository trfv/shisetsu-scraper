import datetime
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
    PARTIALLY_VACANT = "RESERVATION_STATUS_PARTIALLY_VACANT"
    OCCUPIED = "RESERVATION_STATUS_OCCUPIED"
    KIKANGAI = "RESERVATION_STATUS_KIKANGAI"
    CLOSED = "RESERVATION_STATUS_CLOSED"
    OUT_OF_TARGRT = "RESERVATION_STATUS_OUT_OF_TARGRT"
    APPLIABLE = "RESERVATION_STATUS_APPLIABLE"


class ToshimaScraperModel:
    """
    scraper model for toshima-ku
    """

    ROOT_URL = "https://www2.pf489.com/toshima/web/Wg_ModeSelect.aspx"

    SEARCH_YOYAKU＿MENU_ID = "btnNormal"
    SEARCH_VACANT_ID = "rbtnYoyaku"
    SEARCH_PURPOSE_ID = "btnMokuteki"
    SELECT_CATEGORY_ID = "ucOecRadioButtonList_dgButtonList_ctl02_rdSelectLeft"
    PURPOSE_NEXT_PAGE_BUTTON_ID = "ucButtonList_btnNext"
    SELECT_PURPOSE_ID = "ucButtonList_dgButtonList_ctl06_chkSelectLeft"
    NEXT_BUTTON_ID = "ucPCFooter_btnForward"
    SHOW_INSTITUTE_LIST_BUTTON_ID = "btnList"

    INSTITUTE_IDS = [
        "dgShisetsuList_ctl02_chkSelectLeft",
        "dgShisetsuList_ctl03_chkSelectLeft",
        "dgShisetsuList_ctl04_chkSelectLeft",
        "dgShisetsuList_ctl05_chkSelectLeft",
        "dgShisetsuList_ctl06_chkSelectLeft",
        "dgShisetsuList_ctl07_chkSelectLeft",
        "dgShisetsuList_ctl08_chkSelectLeft",
        "dgShisetsuList_ctl09_chkSelectLeft",
        "dgShisetsuList_ctl02_chkSelectRight",
        "dgShisetsuList_ctl03_chkSelectRight",
        "dgShisetsuList_ctl04_chkSelectRight",
        "dgShisetsuList_ctl05_chkSelectRight",
        "dgShisetsuList_ctl06_chkSelectRight",
        # "dgShisetsuList_ctl07_chkSelectRight", 南大塚ホール
        "dgShisetsuList_ctl08_chkSelectRight",
    ]

    SELECT_MONTH_ID = "rbtnMonth"
    MONTH_INPUT_ID = "txtMonth"
    DAT_INPUT_ID = "txtDay"
    DIVISION_IDS = [
        "rbtnAm",
        "rbtnPm",
        "rbtnNight",
    ]

    DISPLAY_START_DATE_INPUT_ID = "ucTermSetting_txtDateFrom"
    TABLE_ID = "dlRepeat"
    NEXT_MONTH_BTN_ID = "btnNextPeriod"
    BACK_TO_DATE_SELECT_BTN_ID = "ucPCSideMenuBody_DataListBody_ctl08_ucPCSideMenuItem_dataListItem_ctl00_lnkBtnGoPage"

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

    def get_status_from_text(self, text):

        if "○" in text:
            return ReservationStatus.VACANT.value
        elif "△" in text:
            return ReservationStatus.PARTIALLY_VACANT.value
        elif "×" in text:
            return ReservationStatus.OCCUPIED.value
        elif "－" in text:
            return ReservationStatus.KIKANGAI.value
        elif "休館" in text or "なし" in text:
            return ReservationStatus.CLOSED.value
        elif "＊" in text:
            return ReservationStatus.OUT_OF_TARGRT.value
        elif "抽選" in text:
            return ReservationStatus.APPLIABLE.value
        else:
            return ReservationStatus.INVALID.value

    def to_rows(self, building, dateLine, statusLine):
        res = []
        institute = statusLine.find_elements_by_css_selector("td")[0].text.split("…")[0]
        yearMonth, div = dateLine.find_elements_by_css_selector("td")[0].text.split(
            "\n"
        )
        for x, y in zip(
            dateLine.find_elements_by_css_selector("td")[2:],
            statusLine.find_elements_by_css_selector("td")[2:],
        ):
            date, day_of_week = x.text.split("\n")
            status = y.text
            res.append(
                [
                    building,
                    institute,
                    yearMonth + date,
                    day_of_week,
                    div,
                    self.get_status_from_text(status),
                ]
            )
        return res

    def get_element_by_id(self, id):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.ID, id))
        )
        return self.driver.find_element_by_id(id)

    def wait_for_load_reservation_page(self, previous_value):
        for _ in range(6):
            try:
                input = self.get_element_by_id(self.DISPLAY_START_DATE_INPUT_ID)
                if input.get_attribute("value") == previous_value:
                    raise Exception("not transfered yet.")
                else:
                    break
            except Exception as e:
                logger.info(e)
                time.sleep(10)

    def prepare_for_scraping(self):
        self.driver.get(self.ROOT_URL)
        self.get_element_by_id(self.SEARCH_YOYAKU＿MENU_ID).click()  # 公共施設予約メニュー
        self.get_element_by_id(self.SEARCH_VACANT_ID).click()  # 空き照会・予約の申込
        self.get_element_by_id(self.SEARCH_PURPOSE_ID).click()  # 使用目的で探す
        self.get_element_by_id(self.SELECT_CATEGORY_ID).click()  # 文化・集会活動
        self.get_element_by_id(self.PURPOSE_NEXT_PAGE_BUTTON_ID).click()  # 次頁
        self.get_element_by_id(self.SELECT_PURPOSE_ID).click()  # 楽器演奏
        self.get_element_by_id(self.NEXT_BUTTON_ID).click()  # 次へ
        time.sleep(1)  # これがあると安定する
        self.get_element_by_id(self.NEXT_BUTTON_ID).click()  # 次へ

    def scraping(self):
        # このメソッドを実行するときは、 空き照会・予約の申込 施設選択を開いている必要がある
        self.get_element_by_id(self.SHOW_INSTITUTE_LIST_BUTTON_ID).click()  # 一覧表示
        for institute_id in self.INSTITUTE_IDS:
            self.get_element_by_id(institute_id).click()  # 施設を選択する
        time.sleep(1)  # これがあると安定する
        self.get_element_by_id(self.NEXT_BUTTON_ID).click()  # 次へ
        self.get_element_by_id(self.SELECT_MONTH_ID).click()  # 1ヶ月

        now = datetime.datetime.now()
        for division in self.DIVISION_IDS:
            self.get_element_by_id(self.MONTH_INPUT_ID).clear()
            self.get_element_by_id(self.MONTH_INPUT_ID).send_keys(now.month)
            self.get_element_by_id(self.DAT_INPUT_ID).clear()
            self.get_element_by_id(self.DAT_INPUT_ID).send_keys(now.day)
            self.get_element_by_id(division).click()
            self.get_element_by_id(self.NEXT_BUTTON_ID).click()  # 次へ

            display_start_date = ""
            # 月単位で頁送りする
            for j in range(6):  # TODO 年を跨ぐときの処理
                self.wait_for_load_reservation_page(display_start_date)
                display_start_date = self.get_element_by_id(
                    self.DISPLAY_START_DATE_INPUT_ID
                ).get_attribute("value")
                for block in self.get_element_by_id(
                    self.TABLE_ID
                ).find_elements_by_css_selector("font"):
                    table = block.find_elements_by_css_selector("tr")
                    lines = table[2].find_elements_by_css_selector("tr")
                    rows = self.to_rows(
                        table[0].text.split(" ")[0].strip(), lines[0], lines[1]
                    )

                    # データ保存
                    self.reservation_model.append(division, rows, j + 1)

                # 次の月へ
                if j != 5:
                    self.get_element_by_id(self.NEXT_MONTH_BTN_ID).click()

            # 日時選択へもどる
            display_start_date = ""
            self.get_element_by_id(self.BACK_TO_DATE_SELECT_BTN_ID).click()
