import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from tqdm import tqdm
import tempfile
import os
import logging
from datetime import datetime

class JoonggoCrawler:
    def __init__(self, headless=False):
        self.setup_logger()
        self.setup_driver(headless)
        
    def setup_logger(self):
        # 로거 설정
        self.logger = logging.getLogger('JoonggoCrawler')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정
        log_filename = f'crawler_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # 콘솔 핸들러 설정
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # 포맷터 설정
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def setup_driver(self, headless):
        start_time = time.time()
        self.logger.info("WebDriver 설정 시작")
        
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-popup-blocking')
        
        # 임시 프로필 디렉토리 사용
        temp_dir = os.path.join(tempfile.gettempdir(), 'chrome_profile')
        os.makedirs(temp_dir, exist_ok=True)
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.logger.info(f"WebDriver 설정 완료 (소요시간: {time.time() - start_time:.2f}초)")

    def switch_to_iframe(self):
        start_time = time.time()
        try:
            iframe = self.wait.until(
                EC.presence_of_element_located((By.ID, "cafe_main"))
            )
            self.driver.switch_to.frame(iframe)
            self.logger.info(f"iframe 전환 성공 (소요시간: {time.time() - start_time:.2f}초)")
            return True
        except Exception as e:
            self.logger.error(f"iframe 전환 실패: {e} (소요시간: {time.time() - start_time:.2f}초)")
            return False

    def get_post_urls(self, category_url, max_pages=1, last_url=None):
        start_time = time.time()
        self.logger.info(f"URL 수집 시작 (최대 {max_pages}페이지)")
        
        self.driver.get(category_url)
        time.sleep(2)
        if not self.switch_to_iframe():
            return []
            
        post_urls = []
        found_last_url = False if last_url else True
        
        for page in range(1, max_pages + 1):
            page_start_time = time.time()
            try:
                self.logger.info(f"페이지 {page} 처리 시작")
                
                # 페이지 로딩 대기
                self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "tr:not(.board-notice) a.article"))
                )
                time.sleep(2)
                
                # 공지 제외
                articles = self.driver.find_elements(By.CSS_SELECTOR, "tr:not(.board-notice) a.article")
                self.logger.info(f"페이지 {page} 게시글 수: {len(articles)}")
                
                for article in articles:
                    url = article.get_attribute('href')
                    if url:
                        if not found_last_url:
                            if url == last_url:
                                found_last_url = True
                                continue
                            continue
                        post_urls.append(url)
                
                if not found_last_url:
                    self.logger.info(f"페이지 {page}에서 마지막 URL을 찾지 못했습니다.")
                
                # 다음 페이지로 이동
                if page < max_pages:
                    try:
                        # 10의 배수 페이지에서는 다음 버튼 클릭
                        if page % 10 == 0:
                            next_btn = self.driver.find_element(By.CSS_SELECTOR, "a.pgR")
                            next_btn.click()
                            time.sleep(3)
                            # 다음 페이지 그룹의 첫 페이지(11, 21, 31...)로 이동
                            page_btn = self.driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                            page_btn.click()
                        else:
                            # 그 외에는 숫자 버튼 직접 클릭
                            page_btn = self.driver.find_element(By.XPATH, f"//a[text()='{page + 1}']")
                            page_btn.click()
                            
                        # 페이지 로딩 대기
                        time.sleep(3)
                        
                    except Exception as e:
                        self.logger.error(f"페이지 {page}에서 {page + 1}로 이동 실패: {e}")
                        break
                    
                self.logger.info(f"페이지 {page} 처리 완료 (소요시간: {time.time() - page_start_time:.2f}초)")
                    
            except Exception as e:
                self.logger.error(f"페이지 {page} 처리 중 오류: {e}")
                break
                
        self.logger.info(f"URL 수집 완료 (총 {len(post_urls)}개 URL, 소요시간: {time.time() - start_time:.2f}초)")
        return post_urls

    def extract_post_data(self, url):
        start_time = time.time()
        try:
            self.driver.get(url)
            time.sleep(2)
            if not self.switch_to_iframe():
                return None
                
            # 제목
            title = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3.title_text"))
            ).text
            # 가격
            try:
                price = self.driver.find_element(By.CSS_SELECTOR, "div.ProductPrice strong.cost").text
            except:
                price = "가격 정보 없음"
            # 판매여부
            try:
                status = self.driver.find_element(By.CSS_SELECTOR, "em.SaleLabel").text
            except:
                status = "판매중"
            # 닉네임
            try:
                nickname = self.driver.find_element(By.CSS_SELECTOR, "div.nick_box button.nickname").text
            except:
                nickname = "닉네임 없음"
            # 날짜
            try:
                date = self.driver.find_element(By.CSS_SELECTOR, "div.article_info span.date").text
            except:
                date = "날짜 정보 없음"
            category = "여성패션"
            
            self.logger.info(f"상품 데이터 추출 완료: {title} (소요시간: {time.time() - start_time:.2f}초)")
            
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
            self.logger.error(f"게시글 데이터 추출 실패 ({url}): {e} (소요시간: {time.time() - start_time:.2f}초)")
            return None

    def crawl_category(self, category_url, max_pages=1, last_url=None):
        start_time = time.time()
        self.logger.info(f"카테고리 크롤링 시작: {category_url}")
        if last_url:
            self.logger.info(f"마지막 크롤링 URL 이후부터 시작: {last_url}")
            
        post_urls = self.get_post_urls(category_url, max_pages, last_url)
        self.logger.info(f"수집된 게시글 URL 수: {len(post_urls)}")
        
        # CSV 파일 초기 생성
        output_file = f"joonggo_data_{int(time.time())}.csv"
        df = pd.DataFrame(columns=['category', 'title', 'price', 'status', 'date', 'nickname', 'url'])
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        self.logger.info(f"CSV 파일 생성됨: {output_file}")
        
        posts_data = []
        for url in tqdm(post_urls, desc="게시글 데이터 수집 중"):
            post_data = self.extract_post_data(url)
            if post_data:
                posts_data.append(post_data)
                # 실시간으로 CSV 파일 업데이트
                df = pd.DataFrame([post_data])
                df.to_csv(output_file, mode='a', header=False, index=False, encoding='utf-8-sig')
        
        self.logger.info(f"크롤링 완료! 총 {len(posts_data)}개의 상품이 수집되었습니다. (총 소요시간: {time.time() - start_time:.2f}초)")
        if posts_data:
            self.logger.info(f"마지막으로 크롤링한 URL: {posts_data[-1]['url']}")
        return posts_data

    def close(self):
        self.logger.info("WebDriver 종료")
        self.driver.quit() 