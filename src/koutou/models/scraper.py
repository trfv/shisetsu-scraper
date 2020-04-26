import os
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class KoutouScraperModel:
    """
    scraper model for koutou-ku
    """

    ROOT_URL = "https://sisetun.kcf.or.jp/web/"

    SEARCH_VACANT_SCRIPT = "doAction(((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantAction : document.formWTransInstSrchVacantAction ), gRsvWTransInstSrchVacantAction)"
    SEARCH_MULTIPLE_SCRIPT = "doAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction)"
    START_SETTING_DATE_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchSetDayAction);"
    CHANGE_DATE_SCRIPT = "changeDayGif((_dom == 3) ? document.layers['disp'].document.CalendarDays{day} : document.CalendarDays{day}, {year}, {month}, {day})"
    FINISH_SETTING_DATE_SCRIPT = "sendSelectDay((_dom == 3) ? document.layers['disp'].document.formCommonSrchDayWeekAction : document.formCommonSrchDayWeekAction, gRsvWTransInstSrchMultipleAction, 1)"
    SEARCH_START_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWGetInstSrchInfAction)"
    TO_NEXT_INSTITUTE_SCRIPT = "doTransInstSrchVacantTzoneAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantTzoneAction : document.formWTransInstSrchVacantTzoneAction, gRsvWTransInstSrchVacantAction, 6, gSrchSelectInstNo, gSrchSelectInstMax)"

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
    NEXT_BUTTON_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody[1]/tr/td/table/tbody/tr/td[3]/a'
    )

    def __init__(self, start_date, reservation_model):
        self.start_date = start_date
        self.reservation_model = reservation_model

        chrome_options = webdriver.ChromeOptions()

        # FIXME ローカル環境で実行するときは、ここの第2引数を書き換える必要がある
        CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "")
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

    def get_status_from_img_src(self, img_src):
        if img_src == self.ROOT_URL + self.EMPTYBS_GIF:
            return "VACANT"
        elif img_src == self.ROOT_URL + self.FINISHS_GIF:
            return "OCCUPIED"
        elif img_src == self.ROOT_URL + self.CLOSES_GIF:
            return "CLOSED"
        elif img_src == self.ROOT_URL + self.KEEPS_GIF:
            return "KEEP"
        elif img_src == self.ROOT_URL + self.KIKANGAIS_GIF:
            return "KIKANGAI"
        elif img_src == self.ROOT_URL + self.SOUND_GIF:
            return "SOUND"
        else:
            return "INVALID"

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
        self.exec_next_page_script(self.START_SETTING_DATE_SCRIPT)  # 年月日ボタン

        # 日付設定
        self.driver.execute_script(
            self.CHANGE_DATE_SCRIPT.format(
                year=self.start_date.year,
                month=self.start_date.month,
                day=self.start_date.day,
            ),
        )

        self.exec_next_page_script(self.FINISH_SETTING_DATE_SCRIPT,)  # 設定（年月日）ボタン
        self.exec_next_page_script(self.SEARCH_START_SCRIPT)  # 複合検索ボタン

    def scraping(self):
        # データ取得
        has_next = True
        while has_next:
            # dispというIDのテーブルが読み込まれるまでは待機
            try:
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.ID, "disp")),
                )
            except TimeoutException:
                print(f"failed to load table due to timeout.")
                break

            # 建物名・施設名取得
            title = self.driver.find_element_by_xpath(self.TITLE_XPATH)
            [building, institute] = title.text.replace("<br>", "").split("\n")

            # テーブルデータ取得
            table = self.driver.find_element_by_xpath(self.TABLE_XPATH)
            rows = self.to_rows(table)

            # データ保存
            self.reservation_model.append(building, institute, rows)

            # has_nextの更新
            # try:
            #     self.driver.find_element_by_xpath(self.NEXT_BUTTON_XPATH)
            # except NoSuchElementException:  # 次施設がクリックできない時
            has_next = False
            # except Exception as e:  # なんらかの理由でデータが取得できなかった時
            #     print("failed to update has_next.")
            #     raise e

            # 次の施設へ
            # self.exec_next_page_script(self.TO_NEXT_INSTITUTE_SCRIPT)
