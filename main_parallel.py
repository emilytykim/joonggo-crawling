from multiprocessing import Pool, cpu_count
from crawler import crawl_category
import json


def run_parallel(categories, max_pages=20):
    tasks = []
    for cat in categories:
        name = cat["name"]
        url = cat["url"]
        tasks.append((name, url, max_pages))

    with Pool(processes=min(4, cpu_count())) as pool:
        pool.starmap(crawl_category, tasks)


if __name__ == "__main__":
    with open("categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    # ✅ 상위 3개 카테고리만 실행 (예시)
    selected = categories[:3]
    run_parallel(selected, max_pages=20)
