# coding: utf-8
import datetime
import sys
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT_URL = 'https://sisetun.kcf.or.jp/web/'
SEARCH_VACANT_SCRIPT = "doAction(((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantAction : document.formWTransInstSrchVacantAction ), gRsvWTransInstSrchVacantAction)"
SEARCH_MULTIPLE_SCRIPT = "doAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchMultipleAction)"
START_SETTING_DATE_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWTransInstSrchSetDayAction);"
CHANGE_DATE_SCRIPT = "changeDayGif((_dom == 3) ? document.layers['disp'].document.CalendarDays{day} : document.CalendarDays{day}, {year}, {month}, {day})"
FINISH_SETTING_DATE_SCRIPT = "sendSelectDay((_dom == 3) ? document.layers['disp'].document.formCommonSrchDayWeekAction : document.formCommonSrchDayWeekAction, gRsvWTransInstSrchMultipleAction, 1)"
SEARCH_START_SCRIPT = "sendSelectWeekNum((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchMultipleAction : document.formWTransInstSrchMultipleAction, gRsvWGetInstSrchInfAction)"
TO_NEXT_INSTITUTE_SCRIPT = "doTransInstSrchVacantTzoneAction((_dom == 3) ? document.layers['disp'].document.formWTransInstSrchVacantTzoneAction : document.formWTransInstSrchVacantTzoneAction, gRsvWTransInstSrchVacantAction, 6, gSrchSelectInstNo, gSrchSelectInstMax)"

EMPTYBS_GIF = ROOT_URL + "image/lw_emptybs.gif"
FINISHS_GIF = ROOT_URL + "image/lw_finishs.gif"
CLOSES_GIF = ROOT_URL + "image/lw_closes.gif"
KEEPS_GIF = ROOT_URL + "image/lw_keeps.gif"
KIKANGAIS_GIF = ROOT_URL + "image/lw_kikangais.gif"
SOUND_GIF = ROOT_URL + "image/lw_sound.gif"

def get_status_from_img_src(img_src):
    if img_src == EMPTYBS_GIF:
        return 'vacant'
    elif img_src == FINISHS_GIF:
        return 'occupied'
    elif img_src == CLOSES_GIF:
        return 'closed'
    elif img_src == KEEPS_GIF:
        return 'keep'
    elif img_src == KIKANGAIS_GIF:
        return 'kikangai'
    elif img_src == SOUND_GIF:
        return 'sound'
    else:
        return 'undefined'

def toRows(table):
    res = []
    for index, row in enumerate(table.find_elements_by_css_selector('tr')):
        if index == 0: # Header
            res.append([d.text.replace('\t', '') for d in row.find_elements_by_css_selector('td')])
        else: # Body
            arr = []
            for i, item in enumerate(row.find_elements_by_tag_name('td')):
                if i == 0:
                    arr.append(item.text.replace('\t', ''))
                else:
                    img = item.find_elements_by_css_selector('img')[0]
                    arr.append(get_status_from_img_src(img.get_attribute('src')))
            res.append(arr)
    return res

def exec_next_page_script(driver, script):
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located)
        time.sleep(5)
        driver.execute_script(script)
    except TimeoutException as e:
        print(f'failed to execute script due to timeout. script={script}')
        raise e
    except Exception as e:
        print(f'failed to execute script:{script}')
        raise e

def main(date):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    start = time.time()
    driver.get(ROOT_URL)

    exec_next_page_script(driver, SEARCH_VACANT_SCRIPT) # 施設の空き状況ボタン
    exec_next_page_script(driver, SEARCH_MULTIPLE_SCRIPT) # 複合検索ボタン
    exec_next_page_script(driver, START_SETTING_DATE_SCRIPT) # 年月日ボタン

    # 日付設定
    time.sleep(5)
    driver.execute_script(CHANGE_DATE_SCRIPT.format(year=date.year, month=date.month, day=date.day))

    exec_next_page_script(driver, FINISH_SETTING_DATE_SCRIPT) # 設定（年月日）ボタン
    exec_next_page_script(driver, SEARCH_START_SCRIPT) # 複合検索ボタン

    # データ取得
    hasNext = True
    while hasNext:
        try:
            # dispというIDのテーブルが読み込まれるまでは待機
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'disp')))

            # 施設名取得
            title = driver.find_element_by_xpath('//*[@id="disp"]/center/table[3]/tbody[2]/tr[2]/td[2]/a/font/b')
            print(title.text.replace('<br>', '').replace('\n', ' '))

            # テーブルデータ取得
            table = driver.find_element_by_xpath('//*[@id="disp"]/center/table[3]/tbody[2]/tr[3]/td[2]/center/table/tbody')
            rows = toRows(table)

            # 出力（仮）
            # TODO (trfv)
            for row in rows:
                print(row)
        except TimeoutException as e:
            print('failed to scraping table due to timeout.')
            print(e)
        except:
            print('failed to scraping table.')

        # hasNextの更新
        try:
            driver.find_element_by_xpath('//*[@id="disp"]/center/table[3]/tbody[1]/tr/td/table/tbody/tr/td[3]/a')
        except NoSuchElementException: # 次施設がクリックできない時
            hasNext = False
        except Exception as e: # なんらかの理由でデータが取得できなかった時
            print('failed to update hasNext.')
            print(e)
        exec_next_page_script(driver, TO_NEXT_INSTITUTE_SCRIPT)

    end = time.time()
    print(f'経過時間: {end - start} 秒')
    driver.quit()

if __name__ == '__main__':
    date = datetime.date(int(sys.argv[1]) , int(sys.argv[2]), int(sys.argv[3]))
    main(date)