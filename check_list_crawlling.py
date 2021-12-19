import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import chromedriver_autoinstaller
import pandas as pd
import re
from sqlalchemy import create_engine
import numpy as np
import pymysql

#SQL 접속 및 공용변수 선언
engine = create_engine("")
engine.connect()
L_id = 0
A_id = 0
N_id = 0

#SELENIUM 사용을 위한 CHROMEDRIVER 다운로드 및 설정
def download_chromedriver():
    chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")
#TEMP 안에 CHROMEDRIVER있으면 사용 아니면 다운로드 후 사용
    try:
        driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', chrome_options=options)
        driver.set_window_position(0, 0)
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(10)
        return driver

    except:
        chromedriver_autoinstaller.install(True)
        driver = webdriver.Chrome(f'./{chrome_ver}/chromedriver.exe', chrome_options=options)
        driver.set_window_position(0, 0)
        driver.set_window_size(1920, 1080)
        driver.implicitly_wait(10)
        return driver

#유저의 아이디와 비밀번호를 설정
def set_user_id_and_password(input_user_id, input_user_pass):
    user_id = input_user_id
    user_pass = input_user_pass
    return user_id, user_pass

#학교 공지사항 크롤링
def crawling_announce_univ(page_num):
    global N_id
    driver = download_chromedriver()
    full_announce = list()
    u = "아주대"
    d = None
    c = None
    #카테고리 반복 탐색
    for i in range(1, 9):
        #페이지 반복 탐색
        for guide in range(0,page_num):
            part_announce = list()
            page = guide * 10
            url = "https://www.ajou.ac.kr/kr/ajou/notice.do?mode=list&&articleLimit=10&srCategoryId={0}&article.offset={1}".format(i, page)
            driver.get(url)
            element = driver.find_elements_by_xpath("//*[@id='cms-content']/div/div/div[3]/table/tbody/tr")
            #크롤링한 텍스트를 분해 및 저장
            for j in range(1, len(element)):
                list_1 = element[j].text.split("\n")
                category = list_1[0].split(" ")[-1]
                title = list_1[1]
                if'첨부파일' in list_1:
                    announce = str()
                    date = list_1[3].split(" ")[-1]
                    if len(list_1[3].split(" ")) > 2:
                        announce_len = list_1[3].split(" ")[0:-1]
                        for i in range(len(announce_len)):
                            announce += announce_len[i]
                    elif len(list_1[3].split(" ")) == 2:
                        announce = list_1[3].split(" ")[0]
                    N_id += 1
                    part_announce.append([date, title, announce, u, d, c, str(N_id), category])
                else:
                    announce = str()
                    if len(list_1[2].split(" ")) > 2:
                        announce_len = list_1[2].split(" ")[0:-1]
                        for i in range(len(announce_len)):
                            announce += announce_len[i]
                    elif len(list_1[2].split(" ")) == 2:
                        announce = list_1[2].split(" ")[0]
                    date = list_1[2].split(" ")[-1]
                    N_id += 1
                    part_announce.append([date, title, announce, u, d, c, str(N_id), category])
            full_announce.extend(part_announce)
            time.sleep(3)
    #크롤링 후 정리된 데이터 DATAFRAME에 저장
    full_announce_data = pd.DataFrame(full_announce, columns=["date","title", "announce", "U_name","D_name","Course_code","N_id","category"])
    #SQL에 데이터 전송
    full_announce_data.to_sql(name='notice', con= engine, if_exists="append", index= False)

#학과 공지사항 크롤링(미구현)
def crawling_announce_dept(category_list):
    driver = download_chromedriver()
    full_announce = list()
    u = None
    d = "정보통신대학"
    c = None
    for cate in category_list:
        part_announce = list()
        for guide in range(0, 5):
            page = guide * 10
            url = "http://it.ajou.ac.kr/it/community/community01.jsp?mode=list&search%3Asearch_category%3Acategory={0}&board_no=209&pager.offset={1}".format(cate, page)
            driver.get(url)
            element = driver.find_elements_by_xpath("//*[@id='jwxe_main_content']/div/div[3]/table/tbody/tr")
            for j in range(len(element)):
                if element[j].text == "등록된 글이 없습니다.":
                    break
                list_1 = element[j].text.split("\n")
                title = list_1[0]
                date = list_1[1].split(" ")[1]
                part_announce.append([date, title, u, d, c])
                time.sleep(10)
        print(part_announce)
        full_announce.append(part_announce)
    full_announce_data = pd.DataFrame(full_announce, columns=["날짜", "제목", 'u', 'd', 'c'])
    js_announce = full_announce_data.to_json(orient='columns')

#수업 공지 BB 크롤링
def crawling_bb(content_code_list):
    global A_id, N_id, L_id
    user_form = set_user_id_and_password("taehun9606", "rlaxogjs8856*")
    inner_text_lists = list()
    inner_text_splits = list()
    inner_homework_list = list()
    inner_video_list = list()

    for content_code in content_code_list:
        driver = download_chromedriver()
        url = "https://eclass2.ajou.ac.kr"

        driver.get(url)
        element = driver.find_element_by_id("userId")
        element.send_keys(user_form[0])
        element = driver.find_element_by_id("password")
        element.send_keys(user_form[1])
        element.send_keys(Keys.ENTER)

        try:
            alert_window = driver.switch_to.alert()
            alert_window.accept()
        except:
            pass
        driver.find_element_by_partial_link_text(content_code).click()
        driver.switch_to.frame("classic-learn-iframe")
        element = driver.find_element_by_xpath("//span[contains(text(), '공지사항')]")
        element.click()
        # 공지사항 크롤링
        inner_contents = driver.find_elements_by_css_selector("#announcementList > li")
        for inner_content in inner_contents:
            inner_text_lists.append(inner_content.text)
        for inner_text_list in inner_text_lists:
            inner_text_split = inner_text_list.split("\n", maxsplit=2)
            split = re.findall(r'\d+', inner_text_split[1])
            date = split[0] + "-" + split[1] + "-" + split[2]
            date_format = datetime.strptime(date, "%Y-%m-%d")
            '''
            date_diff = datetime.now() - date_format
            if date_diff.days > 7:
                continue
            '''
            N_id += 1
            inner_text_split[1] = date
            inner_text_split.append(None)
            inner_text_split.append(None)
            inner_text_split.append(content_code)
            inner_text_split.append(str(N_id))
            inner_text_split.append("professor")
            inner_text_split.append("수업")
            if len(inner_text_split[2]) > 200:
                inner_text_split[2] = inner_text_split[2][0:198]
            inner_text_splits.append(inner_text_split)
        element = driver.find_element_by_xpath("//span[contains(text(), '과제')]")
        element.click()

        #과제 크롤링
        inner_text_lists.clear()
        inner_homeworks = driver.find_elements_by_css_selector("#content_listContainer > li")
        for inner_content in inner_homeworks:
            inner_text_lists.append(inner_content.text)
            inner_content.click()
            try:
                element = inner_content.find_element_by_xpath("//*[@id='metadata']/div/div/div[1]/div[2]")
                due_date_text = element.text
                due_date = datetime.strptime(due_date_text, "%Y-%m-%d")
                print(due_date)
            except:
                pass
            print(element)
        for inner_text_list in inner_text_lists:
            inner_text_split = inner_text_list.split("\n", maxsplit=1)
            if len(inner_text_split[1]) > 200:
                inner_text_split[1] = inner_text_split[1][0:198]
            if len(inner_text_split[0]) > 45:
                inner_text_split[0] = inner_text_split[0][0:43]

            A_id += 1
            inner_text_split.append(str(A_id))
            inner_text_split.append(content_code)
            inner_homework_list.append(inner_text_split)


        element = driver.find_element_by_xpath("//span[contains(text(), '강의노트')]")
        element.click()

        # 강의 노트 크롤링
        inner_text_lists.clear()
        inner_videos = driver.find_elements_by_xpath("//*[@id='content_listContainer']/li")
        for inner_video in inner_videos:
            inner_text_lists.append(inner_video.text)

        for inner_text_list in inner_text_lists:
            inner_text_split = inner_text_list.split("\n", maxsplit=1)
            if len(inner_text_split) != 2:
                inner_text_split.append("none")
            if len(inner_text_split[0]) > 45:
                inner_text_split[0] = inner_text_split[0][0:43]
            if len(inner_text_split[1]) > 200:
                inner_text_split[1] = inner_text_split[1][0:198]

            L_id += 1
            inner_text_split.append(str(L_id))
            inner_text_split.append(content_code)
            inner_video_list.append(inner_text_split)

        inner_text_lists.clear()
        time.sleep(20)
        driver.quit()
    # 각 데이터 DATAFRAME에 저장
    dataframe_announcement = pd.DataFrame(inner_text_splits, columns=["title", "date", "content", "U_name", "D_name", "Course_code","N_id","announce","category"])
    dataframe_homework = pd.DataFrame(inner_homework_list, columns=["A_id", "title", "content","Course_code"])
    dataframe_video = pd.DataFrame(inner_video_list, columns=["title", "content","L_id","Course_code"])
    #데이터베이스 전송
    dataframe_video.to_sql(name='lecture_note', con=engine, if_exists="append", index=False)
    dataframe_homework.to_sql(name='assignment', con=engine, if_exists="append", index=False)
    dataframe_announcement.to_sql(name='notice', con=engine, if_exists="append", index=False)


if __name__ == "__main__":
    start = datetime.now()
    content_code_set = ["F004", "F003", "F055", "F063", "F070", "F113"]

    crawling_bb(content_code_set)
    crawling_announce_univ(8)

    end = datetime.now()
    ET = end - start
    print(ET.seconds)
