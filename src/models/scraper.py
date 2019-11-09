# coding: utf-8
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import chromedriver_binary
import re

class ScraperModel():
    """
    base scraper model
    """
    def __init__(self, root_url):
        self.root_url = root_url
        PATH = "/mnt/d/MSAT/chromedriver/chromedriver.exe"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path=PATH)

class KoutouScraperModel(ScraperModel):
    """
    scraper for koutou-ku
    """
    ROOT_URL = 'https://sisetun.kcf.or.jp/web/'

    SEARCH_VACANT_SCRIPT = "doAction(((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantAction : document.formWTransInstSrchVacantAction ), gRsvWTransInstSrchVacantAction)"
    SEARCH_MULTIPLE_SCRIPT = "doAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction)"
    START_SETTING_DATE_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchSetDayAction);"
    CHANGE_DATE_SCRIPT = "changeDayGif((_dom == 3) ? document.layers['disp'].document.CalendarDays{day} : document.CalendarDays{day}, {year}, {month}, {day})"
    FINISH_SETTING_DATE_SCRIPT = "sendSelectDay((_dom == 3) ? document.layers['disp'].document.formCommonSrchDayWeekAction : document.formCommonSrchDayWeekAction, gRsvWTransInstSrchMultipleAction, 1)"
    SEARCH_START_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWGetInstSrchInfAction)"
    TO_NEXT_INSTITUTE_SCRIPT = "doTransInstSrchVacantTzoneAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantTzoneAction : document.formWTransInstSrchVacantTzoneAction, gRsvWTransInstSrchVacantAction, 6, gSrchSelectInstNo, gSrchSelectInstMax)"
    
    EMPTYBS_GIF = 'image/lw_emptybs.gif'
    FINISHS_GIF = 'image/lw_finishs.gif'
    CLOSES_GIF = 'image/lw_closes.gif'
    KEEPS_GIF = 'image/lw_keeps.gif'
    KIKANGAIS_GIF = 'image/lw_kikangais.gif'
    SOUND_GIF = 'image/lw_sound.gif'

    TITLE_XPATH = '//*[@id="disp"]/center/table[3]/tbody[2]/tr[2]/td[2]/a/font/b'
    TABLE_XPATH = '//*[@id="disp"]/center/table[3]/tbody[2]/tr[3]/td[2]/center/table/tbody'
    NEXT_BUTTON_XPATH = '//*[@id="disp"]/center/table[3]/tbody[1]/tr/td/table/tbody/tr/td[3]/a'

    def __init__(self, start_date, reservation_model):
        super().__init__(self.ROOT_URL)
        self.start_date = start_date
        self.reservation_model = reservation_model

    def get_status_from_img_src(self, img_src):
        if img_src == self.root_url + self.EMPTYBS_GIF:
            return 'VACANT'
        elif img_src == self.root_url + self.FINISHS_GIF:
            return 'OCCUPIED'
        elif img_src == self.root_url + self.CLOSES_GIF:
            return 'CLOSED'
        elif img_src == self.root_url + self.KEEPS_GIF:
            return 'KEEP'
        elif img_src == self.root_url + self.KIKANGAIS_GIF:
            return 'KIKANGAI'
        elif img_src == self.root_url + self.SOUND_GIF:
            return 'SOUND'
        else:
            return 'INVALID'
    
    def exec_next_page_script(self, script):
        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located)
            time.sleep(5)
            self.driver.execute_script(script)
        except TimeoutException as e:
            print(f'failed to execute script due to timeout. script={script}')
            raise e
        except Exception as e:
            print(f'failed to execute script: {script}')
            raise e

    def to_rows(self, table):
        res = []
        for index, row in enumerate(table.find_elements_by_css_selector('tr')):
            if index == 0:
                res.append([d.text.replace('\t', '') for d in row.find_elements_by_css_selector('td')])
            else:
                arr = []
                for i, item in enumerate(row.find_elements_by_tag_name('td')):
                    if i == 0:
                        arr.append(item.text.replace('\t', ''))
                    else:
                        img = item.find_elements_by_css_selector('img')[0]
                        arr.append(self.get_status_from_img_src(img.get_attribute('src')))
                res.append(arr)
        return res

    def prepare_for_scraping(self):
        self.driver.get(self.root_url)
        self.exec_next_page_script(self.SEARCH_VACANT_SCRIPT) # 施設の空き状況ボタン
        self.exec_next_page_script(self.SEARCH_MULTIPLE_SCRIPT) # 複合検索ボタン
        self.exec_next_page_script(self.START_SETTING_DATE_SCRIPT) # 年月日ボタン

        # 日付設定
        self.driver.execute_script(
            self.CHANGE_DATE_SCRIPT.format(
                year=self.start_date.year,month=self.start_date.month, day=self.start_date.day
            )
        )

        self.exec_next_page_script(self.FINISH_SETTING_DATE_SCRIPT) # 設定（年月日）ボタン
        self.exec_next_page_script(self.SEARCH_START_SCRIPT) # 複合検索ボタン
    
    def scraping(self):
        # データ取得
        has_next = True
        while has_next:
            # dispというIDのテーブルが読み込まれるまでは待機
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 'disp')))

            # 建物名・施設名取得
            title = self.driver.find_element_by_xpath(self.TITLE_XPATH)
            [building, institute] = title.text.replace('<br>', '').split('\n')

            # テーブルデータ取得
            table = self.driver.find_element_by_xpath(self.TABLE_XPATH)
            rows = self.to_rows(table)

            # データ保存
            self.reservation_model.append(building, institute, rows)

            # has_nextの更新
            try:
                self.driver.find_element_by_xpath(self.NEXT_BUTTON_XPATH)
            except NoSuchElementException: # 次施設がクリックできない時
                has_next = False
            except Exception as e: # なんらかの理由でデータが取得できなかった時
                print('failed to update has_next.')
                raise e
            self.exec_next_page_script(self.TO_NEXT_INSTITUTE_SCRIPT)
        
    def clear(self):
        self.driver.quit()




class EdogawaScraperModel(ScraperModel):
    """
    scraper for edogawa-ku
    written by 藪智明 2019-11-09
    """
    ROOT_URL = 'https://www.edogawa-yoyaku.jp/edo-user/'

    SEARCH_VACANT_SCRIPT = "return fcSubmit(FRM_RSGK001,'INIT','rsv.bean.RSGK301BusinessInit','RSGK301');"
    TO_NEXT_PAGE_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK301, 'NEXT', 'rsv.bean.RSGK301BusinessMovePage', 'RSGK301', false, '');"
    SEARCH_INSTRUMENTAL_LOUD_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK301, 'LINK_CLICK', 'rsv.bean.RSGK303BusinessInit', 'RSGK301', false, '0038');"
    SELECT_FIRST_INSTITUTE_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK303, 'LINK_CLICK', 'rsv.bean.RSGK304BusinessInit', 'RSGK303', false, '140');"
    SELECT_ALL_ROOM_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK304, 'LINK_CLICK', 'rsv.bean.RSGK305BusinessInit', 'RSGK304', false, '');"
    CHANGE_DATE_SCRIPT = "return fcSubmit_Yoyaku( FRM_RSGK305, 'SEARCH_POINT_RSGK306', 'rsv.bean.RSGK306BusinessInit', 'RSGK305', false, '{}');"
    SHOW_WEEK_VIEW_SCRIPT = "return fcSubmit(FRM_RSGK306,'AKIJOUKYOU_WEEK','rsv.bean.RSGK307BusinessFromRSGK306','RSGK306');"
    TO_NEXT_INSTITUTE_SCRIPT = "return fcSubmit(FRM_RSGK307,'SEARCH_NEXT1S','rsv.bean.RSGK307BusinessMoveShisetsu','RSGK307');"

    TITLE_XPATH = '//*[@id="{}"]/span' # 施設によってIDが違うので正規表現で指定
    DATE_XPATH = '//*[@id="FRM_RSGK307"]/div[3]/div/div/table[1]/tbody/tr[1]/td[2]/strong'
    DAYS_XPATH = '//*[@id="tbl_time3"]/tbody'
    TABLE_XPATH = '//*[@id="tbl_time2"]/tbody'
    NEXT_BUTTON_XPATH = '//*[@id="disp"]/center/table[3]/tbody[1]/tr/td/table/tbody/tr/td[3]/a'

    def __init__(self, start_date, reservation_model):
        super().__init__(self.ROOT_URL)
        self.start_date = start_date
        self.reservation_model = reservation_model
    
    def exec_next_page_script(self, script):
        try:
            WebDriverWait(self.driver, 30).until(EC.presence_of_all_elements_located)
            time.sleep(5)
            self.driver.execute_script(script)
        except TimeoutException as e:
            print(f'failed to execute script due to timeout. script={script}')
            raise e
        except Exception as e:
            print(f'failed to execute script: {script}')
            raise e

    def to_rows(self, table):
        res = []
        inst_and_arr = [] # [時間帯＆予約状況]の配列
        building_inst = [] # [building, institution]
        pattern1 = re.compile("\d{4}-\d{4}") # 正規表現チェック用1 (例: 0900-0930)
        pattern2 = re.compile("\d{2,4}人|-") # 正規表現チェック用2 (例: 130人)
        
        for index, row in enumerate(table.find_elements_by_css_selector('tr')):
            arr = [] # 1行ずつ読み込む用の配列
            for i, item in enumerate(row.find_elements_by_tag_name('td')):
                if i == 0 and not pattern1.fullmatch(item.text): # 施設名と部屋名が来た場合

                    if len(building_inst) == 2: #2回目以降なら
                        #前回のループで得た [building, institution] を [時間帯＆予約状況]の配列の先頭に追加
                        inst_and_arr.insert(0,building_inst)
                        res.append(inst_and_arr)
                        inst_and_arr = [] # [時間帯＆予約状況]の配列を初期化
                    
                    # 以下, 今回のループの処理
                    building_inst = item.text.split("\n") # [building, institution]
                elif i == 1 and pattern2.match(item.text): # 人数が場合は無視
                    continue
                elif item.text == "": # 何もない場合はとりあえず"VACANT"を入れている
                    arr.append(item.text.replace("","VACANT"))
                else:
                    arr.append(item.text)
            inst_and_arr.append(arr) # [時間帯＆予約状況]の配列に1行ずつ追加
        inst_and_arr.insert(0,building_inst) # [building, institution] を先頭に追加
        res.append(inst_and_arr)
        return res


    def prepare_for_scraping(self):
        self.driver.get(self.root_url)
        self.exec_next_page_script(self.SEARCH_VACANT_SCRIPT) # 空状況照会・予約（利用目的から選択）ボタン
        self.exec_next_page_script(self.TO_NEXT_PAGE_SCRIPT) # 次のページボタン
        self.exec_next_page_script(self.SEARCH_INSTRUMENTAL_LOUD_SCRIPT) # 器楽（音量大）ボタン
        self.exec_next_page_script(self.SELECT_FIRST_INSTITUTE_SCRIPT) # 松江区民プラザ（最初の施設）のボタン
        self.exec_next_page_script(self.SELECT_ALL_ROOM_SCRIPT) # 利用可能な室場分類全てボタン

        # 日付設定
        self.exec_next_page_script(
            self.CHANGE_DATE_SCRIPT.format(self.start_date.day) # 本日の日付を入力する　＜＜＜本日の日付がdisabledだったらどうするかは後で＞＞＞
        )

        self.exec_next_page_script(self.SHOW_WEEK_VIEW_SCRIPT) # 週別表示ボタン
    
    def scraping(self):
        NUMBER_OF_PAGES = 17

        # データ取得 ページ数は17
        for i in range(NUMBER_OF_PAGES):
            # scInlineというIDのテーブルが読み込まれるまでは待機
            WebDriverWait(self.driver, 30).until(EC.presence_of_element_located((By.ID, 'scInline')))

            # IDを検索
            institute_id = re.findall("RSGK307_\d{4}", self.driver.page_source)

            for j in institute_id:
                rows = []
                # 建物名・施設名はテーブルデータに含まれる          

                # 日付・曜日取得 ＜＜＜月をまたぐ場合の処理はまだ＞＞＞
                start_date = self.driver.find_element_by_xpath(self.DATE_XPATH.format())
                days = self.driver.find_element_by_xpath(self.DAYS_XPATH)

                [damp, temp_day_of_the_week, temp_date] = re.split("時間|\n", days.text)
                day_of_the_week = temp_day_of_the_week.split()
                date = temp_date.split()
                res = [start_date.text, date, day_of_the_week]

                # テーブルデータ取得
                table = self.driver.find_element_by_xpath(self.TABLE_XPATH)
                rows = self.to_rows(table)
                rows.insert(0,res) # 先頭に日付等のデータを挿入

            # データ保存
            self.reservation_model.append(rows)

            # 次の施設へ
            self.exec_next_page_script(self.TO_NEXT_INSTITUTE_SCRIPT)

 
    def clear(self):
        self.driver.quit()