from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import os

from webdriver_manager.chrome import ChromeDriverManager


def setup_driver():
    options = Options()
    # options.add_argument("--headless")  # 창 안 띄우려면
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def switch_to_iframe(driver):
    WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "cafe_main"))
    )


def extract_posts(driver, page_num):
    base_url = f"https://cafe.naver.com/ArticleList.nhn?search.clubid=10050146&search.menuid=356&search.boardtype=L&search.page={page_num}"
    driver.get(base_url)
    switch_to_iframe(driver)

    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table.board-list tbody tr")
        post_urls = []
        for row in rows:
            try:
                link = row.find_element(By.CSS_SELECTOR, "a.article")
                href = link.get_attribute("href")
                if href:
                    full_url = "https://cafe.naver.com" + href
                    post_urls.append(full_url)
            except:
                continue
        return post_urls
    except Exception as e:
        print(f"❌ Failed to extract post URLs: {e}")
        return []


def extract_detail(driver, url):
    driver.get(url)
    switch_to_iframe(driver)

    try:
        title = driver.find_element(By.CSS_SELECTOR, "h3.title_text").text.strip()
    except:
        title = ""

    try:
        price = driver.find_element(
            By.CSS_SELECTOR, "div.ProductPrice strong.cost"
        ).text.strip()
    except:
        price = ""

    try:
        content = driver.find_element(
            By.CSS_SELECTOR, "div.se-main-container"
        ).text.strip()
    except:
        content = ""

    return {"url": url, "title": title, "price": price, "content": content}


def crawl_category(category_name="여성패션", pages=3):
    driver = setup_driver()
    time.sleep(10)
    results = []

    for page in range(1, pages + 1):
        print(f"📄 Crawling page {page}")
        post_urls = extract_posts(driver, page)

        for post_url in post_urls:
            detail = extract_detail(driver, post_url)
            if detail["title"]:
                results.append(detail)
                print(f"✅ {detail['title']}")

        time.sleep(1)

    driver.quit()
    save_csv(results, category_name)


def save_csv(data, category_name):
    os.makedirs("results", exist_ok=True)
    path = f"results/{category_name}.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "title", "price", "content"])
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ {category_name} → 저장 완료: {path} ({len(data)}건)")


if __name__ == "__main__":
    crawl_category(category_name="여성패션", pages=5)
