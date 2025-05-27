from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime, timedelta

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 10)

def crawl_hynix_news_by_date(year, month, day):
    """특정 날짜의 하이닉스 뉴스를 크롤링하는 함수 - 2025년 업데이트 버전"""
    
    try:
        # 날짜 파라미터를 포함한 URL 직접 구성 
        date_str = f"{year:04d}.{month:02d}.{day:02d}"
        
        url = f"https://search.naver.com/search.naver?where=news&query=%ED%95%98%EC%9D%B4%EB%8B%89%EC%8A%A4&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={date_str}&de={date_str}&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so%3Ar%2Cp%3A1d&is_sug_officeid=0"
        
        driver.get(url)
        time.sleep(3)
        
        # 스크롤해서 모든 뉴스 로드
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        
        news_data = []
        
        news_containers = driver.find_elements(By.CSS_SELECTOR, ".kuu3XjzMNeL3gDPWyWNX")
        
        if not news_containers:
            print(f"{year}-{month:02d}-{day:02d}: 뉴스 컨테이너를 찾을 수 없음")
            return []
        
        print(f"찾은 뉴스 컨테이너: {len(news_containers)}개")
        
        for i, container in enumerate(news_containers):
            try:
                # 제목 추출
                try:
                    title_element = container.find_element(By.CSS_SELECTOR, ".sds-comps-text-type-headline1")
                    title = title_element.text.strip()
                except:
                    continue
                
                # 제목에 '하이닉스'가 포함된 경우만 처리
                if '하이닉스' not in title:
                    continue
                
                news_item = {
                    'title': title,
                    'date': f"{year}-{month:02d}-{day:02d}",
                    'preview': ''
                }
                
                # 날짜 추출 (실제 발행 시간)
                try:
                    date_elements = container.find_elements(By.CSS_SELECTOR, ".sds-comps-profile-info-subtext span")
                    for elem in date_elements:
                        text = elem.text.strip()
                        if "전" in text or ":" in text:
                            news_item['date'] = text
                            break
                except:
                    pass
                
                # 본문 미리보기 추출
                try:
                    preview_element = container.find_element(By.CSS_SELECTOR, ".sds-comps-text-type-body1")
                    news_item['preview'] = preview_element.text.strip()
                except:
                    pass
                
                news_data.append(news_item)
                print(f"하이닉스 뉴스 발견: {title}")
                
            except:
                continue
        
        return news_data
        
    except Exception as e:
        print(f"{year}-{month:02d}-{day:02d} 크롤링 실패: {e}")
        return []

# 메인 크롤링 실행
try:
    print("하이닉스 뉴스 날짜별 크롤링 시작...")
    
    all_news_data = []
    
    # 2024년 1월 1일부터 현재 날짜까지
    start_date = datetime(2024, 1, 1)
    end_date = datetime.now()
    
    current_date = start_date
    while current_date <= end_date:
        year = current_date.year
        month = current_date.month
        day = current_date.day
        
        print(f"{year}-{month:02d}-{day:02d} 크롤링 중...")
        
        daily_news = crawl_hynix_news_by_date(year, month, day)
        all_news_data.extend(daily_news)
        
        print(f"  -> {len(daily_news)}개 하이닉스 뉴스 수집")
        
        current_date += timedelta(days=1)
        time.sleep(2)  
    
    # 데이터프레임 생성
    if all_news_data:
        news_df = pd.DataFrame(all_news_data)
        # 중복 제거 (제목 기준)
        news_df = news_df.drop_duplicates(subset=['title'], keep='first')
        print(f"총 {len(news_df)}개 하이닉스 뉴스 수집 완료")
        print(news_df)
    else:
        print("수집된 하이닉스 뉴스가 없습니다.")
        news_df = pd.DataFrame()

except Exception as e:
    print(f"전체 오류: {e}")

finally:
    driver.quit()
