import os
from llama_parse import LlamaParse
import nest_asyncio
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin
import pandas as pd
import time
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
api_key = os.getenv("LLAMA_CLOUD_API_KEY")

# LlamaParse 설정
parser = LlamaParse(
    api_key=api_key,
    result_type="markdown",
    num_workers=4,
    verbose=True,
    language="ko",
)

nest_asyncio.apply()

# 이미지에서 텍스트 추출 함수
def extract_text_from_image(img_url):
    img_response = requests.get(img_url, timeout=1)
    if img_response.status_code == 200:
        img_data = BytesIO(img_response.content)
        file_info = {"file_name": img_url.split('/')[-1]}
        documents = parser.load_data(img_data, extra_info=file_info)

        extracted_texts = [doc.text.strip() for doc in documents if doc.text.strip()]
        
        # 줄바꿈을 포함해 포맷팅
        return "\n".join(extracted_texts)  # 각 문단 사이에 두 줄바꿈 추가
    else:
        print(f"이미지를 가져오는 데 실패했습니다: {img_url}")
        return ""

data = []

for i in range(264710, 264716):  # 원하는 범위 설정
    try:
        response = requests.get(f"https://www.hansung.ac.kr/bbs/hansung/143/{i}/artclView.do?layout=unknown", timeout=1)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        items = soup.select(".contents")

        for item in items:
            subject = item.select_one(".view-title").get_text(strip=True) if item.select_one(".view-title") else "제목 없음"
            writer = item.select_one(".writer dd").get_text(strip=True) if item.select_one(".writer dd") else "작성자 없음"
            category = item.select_one(".cate dd").get_text(strip=True) if item.select_one(".cate dd") else "카테고리 없음"
            date = item.select_one(".write dd").get_text(strip=True) if item.select_one(".write dd") else "작성일 없음"
            spans = item.select(".view-con span")
            text = " ".join(span.get_text(strip=True) for span in spans) if spans else ""

            # 이미지 태그 찾기
            images = item.select('img')
            extracted_texts = []  # 이미지 텍스트를 저장할 리스트
            
            for img in images:
                img_url = urljoin(response.url, img['src'])  # 절대 URL로 변환
                extracted_text = extract_text_from_image(img_url)
                extracted_texts.append(extracted_text)  # 추출된 텍스트를 리스트에 추가

            # 내용과 이미지 텍스트가 둘 다 없는 경우 데이터 추가하지 않음
            if text or any(extracted_texts):
                data.append({
                    "content": text,
                    "image content": "\n".join(extracted_texts),
                    "date": date,
                    "title": subject,
                    "link": response.url,
                    "author": writer,
                    "category": category
                })
        
        time.sleep(0.1)  # 요청 간격을 두기 위해 0.1초 대기

    except requests.exceptions.RequestException as e:
        print(f"요청 중 오류 발생: {e}")

# DataFrame으로 변환하고 CSV 파일 저장
csv_file_path = "data.csv"
try:
    df = pd.DataFrame(data)
    with open(csv_file_path, 'w', encoding='utf-8-sig', newline='') as f:
        df.to_csv(f, index=False)
    print(f"CSV 파일 '{csv_file_path}'로 저장되었습니다.")
except Exception as e:
    print(f"CSV 파일 저장 중 오류 발생: {e}")
