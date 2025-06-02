from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    options = Options()
    # options.add_argument('--headless')  # 창 안 띄우려면
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('user-agent=Mozilla/5.0')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_album_list_data(driver, category_name="여성패션"):
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
        except:
            url = ""
        results.append({
            "category": category_name,
            "status": status,
            "title": title,
            "price": price,
            "nickname": nickname,
            "date": date,
            "url": url
        })
    return results

def crawl_category_album(driver, category_url, max_pages=2, category_name="여성패션"):
    all_results = []
    for page in range(1, max_pages + 1):
        url = f"{category_url}?page={page}&viewType=I&size=20"
        driver.get(url)
        time.sleep(2)
        results = extract_album_list_data(driver, category_name)
        all_results.extend(results)
        print(f"페이지 {page} 수집 완료: {len(results)}건")
    return all_results

def save_csv(data, filename):
    os.makedirs("results", exist_ok=True)
    path = f"results/{filename}"
    df = pd.DataFrame(data)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"✅ 저장 완료: {path} ({len(data)}건)")

def main():
    driver = setup_driver()
    # 네이버 로그인
    driver.get("https://nid.naver.com/nidlogin.login")
    input("네이버 로그인을 완료하고 엔터를 누르세요...")

    category_url = "https://cafe.naver.com/f-e/cafes/10050146/menus/356"
    category_name = "여성패션"
    results = crawl_category_album(driver, category_url, max_pages=2, category_name=category_name)
    save_csv(results, "joonggo_album.csv")
    driver.quit()

if __name__ == "__main__":
    main()
