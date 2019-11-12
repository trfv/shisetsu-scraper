# coding: utf-8
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.common.models.scraper import ScraperModel


class EdogawaScraperModel(ScraperModel):
    """
    scraper for edogawa-ku
    written by 藪智明 2019-11-09
    """

    ROOT_URL = "https://www.edogawa-yoyaku.jp/edo-user/"

    SEARCH_VACANT_SCRIPT = (
        "return fcSubmit(FRM_RSGK001,'INIT','rsv.bean.RSGK301BusinessInit','RSGK301');"
    )
    TO_NEXT_PAGE_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK301, 'NEXT', 'rsv.bean.RSGK301BusinessMovePage', 'RSGK301', false, '');"
    SEARCH_INSTRUMENTAL_LOUD_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK301, 'LINK_CLICK', 'rsv.bean.RSGK303BusinessInit', 'RSGK301', false, '0038');"
    SELECT_FIRST_INSTITUTE_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK303, 'LINK_CLICK', 'rsv.bean.RSGK304BusinessInit', 'RSGK303', false, '140');"
    SELECT_ALL_ROOM_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK304, 'LINK_CLICK', 'rsv.bean.RSGK305BusinessInit', 'RSGK304', false, '');"
    CHANGE_DATE_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK305, 'SEARCH_POINT_RSGK306', 'rsv.bean.RSGK306BusinessInit', 'RSGK305', false, '{}');"
    SHOW_WEEK_VIEW_SCRIPT = "return fcSubmit(FRM_RSGK306,'AKIJOUKYOU_WEEK','rsv.bean.RSGK307BusinessFromRSGK306','RSGK306');"
    TO_NEXT_INSTITUTE_SCRIPT = "return fcSubmit(FRM_RSGK307,'SEARCH_NEXT1S','rsv.bean.RSGK307BusinessMoveShisetsu','RSGK307');"

    TITLE_XPATH = '//*[@id="{}"]/span'  # 施設によってIDが違うので正規表現で指定
    DATE_XPATH = (
        '//*[@id="FRM_RSGK307"]/div[3]/div/div/table[1]/tbody/tr[1]/td[2]/strong'
    )
    DAYS_XPATH = '//*[@id="tbl_time3"]/tbody'
    TABLE_XPATH = '//*[@id="tbl_time2"]/tbody'
    NEXT_BUTTON_XPATH = (
        '//*[@id="disp"]/center/table[3]/tbody[1]/tr/td/table/tbody/tr/td[3]/a'
    )

    def __init__(self, start_date, reservation_model):
        super().__init__(self.ROOT_URL)
        self.start_date = start_date
        self.reservation_model = reservation_model

    def to_rows(self, table):
        res = []
        inst_and_arr = []  # [時間帯＆予約状況]の配列
        building_inst = []  # [building, institution]
        pattern1 = re.compile(r"\d{4}-\d{4}")  # 正規表現チェック用1 (例: 0900-0930)
        pattern2 = re.compile(r"\d{2,4}人|-")  # 正規表現チェック用2 (例: 130人)

        for row in table.find_elements_by_css_selector("tr"):
            arr = []  # 1行ずつ読み込む用の配列
            for i, item in enumerate(row.find_elements_by_tag_name("td")):
                if i == 0 and not pattern1.fullmatch(item.text,):  # 施設名と部屋名が来た場合

                    if len(building_inst) == 2:  # 2回目以降なら
                        # 前回のループで得た [building, institution] を [時間帯＆予約状況]の配列の先頭に追加
                        inst_and_arr.insert(0, building_inst)
                        res.append(inst_and_arr)
                        inst_and_arr = []  # [時間帯＆予約状況]の配列を初期化

                    # 以下, 今回のループの処理
                    building_inst = item.text.split("\n",)  # [building, institution]
                elif i == 1 and pattern2.match(item.text):  # 人数が場合は無視
                    continue
                elif item.text == "":  # 何もない場合はとりあえず'VACANT'を入れている
                    arr.append(item.text.replace("", "VACANT"))
                else:
                    arr.append(item.text)
            inst_and_arr.append(arr)  # [時間帯＆予約状況]の配列に1行ずつ追加
        inst_and_arr.insert(0, building_inst)  # [building, institution] を先頭に追加
        res.append(inst_and_arr)
        return res

    def prepare_for_scraping(self):
        self.driver.get(self.root_url)
        self.exec_next_page_script(self.SEARCH_VACANT_SCRIPT,)  # 空状況照会・予約（利用目的から選択）ボタン
        self.exec_next_page_script(self.TO_NEXT_PAGE_SCRIPT)  # 次のページボタン
        self.exec_next_page_script(self.SEARCH_INSTRUMENTAL_LOUD_SCRIPT,)  # 器楽（音量大）ボタン
        self.exec_next_page_script(
            self.SELECT_FIRST_INSTITUTE_SCRIPT,
        )  # 松江区民プラザ（最初の施設）のボタン
        self.exec_next_page_script(self.SELECT_ALL_ROOM_SCRIPT,)  # 利用可能な室場分類全てボタン

        # 日付設定
        self.exec_next_page_script(
            self.CHANGE_DATE_SCRIPT.format(
                self.start_date.day,
            ),  # 本日の日付を入力する　＜＜＜本日の日付がdisabledだったらどうするかは後で＞＞＞
        )

        self.exec_next_page_script(self.SHOW_WEEK_VIEW_SCRIPT)  # 週別表示ボタン

    def scraping(self):
        NUMBER_OF_PAGES = 17

        # データ取得 ページ数は17
        for _ in range(NUMBER_OF_PAGES):
            # scInlineというIDのテーブルが読み込まれるまでは待機
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "scInline")),
            )

            # IDを検索
            institute_id = re.findall(r"RSGK307_\d{4}", self.driver.page_source,)

            for _ in institute_id:
                rows = []
                # 建物名・施設名はテーブルデータに含まれる

                # 日付・曜日取得 ＜＜＜月をまたぐ場合の処理はまだ＞＞＞
                start_date = self.driver.find_element_by_xpath(
                    self.DATE_XPATH.format(),
                )
                days = self.driver.find_element_by_xpath(self.DAYS_XPATH)

                [_, temp_day_of_the_week, temp_date] = re.split("時間|\n", days.text,)
                day_of_the_week = temp_day_of_the_week.split()
                date = temp_date.split()
                res = [start_date.text, date, day_of_the_week]

                # テーブルデータ取得
                table = self.driver.find_element_by_xpath(self.TABLE_XPATH)
                rows = self.to_rows(table)
                rows.insert(0, res)  # 先頭に日付等のデータを挿入

            # データ保存
            self.reservation_model.append(rows)

            # 次の施設へ
            self.exec_next_page_script(self.TO_NEXT_INSTITUTE_SCRIPT)
