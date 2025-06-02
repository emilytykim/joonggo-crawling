import pandas as pd
import glob
import os

# 결과 파일 패턴 (필요시 수정)
file_pattern = "results/여성패션_의류_*.csv"
output_file = "results/여성패션_의류_통합.csv"

def main():
    files = glob.glob(file_pattern)
    if not files:
        print("통합할 파일이 없습니다.")
        return
    print(f"통합 대상 파일: {files}")
    dfs = [pd.read_csv(f) for f in files]
    df_all = pd.concat(dfs, ignore_index=True)
    before = len(df_all)
    # article_id 기준 중복 제거
    df_all = df_all.drop_duplicates(subset=["article_id"])
    after = len(df_all)
    df_all.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ 통합 및 중복제거 완료: {output_file} ({after}건, 중복 {before-after}건 제거)")

if __name__ == "__main__":
    main() 