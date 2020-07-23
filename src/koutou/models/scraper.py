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
    VACANT = "RESERVATION_STATUS_VACANT"
    OCCUPIED = "RESERVATION_STATUS_OCCUPIED"
    CLOSED = "RESERVATION_STATUS_CLOSED"
    KEEP = "RESERVATION_STATUS_KEEP"
    KIKANGAI = "RESERVATION_STATUS_KIKANGAI"
    SOUND = "RESERVATION_STATUS_SOUND"


class KoutouScraperModel:
    """
    scraper model for koutou-ku
    """

    ROOT_URL = "https://sisetun.kcf.or.jp/web/"

    EMPTYBS_GIF = "image/lw_emptybs.gif"
    FINISHS_GIF = "image/lw_finishs.gif"
    CLOSES_GIF = "image/lw_closes.gif"
    KEEPS_GIF = "image/lw_keeps.gif"
    KIKANGAIS_GIF = "image/lw_kikangais.gif"
    SOUND_GIF = "image/lw_sound.gif"

    TITLE_XPATH = '//*[@id="disp"]/center/table[3]/tbody[2]/tr[2]/td[2]/a/font/b'
    TABLE_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody[2]/tr[3]/td[2]/center/table/tbody'
    )

    SEARCH_VACANT_XPATH = '//*[@id="disp"]/center/form/table[4]/tbody/tr[2]/td/a[1]'
    SEARCH_MULTIPLE_XPATH = '//*[@id="disp"]/center/table[2]/tbody/tr[2]/td/a'
    SET_CATEGORY_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody/tr[2]/td[2]/table/tbody/tr[1]/td[1]/a'
    )
    CHANGE_CATEGORY_XPATH = '//*[@id="disp"]/center/table[3]/tbody/tr[4]/td[2]/a'
    SET_PURPOSE_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody/tr[2]/td[2]/table/tbody/tr[1]/td[3]/a'
    )
    CHANGE_PURPOSE_XPATH = '//*[@id="disp"]/center/table[3]/tbody/tr[4]/td[3]/a'
    SET_INSTITUTE_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody/tr[2]/td[2]/table/tbody/tr[3]/td[1]/a'
    )
    INSTITUTE_XPATHS_AND_ID = [
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[2]/td[4]/a',
            "5efcfead-45d1-4ebc-aaea-ff10b68dc759",
        ),  # 江東区文化センター レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[2]/td[6]/a',
            "451832cb-7086-4fc8-a097-fca7a8259cbc",
        ),  # 江東区文化センター サブ・レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[3]/td[2]/a',
            "37f928c6-a487-4866-a51b-f66a153f89cc",
        ),  # 江東区文化センター 大研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[3]/td[4]/a',
            "cb03753a-c82f-4a8d-81c7-a64e0a38fbda",
        ),  # 江東区文化センター 第１音楽スタジオ
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[3]/td[6]/a',
            "fbcc4d0e-5da7-4f18-967b-2b7d9c614595",
        ),  # 江東区文化センター 第２音楽スタジオ
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[4]/td[2]/a',
            "3a3499ef-2e80-4275-a9db-6e28dfb928b6",
        ),  # 江東区文化センター 教材製作室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[4]/td[4]/a',
            "ff4eb700-8fe8-491a-a327-bf8f9de6e1d6",
        ),  # 江東区文化センター 運営室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[4]/td[6]/a',
            "18408d2e-2742-4769-86a4-a0a0abb243f8",
        ),  # 東大島文化センター レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[5]/td[2]/a',
            "5320a802-e31b-45b7-a846-692127b118f1",
        ),  # 東大島文化センター ＡＶ・ホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[5]/td[4]/a',
            "816cffd3-7262-41b6-9104-ad0a948d5504",
        ),  # 東大島文化センター 第６研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[5]/td[6]/a',
            "a854f781-f768-4395-9d17-47f0022881d9",
        ),  # 東大島文化センター 音楽スタジオ
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[6]/td[2]/a',
            "65e2f55a-e265-4e5d-91b9-62822e1f5bcf",
        ),  # 豊洲文化センター レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[6]/td[4]/a',
            "d28f2e82-0f72-4aca-943a-10c18293dc5d",
        ),  # 豊洲文化センター サブ・レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[6]/td[6]/a',
            "1bfd66ac-1983-45c0-afaf-4935214c6e36",
        ),  # 豊洲文化センター 音楽練習室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[7]/td[2]/a',
            "10f34c41-4493-472b-aa14-113e37cbed4f",
        ),  # 豊洲文化センター 第７研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[7]/td[4]/a',
            "7033422d-f882-42c3-b141-877f303de0d4",
        ),  # 豊洲文化センター 第８研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[7]/td[6]/a',
            "bc494b57-7d78-4e76-909c-e25b7fe3b9f8",
        ),  # 砂町文化センター 第１研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[8]/td[2]/a',
            "12de35f1-c225-4334-bf0b-248616ba3a1e",
        ),  # 砂町文化センター 第２研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[8]/td[4]/a',
            "34939752-60e0-4707-ae54-7d0c2708d4b6",
        ),  # 砂町文化センター サブ・レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[8]/td[6]/a',
            "3fd17f9d-37a3-440f-b479-6a0f8f32ac92",
        ),  # 砂町文化センター 第１音楽室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[9]/td[2]/a',
            "8dd2dd38-6cd3-46c4-b158-1a30669758b1",
        ),  # 砂町文化センター 第２音楽室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[9]/td[4]/a',
            "0cd95c96-878f-4604-8d65-12ba53eafced",
        ),  # 森下文化センター 多目的ホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[9]/td[6]/a',
            "25fc8dd4-b14f-4307-b816-762ab5b99600",
        ),  # 森下文化センター 第１レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[10]/td[2]/a',
            "46efacbd-a5b0-4d9f-9b1a-73f85d129798",
        ),  # 森下文化センター 第２レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[10]/td[4]/a',
            "e75a2ea8-bc9d-4305-9f9f-ebc912fa4498",
        ),  # 森下文化センター ＡＶ・ホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[10]/td[6]/a',
            "e5a55c73-2ac6-4fb1-82df-f1636ed12fe7",
        ),  # 森下文化センター 音楽スタジオ
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[11]/td[2]/a',
            "b3e89c6f-92d8-4bae-8896-513f3d8ca0e9",
        ),  # 古石場文化センター 大研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[11]/td[4]/a',
            "c1bc0403-3a7f-496a-ac61-9d8e06259a54",
        ),  # 古石場文化センター 第２会議室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[11]/td[6]/a',
            "b5d894ce-9a84-47c4-82e2-acbe354e3841",
        ),  # 古石場文化センター 第３研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[12]/td[2]/a',
            "0ac9e0de-8c60-4b2a-b8b5-2ba63357e873",
        ),  # 古石場文化センター 音楽スタジオ
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[12]/td[4]/a',
            "cedcecb1-97b5-4bf9-b8d8-417fbec0b1e1",
        ),  # 亀戸文化センター 大研修室　（２階）
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[12]/td[6]/a',
            "a72e6efd-a14c-4315-8e8d-1027a91fd104",
        ),  # 総合区民センター レクホール
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[13]/td[2]/a',
            "f53ae298-228e-414f-828e-e922b3153ca0",
        ),  # 総合区民センター 第１研修室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[13]/td[4]/a',
            "b39ab11a-2236-4c85-af98-c235c0f7feee",
        ),  # 江東公会堂 リハーサル室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[13]/td[6]/a',
            "9891bcf0-17c5-4692-b698-8e1713a277dc",
        ),  # 江東公会堂 第１練習室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[14]/td[2]/a',
            "9a90c014-7217-4117-a15e-f38809258470",
        ),  # 江東公会堂 第２練習室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[14]/td[4]/a',
            "204c98a5-54a3-422e-b914-589c6f53381a",
        ),  # 江東公会堂 第３練習室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[14]/td[6]/a',
            "7cf0dbd4-6e28-40ff-a648-a2f97336f84d",
        ),  # 江東公会堂 第４練習室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[15]/td[2]/a',
            "a4649611-636a-4756-9c1e-10182f281a4c",
        ),  # 江東公会堂 第５練習室
        (
            '//*[@id="disp"]/center/table[3]/tbody/tr[15]/td[4]/a',
            "91c91063-55b2-4068-989e-710a2e3c6e75",
        ),  # 深川江戸資料館 レクホール
    ]
    SEARCH_XPATH = '//*[@id="disp"]/center/table[3]/tbody/tr[1]/td[2]/a[1]'
    NEXT_WEEK_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody[2]/tr[2]/td[3]/table/tbody/tr/td[3]/a'
    )
    BACK_XPATH = '//*[@id="disp"]/center/table[1]/tbody/tr[2]/td[3]/a[1]'

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
        if img_src == self.ROOT_URL + self.EMPTYBS_GIF:
            return ReservationStatus.VACANT.value
        elif img_src == self.ROOT_URL + self.FINISHS_GIF:
            return ReservationStatus.OCCUPIED.value
        elif img_src == self.ROOT_URL + self.CLOSES_GIF:
            return ReservationStatus.CLOSED.value
        elif img_src == self.ROOT_URL + self.KEEPS_GIF:
            return ReservationStatus.KEEP.value
        elif img_src == self.ROOT_URL + self.KIKANGAIS_GIF:
            return ReservationStatus.KIKANGAI.value
        elif img_src == self.ROOT_URL + self.SOUND_GIF:
            return ReservationStatus.SOUND.value
        else:
            return ReservationStatus.INVALID.value

    def to_rows(self, table):
        res = []
        for index, row in enumerate(table.find_elements_by_css_selector("tr")):
            if index == 0:
                res.append(
                    [
                        d.text.replace("\t", "")
                        for d in row.find_elements_by_css_selector("td")
                    ],
                )
            else:
                arr = []
                for i, item in enumerate(row.find_elements_by_tag_name("td")):
                    if i == 0:
                        arr.append(item.text.replace("\t", ""))
                    else:
                        img = item.find_elements_by_css_selector("img")[0]
                        arr.append(
                            self.get_status_from_img_src(img.get_attribute("src"),),
                        )
                res.append(arr)
        return res

    def get_element_by_xpath(self, xpath):
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.ID, "disp"))
        )
        return self.driver.find_element_by_xpath(xpath)

    def get_element_by_xpath_with_retry(self, xpath):
        errors = []
        for _ in range(5):
            try:
                time.sleep(1)  # これがあると安定する
                return self.get_element_by_xpath(xpath)
            except Exception as e:
                logger.error(e)
            else:
                break
        else:
            logger.error("quit scraping with failure.")
            driver.quit()

    def prepare_for_scraping(self):
        self.driver.get(self.ROOT_URL)
        self.get_element_by_xpath(self.SEARCH_VACANT_XPATH).click()  # 施設の空き状況ボタ
        self.get_element_by_xpath(self.SEARCH_MULTIPLE_XPATH).click()  # 複合検索ボタン
        self.get_element_by_xpath(self.SET_CATEGORY_XPATH).click()  # 利用目的分類ボタン
        self.get_element_by_xpath(
            self.CHANGE_CATEGORY_XPATH
        ).click()  # 利用目的分類を「音楽講習」にする
        self.get_element_by_xpath(self.SET_PURPOSE_XPATH).click()  # 利用目的ボタン
        self.get_element_by_xpath(
            self.CHANGE_PURPOSE_XPATH
        ).click()  # 利用目的を「楽団パート練習（弦楽器）」にする

    def scraping(self):
        # このメソッドを実行するときは、複合検索画面を開いている必要がある
        for xpath_and_id in self.INSTITUTE_XPATHS_AND_ID:
            xpath = xpath_and_id[0]
            institution_id = xpath_and_id[1]
            self.get_element_by_xpath_with_retry(self.SET_INSTITUTE_XPATH).click()
            self.get_element_by_xpath_with_retry(xpath).click()
            self.get_element_by_xpath_with_retry(self.SEARCH_XPATH).click()

            # 建物名・施設名取得
            title = self.get_element_by_xpath(self.TITLE_XPATH)
            [building, institute] = title.text.replace("<br>", "").split("\n")

            # その施設の空き状況を繰り返し取得する
            for i in range(26):  # TODO それぞれの施設の予約期間に応じた回数を設定する
                # テーブルデータ取得
                table = self.get_element_by_xpath(self.TABLE_XPATH)
                rows = self.to_rows(table)

                # データ保存
                self.reservation_model.append(
                    building, institute, rows, institution_id, i + 1
                )

                # 翌週へ
                if i != 25:
                    self.get_element_by_xpath(self.NEXT_WEEK_XPATH).click()

            # 複合検索画面に戻る
            self.get_element_by_xpath_with_retry(self.BACK_XPATH).click()
