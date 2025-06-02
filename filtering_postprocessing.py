import pandas as pd

# CSV 파일 경로
input_file = "results/중고폰_모바일_중고폰_추천_1-313.csv"
output_file = "results/중고폰_모바일_중고폰_추천_0531.csv"

# CSV 로드 (utf-8-sig 인코딩)
df = pd.read_csv(input_file, encoding="utf-8-sig")

# "매입" 단어가 포함된 행 찾기
mask = df.applymap(lambda x: "매입" in str(x)).any(axis=1)

# "매입"이 포함된 행 삭제
filtered_df = df[~mask].reset_index(drop=True)

# 필터링된 데이터프레임 저장
filtered_df.to_csv(output_file, index=False, encoding="utf-8-sig")

# 결과 출력
print(f"원본 데이터: {len(df)}행")
print(f"필터링 후 데이터: {len(filtered_df)}행")
print(f"제거된 '매입' 관련 게시글: {len(df) - len(filtered_df)}행")
