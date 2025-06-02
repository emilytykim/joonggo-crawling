# crawler.py

import os
import time
import csv
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Pool, cpu_count
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm


# ✅ 로그인된 크롬 세션으로 실행
def open_logged_in_driver():
    options = Options()
    options.add_argument(
        "user-data-dir=/Users/emily/Library/Application Support/Google/Chrome"
    )
    options.add_argument("profile-directory=Profile 2")
    driver = webdriver.Chrome(options=options)
    return driver


# ✅ 게시글 목록 수집 (제목, URL, 날짜, 닉네임)
def get_post_links(driver, category_url, max_pages=5):
    driver.get(category_url)
    time.sleep(2)
    driver.switch_to.frame("cafe_main")

    all_posts = []

    for page in range(1, max_pages + 1):
        print(f"📄 Page {page}")
        time.sleep(1)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tr[align=center]")

        for row in rows:
            try:
                title_elem = row.select_one("a.article")
                date_elem = row.select_one("td.td_date")
                nick_elem = row.select_one("td.p-nick a.m-tcol-c")

                if not title_elem:
                    continue

                all_posts.append(
                    {
                        "title": title_elem.text.strip(),
                        "url": "https://cafe.naver.com" + title_elem.get("href"),
                        "date": date_elem.text.strip() if date_elem else "",
                        "nickname": nick_elem.text.strip() if nick_elem else "",
                    }
                )
            except:
                continue

        # 페이지 숫자 버튼 클릭
        try:
            next_btn = driver.find_element(
                By.XPATH,
                f"//button[@class='btn number' and text()='{(page % 10) or 10}']",
            )
            next_btn.click()
        except:
            print("⛔️ 더 이상 페이지 없음")
            break

        # 10페이지 단위 화살표 클릭
        if page % 10 == 0:
            try:
                arrow_btn = driver.find_element(
                    By.CSS_SELECTOR, ".Pagination .btn.type_next"
                )
                arrow_btn.click()
            except:
                break

    return all_posts


# ✅ 상세 페이지 수집 (병렬)
def get_post_details(post):
    try:
        options = Options()
        options.add_argument(
            "user-data-dir=/Users/emily/Library/Application Support/Google/Chrome"
        )
        options.add_argument("profile-directory=Profile 2")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)

        driver.get(post["url"])
        time.sleep(1)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        price_elem = soup.select_one("strong.cost")
        post["price"] = price_elem.text.strip() if price_elem else "N/A"

        status_elem = soup.select_one("em.SaleLabel")
        post["status"] = status_elem.text.strip() if status_elem else "판매중"

        driver.quit()
    except Exception as e:
        print(f"❌ 상세페이지 오류: {post['url']}, {e}")
        post["price"] = "N/A"
        post["status"] = "N/A"

    return post


# ✅ 전체 카테고리 실행
def crawl_category(category_name, category_url, output_csv, max_pages=5):
    print(f"🚀 Start: {category_name}")
    driver = open_logged_in_driver()
    try:
        posts = get_post_links(driver, category_url, max_pages)
    finally:
        driver.quit()

    print(f"🔁 상세페이지 병렬 파싱 중... (총 {len(posts)}개)")
    with Pool(processes=cpu_count()) as pool:
        detailed_posts = pool.map(get_post_details, posts)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["title", "url", "date", "nickname", "price", "status"]
        )
        writer.writeheader()
        writer.writerows(detailed_posts)

    print(f"✅ 저장 완료: {output_csv} ({len(detailed_posts)} rows)")


class JoonggoCrawler:
    def __init__(self, headless=False):
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        """Chrome WebDriver 설정"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        
        # 기본 옵션 설정
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-popup-blocking')
        
        # 임시 프로필 디렉토리 사용
        import tempfile
        import os
        temp_dir = os.path.join(tempfile.gettempdir(), 'chrome_profile')
        os.makedirs(temp_dir, exist_ok=True)
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')
        
        # 추가 설정
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def switch_to_iframe(self):
        """iframe으로 전환"""
        try:
            iframe = self.wait.until(
                EC.presence_of_element_located((By.ID, "cafe_main"))
            )
            self.driver.switch_to.frame(iframe)
            return True
        except Exception as e:
            print(f"iframe 전환 실패: {e}")
            return False
            
    def get_post_urls(self, category_url, max_pages=1):
        """게시글 URL 수집"""
        self.driver.get(category_url)
        time.sleep(2)  # 페이지 로딩 대기
        
        if not self.switch_to_iframe():
            return []
            
        post_urls = []
        for page in range(1, max_pages + 1):
            try:
                # 게시글 목록에서 URL 추출 (공지사항 제외)
                articles = self.wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr:not(.board-notice) a.article"))
                )
                
                for article in articles:
                    url = article.get_attribute('href')
                    if url:
                        post_urls.append(url)
                        
                # 다음 페이지로 이동
                if page < max_pages:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.pgR")
                    next_btn.click()
                    time.sleep(1)
                    
            except Exception as e:
                print(f"페이지 {page} 처리 중 오류: {e}")
                break
                
        return post_urls
        
    def extract_post_data(self, url):
        """게시글 상세 정보 추출"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            if not self.switch_to_iframe():
                return None
                
            # 제목 추출
            title = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3.title_text"))
            ).text
            
            # 가격 추출
            try:
                price = self.driver.find_element(By.CSS_SELECTOR, "div.ProductPrice strong.cost").text
            except:
                price = "가격 정보 없음"
                
            # 판매 상태 추출
            try:
                status = self.driver.find_element(By.CSS_SELECTOR, "em.SaleLabel").text
            except:
                status = "판매중"
                
            # 닉네임 추출
            try:
                nickname = self.driver.find_element(By.CSS_SELECTOR, "div.nick_box button.nickname").text
            except:
                nickname = "닉네임 없음"
                
            # 날짜 추출
            try:
                date = self.driver.find_element(By.CSS_SELECTOR, "div.article_info span.date").text
            except:
                date = "날짜 정보 없음"
                
            # 카테고리 추출 (URL에서 추출)
            category = "여성패션"  # 기본값
            
            return {
                'category': category,
                'title': title,
                'price': price,
                'status': status,
                'date': date,
                'nickname': nickname,
                'url': url
            }
            
        except Exception as e:
            print(f"게시글 데이터 추출 실패 ({url}): {e}")
            return None
            
    def crawl_category(self, category_url, max_pages=1):
        """카테고리 크롤링 실행"""
        print(f"카테고리 크롤링 시작: {category_url}")
        
        # 게시글 URL 수집
        post_urls = self.get_post_urls(category_url, max_pages)
        print(f"수집된 게시글 URL 수: {len(post_urls)}")
        
        # 게시글 데이터 수집
        posts_data = []
        for url in tqdm(post_urls, desc="게시글 데이터 수집 중"):
            post_data = self.extract_post_data(url)
            if post_data:
                posts_data.append(post_data)
                
        # DataFrame 생성 및 CSV 저장
        if posts_data:
            df = pd.DataFrame(posts_data)
            output_file = f"joonggo_data_{int(time.time())}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"데이터 저장 완료: {output_file}")
            
        return posts_data
        
    def close(self):
        """WebDriver 종료"""
        self.driver.quit()
