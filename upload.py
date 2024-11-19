import pandas as pd
import requests

# CSV 파일 읽기
csv_file_path = "data.csv"
try:
    df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
    df['content'] = df['content'].fillna('') + '\n' + df['image content'].fillna('')
    df['content'] = df['content'].str.strip()
    df = df.drop(columns=['image content'])

    # CSV 데이터를 다시 문자열로 변환
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')

    # API 요청
    url = "https://hansung.store/api/v1/documents"
    headers = {'Content-Type': 'text/csv; charset=utf-8'}
    response = requests.post(url, headers=headers, data=csv_data.encode('utf-8'))

    if response.status_code == 201:
        print("문서가 성공적으로 업로드되었습니다.")
    else:
        print(f"문서 업로드 실패: {response.status_code}, {response.text}")
except Exception as e:
    print(f"CSV 파일 읽기 또는 업로드 중 오류 발생: {e}")
