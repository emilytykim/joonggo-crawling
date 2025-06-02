# crawler.py

import os
import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from multiprocessing import Pool, cpu_count


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
