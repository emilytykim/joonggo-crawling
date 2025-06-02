import time
import json
import os
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

BASE_URL = "https://cafe.naver.com/f-e"


def init_driver(user_data_dir=None):
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    if user_data_dir:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=chrome_options
    )


def get_post_list_html(driver, category_url, page):
    paginated_url = f"{category_url}&page={page}"
    driver.get(paginated_url)
    time.sleep(2)  # 💤 동적 로딩 대기
    driver.switch_to.frame("cafe_main")  # ✅ 게시글 목록 iframe으로 전환
    return driver.page_source


def parse_post_list(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr[align='center']")

    post_data = []
    for row in rows:
        link_tag = row.select_one("a.article")
        if not link_tag:
            continue

        title = link_tag.text.strip()
        url = BASE_URL + link_tag["href"]
        id_ = url.split("/")[-1]

        user = row.select_one("td.p-nick a")
        nickname = user.text.strip() if user else "Unknown"

        date_tag = row.select_one("td.date")
        date = date_tag.text.strip() if date_tag else ""

        post_data.append(
            {"id": id_, "title": title, "url": url, "nickname": nickname, "date": date}
        )

    return post_data


def crawl_category(category_name, category_url, output_dir="output", max_pages=2):
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{category_name}.csv")

    driver = init_driver(
        user_data_dir="/Users/emily/Library/Application Support/Google/Chrome"
    )  # ✅ 수정 가능
    all_data = []

    try:
        for page in range(1, max_pages + 1):
            print(f"📄 Crawling page {page} of {category_name}")
            html = get_post_list_html(driver, category_url, page)
            posts = parse_post_list(html)
            all_data.extend(posts)
            time.sleep(1)
    except WebDriverException as e:
        print(f"❌ WebDriver error: {e}")
    finally:
        driver.quit()

    with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f, fieldnames=["id", "title", "url", "nickname", "date"]
        )
        writer.writeheader()
        writer.writerows(all_data)

    print(f"✅ Saved {len(all_data)} posts to {output_file}")
