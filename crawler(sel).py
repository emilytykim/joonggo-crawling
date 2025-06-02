# crawler.py

import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os


def get_post_links(driver, category_url, max_pages=50):
    """
    게시판 리스트 페이지에서 글 제목, URL, 작성일, 닉네임 수집
    """
    driver.get(category_url)
    time.sleep(2)

    posts = []
    current_page = 1

    while current_page <= max_pages:
        print(f"📄 Page {current_page}")
        time.sleep(1)

        try:
            post_rows = driver.find_elements(By.CSS_SELECTOR, "#cafe_content .article-board table tbody tr")

            for row in post_rows:
                try:
                    title_elem = row.find_element(By.CSS_SELECTOR, "td.td_article a.article")
                    date_elem = row.find_element(By.CSS_SELECTOR, "td.td_date")
                    nick_elem = row.find_element(By.CSS_SELECTOR, "td.p-nick a.m-tcol-c")

                    posts.append({
                        "title": title_elem.text.strip(),
                        "url": title_elem.get_attribute("href"),
                        "date": date_elem.text.strip(),
                        "nickname": nick_elem.text.strip()
                    })

                except Exception:
                    continue

            # 다음 페이지 버튼 클릭
            next_button_xpath = f"//button[@class='btn number' and text()='{(current_page % 10) or 10}']"
            try:
                next_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                )
                next_btn.click()
                current_page += 1
            except:
                print("⛔️ 더 이상 페이지 없음")
                break

            # 10번째 페이지마다 → 화살표 눌러서 11, 21, ...로 이동
            if current_page % 10 == 1 and current_page != 1:
                try:
                    arrow_btn = driver.find_element(By.CSS_SELECTOR, ".Pagination .btn.type_next")
                    arrow_btn.click()
                    time.sleep(1)
                except:
                    break

        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            break

    return posts


def get_post_details(driver, post):
    """
    상세페이지 진입해서 가격, 판매상태 추출
    """
    try:
        driver.get(post["url"])
        time.sleep(1)

        # 가격 추출
        price_elem = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "strong.cost"))
        )
        post["price"] = price_elem.text.strip()

        # 판매상태 추출
        try:
            status_elem = driver.find_element(By.CSS_SELECTOR, "em.SaleLabel")
            post["status"] = status_elem.text.strip()
        except:
            post["status"] = "판매중"

    except Exception as e:
        print(f"❌ 상세 페이지 오류: {post['url']} | {e}")
        post["price"] = "N/A"
        post["status"] = "N/A"

    return post


def crawl_category(category_name, category_url, output_csv, max_pages=50):
    """
    카테고리 전체 순회 크롤링
    """
    print(f"🚀 Start crawling: {category_name}")

    # 세션 유지하고 싶으면 아래에 user-data-dir 추가
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--user-data-dir=/Users/yourname/Library/Application Support/Google/Chrome")

    driver = webdriver.Chrome(options=options)

    try:
        post_links = get_post_links(driver, category_url, max_pages)

        all_data = []
        for idx, post in enumerate(post_links, 1):
            print(f"🔍 ({idx}/{len(post_links)}) 상세 페이지 크롤링 중...")
            result = get_post_details(driver, post)
            all_data.append(result)

        # 저장 디렉토리 생성
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)

        # CSV 저장
        with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "url", "date", "nickname", "price", "status"])
            writer.writeheader()
            writer.writerows(all_data)

        print(f"✅ 저장 완료: {output_csv}")

    finally:
        driver.quit()
