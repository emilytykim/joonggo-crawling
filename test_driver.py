import undetected_chromedriver as uc

options = uc.ChromeOptions()
options.add_argument(
    "--user-data-dir=/Users/emily/Library/Application Support/Google/Chrome"
)
options.add_argument("--profile-directory=Profile 2")
# options.add_argument("--headless=new")  # 일단 꺼놓기

try:
    print("🟡 드라이버 실행 중...")
    driver = uc.Chrome(options=options)
    print("🟢 드라이버 성공적으로 실행됨")
    driver.get("https://naver.com")
    input("⏸️ 아무 키나 누르면 종료")  # 크롬 눈으로 확인
except Exception as e:
    print(f"❌ 오류 발생: {e}")
