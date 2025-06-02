import pandas as pd
import glob
import os

def combine_csv_files(category_name):
    # 결과를 저장할 디렉토리 생성
    output_dir = "result_total"
    os.makedirs(output_dir, exist_ok=True)
    
    # 입력받은 카테고리로 시작하는 모든 CSV 파일 찾기
    pattern = f"results/{category_name}_*.csv"
    csv_files = glob.glob(pattern)
    
    if not csv_files:
        print(f"'{category_name}'으로 시작하는 CSV 파일을 찾을 수 없습니다.")
        return
    
    # 제외할 날짜 접두어 리스트
    exclude_prefixes = ['2025.05.27', '2025.05.28', '2025.05.29', '2025.05.30']
    
    # 파일들을 데이터프레임으로 읽어서 리스트에 저장
    dfs = []
    for i, file in enumerate(csv_files):
        try:
            df = pd.read_csv(file, encoding='utf-8-sig')
            if i > 0:  # 첫 번째 파일이 아닌 경우
                df = df.iloc[1:]  # 헤더 제외
            
            # 제외할 날짜로 시작하는 행 마스킹
            mask = df['date'].astype(str).str.startswith(tuple(exclude_prefixes))
            removed = df[mask]
            print(f"[{os.path.basename(file)}] 제외된 행: {len(removed)}개 (예시: {removed['date'].unique()[:5]})")
            
            # 제외
            df = df[~mask]
            
            dfs.append(df)
            print(f"파일 로드 완료: {file}")
        except Exception as e:
            print(f"파일 로드 중 오류 발생 ({file}): {e}")
    
    if not dfs:
        print("데이터를 로드할 수 없습니다.")
        return
    
    # 모든 데이터프레임 합치기
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # 결과 파일 저장
    output_file = f"{output_dir}/{category_name}_전체.csv"
    combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 파일 병합 완료: {output_file}")
    print(f"총 {len(combined_df)}개의 행이 저장되었습니다.")
    print(f"총 병합된 파일 개수: {len(csv_files)}개")

if __name__ == "__main__":
    category_name = input("카테고리명을 입력하세요 (예: 도서, 중고폰, 스타굿즈 등): ").strip()
    combine_csv_files(category_name) 