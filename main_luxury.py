import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
import glob
import json

def setup_driver():
    options = Options()
    # options.add_argument('--headless')  # 창 안 띄우려면
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('user-agent=Mozilla/5.0')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_article_id(url):
    match = re.search(r'articles/(\d+)', url)
    return int(match.group(1)) if match else None

def load_existing_article_ids():
    """기존 CSV 파일들에서 article_id를 로드하고 별도 파일로 저장"""
    article_ids = set()
    
    # CSV 파일들에서 ID 로드 (명품 전용)
    for file in glob.glob("results/명품_*.csv"):
        try:
            df = pd.read_csv(file)
            if 'article_id' in df.columns:
                ids = df['article_id'].dropna().astype(int).tolist()
                article_ids.update(ids)
                print(f"파일 {file}에서 {len(ids)}개의 ID 로드")
        except Exception as e:
            print(f"파일 {file} 로드 중 오류: {e}")
    
    # ID 목록을 별도 파일로 저장
    os.makedirs("results", exist_ok=True)
    with open("results/article_ids.json", "w") as f:
        json.dump(list(article_ids), f)
    
    print(f"총 {len(article_ids)}개의 고유 ID 로드 완료")
    return article_ids

def extract_album_list_data(driver, category_name="명품"):
    category_name = category_name.replace('/', '_')
    items = driver.find_elements(By.CSS_SELECTOR, "ul.article-album-view > li.item")
    print(f"상품 li 개수: {len(items)}")  # 디버깅용
    results = []
    for item in items:
        try:
            title = item.find_element(By.CSS_SELECTOR, "dl > dt.tit_area > a.tit > span.tit_txt").text.strip()
        except:
            title = ""
        try:
            price = item.find_element(By.CSS_SELECTOR, "dl > dd.price > em").text.strip()
        except:
            price = ""
        try:
            nickname = item.find_element(By.CSS_SELECTOR, "dl > dd.nick_area span.nickname").text.strip()
        except:
            nickname = ""
        try:
            date = item.find_element(By.CSS_SELECTOR, "dl > dd.date_num > span.date").text.strip()
        except:
            date = ""
        try:
            status = item.find_element(By.CSS_SELECTOR, "svg[aria-label]").get_attribute("aria-label")
        except:
            status = ""
        try:
            url = item.find_element(By.CSS_SELECTOR, "dl > dt.tit_area > a.tit").get_attribute("href")
            article_id = extract_article_id(url)
        except:
            url = ""
            article_id = None
        results.append({
            "category": category_name,
            "status": status,
            "title": title,
            "price": price,
            "nickname": nickname,
            "date": date,
            "url": url,
            "article_id": article_id
        })
    return results

def save_csv(data, filename, header=True):
    os.makedirs("results", exist_ok=True)
    path = f"results/{filename}"
    df = pd.DataFrame(data)
    columns = ["category", "status", "title", "price", "nickname", "date", "url", "article_id"]
    output_columns = ["category", "status", "title", "price", "nickname", "date"]
    df = df[columns] if all(col in df.columns for col in columns) else df
    df_out = df[output_columns] if all(col in df.columns for col in output_columns) else df
    df_out.to_csv(path, mode='a', header=header, index=False, encoding="utf-8-sig")
    print(f"✅ 저장 완료: {path} (+{len(data)}건)")

def is_date_format(s):
    return bool(re.match(r"^\d{4}\.\d{2}\.\d{2}$", s))

def crawl_category_album(driver, category_url, start_page, end_page, category_name, existing_ids, filename):
    all_results = []
    header_written = False
    stop_date = "2025.05.31"
    stop_flag = False
    for page in range(start_page, end_page + 1):
        if stop_flag:
            break
        url = f"{category_url}?page={page}&viewType=I&size=20"
        driver.get(url)
        time.sleep(2)
        results = extract_album_list_data(driver, category_name)
        new_results = []
        for row in results:
            article_id = row.get("article_id")
            if article_id is None:
                continue
            post_date = row.get("date", "")
            # 2025.05.31까지 저장, 그 이전(더 작은 날짜)은 저장하지 않음
            if is_date_format(post_date):
                if post_date < stop_date:
                    stop_flag = True
                    print(f"중단 기준 날짜({stop_date})보다 이전 게시글 발견: {post_date} (page {page})")
                    break
            new_results.append(row)
        all_results.extend(new_results)
        print(f"페이지 {page} 수집 완료: {len(results)}건 (저장: {len(new_results)}건, 중복 제외: {len(results) - len(new_results)}건)")
        save_csv(new_results, filename, header=not header_written)
        header_written = True
    print(f"이번 크롤링에서 {len(all_results)}개의 게시글을 수집했습니다.")
    return all_results

def main():
    driver = setup_driver()
    driver.get("https://nid.naver.com/nidlogin.login")
    input("네이버 로그인을 완료하고 엔터를 누르세요...")

    # 명품 카테고리 목록
    categories = [
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/1007",
            "name": "명품_여성의류",
            "end_page": 85
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/1008",
            "name": "명품_남성의류",
            "end_page": 60
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/782",
            "name": "명품_가방",
            "end_page": 61
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/1011",
            "name": "명품_시계",
            "end_page": 98
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/791",
            "name": "명품_유아_아동",
            "end_page": 28
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/1010",
            "name": "명품_남성신발",
            "end_page": 15
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/1009",
            "name": "명품_여성신발",
            "end_page": 18
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/785",
            "name": "명품_악세서리",
            "end_page": 48
        },
        {
            "url": "https://cafe.naver.com/f-e/cafes/10050146/menus/787",
            "name": "명품_기타",
            "end_page": 28
        }
    ]
    
    # 기존 article_id 로드
    existing_ids = load_existing_article_ids()
    print(f"기존 article_id 수: {len(existing_ids)}")
    
    # 각 카테고리별로 크롤링
    for category in categories:
        print(f"\n=== {category['name']} 카테고리 크롤링 시작 ===")
        start_page = 1
        end_page = category['end_page']
        # 슬래시를 밑줄로 변환
        safe_name = category['name'].replace('/', '_')
        filename = f"{safe_name}_{start_page}-{end_page}.csv"
        path = f"results/{filename}"
        if os.path.exists(path):
            os.remove(path)
        results = crawl_category_album(driver, category['url'], start_page, end_page, category['name'], existing_ids, filename)
        print(f"=== {category['name']} 카테고리 크롤링 완료 ===\n")
    
    driver.quit()

if __name__ == "__main__":
    main()