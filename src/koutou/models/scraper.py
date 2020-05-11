import enum
import logging
import os
import time

import dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
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

    SEARCH_VACANT_SCRIPT = "doAction(((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantAction : document.formWTransInstSrchVacantAction ), gRsvWTransInstSrchVacantAction)"
    SEARCH_MULTIPLE_SCRIPT = "doAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction)"
    START_SETTING_CATEGORY_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchPpsdAction);"
    CHANGE_CATEGORY_SCRIPT = "sendPpsdCd((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction, '210')"
    START_SETTING_PURPOSE_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchPpsAction);"
    CHANGE_PURPOSE_SCRIPT = "sendPpsCd((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction, '210' , '21190');"
    START_SETTING_DATE_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchSetDayAction);"
    START_SETTING_INSTITUTE_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchInstAction)"
    CHANGE_INSTITUTE_SCRIPT = "sendInstCd((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction, {index}, {building}, {institute})"
    CHANGE_DATE_SCRIPT = "changeDayGif((_dom == 3) ? document.layers['disp'].document.CalendarDays{day} : document.CalendarDays{day}, {year}, {month}, {day})"
    FINISH_SETTING_DATE_SCRIPT = "sendSelectDay((_dom == 3) ? document.layers['disp'].document.formCommonSrchDayWeekAction : document.formCommonSrchDayWeekAction, gRsvWTransInstSrchMultipleAction, 1)"
    SEARCH_START_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWGetInstSrchInfAction)"
    TO_NEXT_WEEK_SCRIPT = "doTransInstSrchVacantTzoneAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantTzoneAction : document.formWTransInstSrchVacantTzoneAction, gRsvWTransInstSrchVacantAction, 4, gSrchSelectInstNo, gSrchSelectInstMax)"
    TO_NEXT_INSTITUTE_SCRIPT = "doTransInstSrchVacantTzoneAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantTzoneAction : document.formWTransInstSrchVacantTzoneAction, gRsvWTransInstSrchVacantAction, 6, gSrchSelectInstNo, gSrchSelectInstMax)"
    BACK_SCRIPT = "doAction((_dom == 3) ? document.layers['disp'].document.formdisp : document.formdisp, gRsvWInstSrchVacantBackAction)"

    INSTITUTES = [
        ("0", "1010", "1010080"),  # 江東区文化センター レクホール
        ("1", "1010", "1010085"),  # 江東区文化センター サブ・レクホール
        ("2", "1010", "1010100"),  # 江東区文化センター 大研修室
        ("3", "1010", "1010220"),  # 江東区文化センター 第１音楽スタジオ
        ("4", "1010", "1010230"),  # 江東区文化センター 第２音楽スタジオ
        ("5", "1010", "1010260"),  # 江東区文化センター 教材製作室
        ("6", "1010", "1010280"),  # 江東区文化センター 運営室
        ("7", "1020", "1020110"),  # 東大島文化センター レクホール
        ("8", "1020", "1020120"),  # 東大島文化センター ＡＶ・ホール
        ("9", "1020", "1020202"),  # 東大島文化センター 第６研修室
        ("10", "1020", "1020240"),  # 東大島文化センター 音楽スタジオ
        ("11", "1035", "1035050"),  # 豊洲文化センター レクホール
        ("12", "1035", "1035060"),  # 豊洲文化センター サブ・レクホール
        ("13", "1035", "1035070"),  # 豊洲文化センター 音楽練習室
        ("14", "1035", "1035140"),  # 豊洲文化センター 第７研修室
        ("15", "1035", "1035150"),  # 豊洲文化センター 第８研修室
        ("16", "1040", "1040010"),  # 砂町文化センター 第１研修室
        ("17", "1040", "1040020"),  # 砂町文化センター 第２研修室
        ("18", "1040", "1040030"),  # 砂町文化センター サブ・レクホール
        ("19", "1040", "1040130"),  # 砂町文化センター 第１音楽室
        ("20", "1040", "1040140"),  # 砂町文化センター 第２音楽室
        ("21", "1050", "1050010"),  # 森下文化センター 多目的ホール
        ("22", "1050", "1050020"),  # 森下文化センター 第１レクホール
        ("23", "1050", "1050022"),  # 森下文化センター 第２レクホール
        ("24", "1050", "1050030"),  # 森下文化センター ＡＶ・ホール
        ("25", "1050", "1050130"),  # 森下文化センター 音楽スタジオ
        ("26", "1060", "1060010"),  # 古石場文化センター 大研修室
        ("27", "1060", "1060030"),  # 古石場文化センター 第２会議室
        ("28", "1060", "1060060"),  # 古石場文化センター 第３研修室
        ("29", "1060", "1060120"),  # 古石場文化センター 音楽スタジオ
        ("30", "1070", "1070060"),  # 亀戸文化センター 大研修室　（２階）
        ("31", "1080", "1080010"),  # 総合区民センター レクホール
        ("32", "1080", "1080140"),  # 総合区民センター 第１研修室
        ("33", "1090", "1090180"),  # 江東公会堂 リハーサル室
        ("34", "1090", "1090190"),  # 江東公会堂 第１練習室
        ("35", "1090", "1090201"),  # 江東公会堂 第２練習室
        ("36", "1090", "1090210"),  # 江東公会堂 第３練習室
        ("37", "1090", "1090221"),  # 江東公会堂 第４練習室
        ("38", "1090", "1090230"),  # 江東公会堂 第５練習室
        ("39", "1100", "1100020"),  # 深川江戸資料館 レクホール
    ]

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

    def __init__(self, start_date, reservation_model):
        self.start_date = start_date
        self.reservation_model = reservation_model

        chrome_options = webdriver.ChromeOptions()

        if GOOGLE_CHROME_BIN:
            chrome_options.binary_location = GOOGLE_CHROME_BIN
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(
            executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options,
        )

    def exec_next_page_script(self, script):
        try:
            WebDriverWait(self.driver, 60).until(EC.presence_of_all_elements_located,)
            time.sleep(5)
            self.driver.execute_script(script)
        except TimeoutException as e:
            logger.error(f"failed to execute script due to timeout. script={script}")
            raise e
        except Exception as e:
            logger.error(f"failed to execute script: {script}")
            raise e

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

    def prepare_for_scraping(self):
        self.driver.get(self.ROOT_URL)
        self.exec_next_page_script(self.SEARCH_VACANT_SCRIPT)  # 施設の空き状況ボタン
        self.exec_next_page_script(self.SEARCH_MULTIPLE_SCRIPT)  # 複合検索ボタン
        self.exec_next_page_script(self.START_SETTING_CATEGORY_SCRIPT)  # 利用目的分類ボタン
        self.exec_next_page_script(self.CHANGE_CATEGORY_SCRIPT)  # 利用目的分類を「音楽講習」にする
        self.exec_next_page_script(self.START_SETTING_PURPOSE_SCRIPT)  # 利用目的ボタン
        self.exec_next_page_script(self.CHANGE_PURPOSE_SCRIPT)  # 利用目的を「楽団パート練習（弦楽器）」にする

    def scraping(self):
        # このメソッドを実行するときは、複合検索画面を開いている必要がある
        for institute_info in self.INSTITUTES:
            self.exec_next_page_script(self.START_SETTING_INSTITUTE_SCRIPT)
            self.exec_next_page_script(
                self.CHANGE_INSTITUTE_SCRIPT.format(
                    index=institute_info[0],
                    building=institute_info[1],
                    institute=institute_info[2],
                )
            )
            self.exec_next_page_script(self.SEARCH_START_SCRIPT)  # 複合検索ボタン

            # dispというIDのテーブルが読み込まれるまでは待機
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.ID, "disp")),
                )
            except TimeoutException:
                logger.error(
                    "failed to load table due to timeout. stop scraping and try to save current data."
                )
                break

            # 建物名・施設名取得
            title = self.driver.find_element_by_xpath(self.TITLE_XPATH)
            [building, institute] = title.text.replace("<br>", "").split("\n")

            # その施設の空き状況を繰り返し取得する
            for i in range(2):  # TODO それぞれの施設の予約期間に応じた回数を設定する
                # dispというIDのテーブルが読み込まれるまでは待機
                try:
                    WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.ID, "disp")),
                    )
                except TimeoutException:
                    logger.error(
                        "failed to load table due to timeout. stop scraping and try to save current data."
                    )
                    break

                # テーブルデータ取得
                table = self.driver.find_element_by_xpath(self.TABLE_XPATH)
                rows = self.to_rows(table)

                # データ保存
                self.reservation_model.append(building, institute, rows, i + 1)

                # 翌週へ
                if i != 2:
                    try:
                        self.exec_next_page_script(self.TO_NEXT_WEEK_SCRIPT)
                    except Exception:
                        logger.error(
                            "failed to go to next week. stop scraping and try to save current data."
                        )
                        break

            # 複合検索画面に戻る
            self.exec_next_page_script(self.BACK_SCRIPT)
