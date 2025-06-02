# main.py

import json
import os
from crawler import crawl_category


def load_categories(path="categories.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    categories = load_categories()
    output_dir = "output"

    for cat in categories:
        name = cat["name"]
        url = cat["url"]
        output_path = os.path.join(output_dir, f"{name}.csv")

        print(f"\n====== {name} 카테고리 시작 ======")
        crawl_category(
            name, url, output_path, max_pages=5
        )  # ← 페이지 수는 테스트용으로 5부터 시작해봐


if __name__ == "__main__":
    main()
# main.py

import json
import os
from crawler import crawl_category


def load_categories(path="categories.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    categories = load_categories()
    output_dir = "output"

    for cat in categories:
        name = cat["name"]
        url = cat["url"]
        output_path = os.path.join(output_dir, f"{name}.csv")

        crawl_category(name, url, output_path)


if __name__ == "__main__":
    main()
