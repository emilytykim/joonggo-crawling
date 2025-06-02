from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

options = Options()
# options.add_argument("--headless")  # 꼭 꺼두세요
options.add_argument("--disable-gpu")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)

driver.get("https://cafe.naver.com/joonggonara")
time.sleep(5)

iframes = driver.find_elements(By.TAG_NAME, "iframe")
for iframe in iframes:
    print("🪟 iframe ID:", iframe.get_attribute("id"))

input("👉 iframe 확인 후 Enter 누르면 창 닫힘")
driver.quit()
