import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from urllib.parse import urljoin
import pandas as pd
import time
import nest_asyncio
from dotenv import load_dotenv
from llama_parse import LlamaParse
import re

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

# 비동기 적용
nest_asyncio.apply()

# 이미지 텍스트 추출 함수
def extract_text_from_image(img_url):
    try:
        img_response = requests.get(img_url, timeout=1)
        if img_response.status_code == 200:
            img_data = BytesIO(img_response.content)
            file_info = {"file_name": img_url.split('/')[-1]}
            documents = parser.load_data(img_data, extra_info=file_info)

            extracted_texts = [doc.text.strip() for doc in documents if doc.text.strip()]
            return "\n".join(extracted_texts)  # 추출된 텍스트 합치기
        else:
            print(f"이미지 가져오기 실패: {img_url}")
            return ""
    except Exception as e:
        print(f"이미지 텍스트 추출 중 오류: {e}")
        return ""

# RSS 피드 URL
rss_url = "https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?row=30"
rss_response = requests.get(rss_url)
rss_response.encoding = 'utf-8'
rss_soup = BeautifulSoup(rss_response.text, "xml")

# 데이터 저장 리스트
data = []

# RSS 피드에서 item 태그 추출
items = rss_soup.find_all("item")

for item in items:
    try:
        # RSS 정보 추출
        link = "https://www.hansung.ac.kr" + item.link.get_text(strip=True)
        pub_date = item.pubDate.get_text(strip=True)
        description = item.description.get_text(strip=True) if item.description else ""

        # AM/PM 제거 및 표준 형식으로 변환
        #pub_date = re.sub(r'\s[APap][Mm]', '', pub_date)

        # 상세 페이지 요청
        response = requests.get(link, timeout=1)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        # 내용 및 이미지 추출
        view_title = soup.select_one(".view-title")
        subject = view_title.get_text(strip=True) if view_title else "제목 없음"
        writer = soup.select_one(".writer dd").get_text(strip=True) if soup.select_one(".writer dd") else "작성자 없음"
        category = soup.select_one(".cate dd").get_text(strip=True) if soup.select_one(".cate dd") else "카테고리 없음"

        spans = soup.select(".view-con span")
        content_text = " ".join(span.get_text(strip=True) for span in spans) if spans else ""

        # description을 content에 합치기
        content_text = f"{description}\n{content_text}".strip()

        # 이미지 텍스트 추출
        images = soup.select('img')
        extracted_texts = []

        for img in images:
            img_src = img.get('src')
            if img_src:
                img_url = urljoin(response.url, img_src)
                extracted_text = extract_text_from_image(img_url)
                if extracted_text:
                    extracted_texts.append(extracted_text)

        # 텍스트 또는 이미지 텍스트가 있는 경우에만 추가
        if content_text or any(extracted_texts):
            data.append({
                "content": content_text,
                "image content": "\n".join(extracted_texts),
                "date": pub_date,
                "title": subject,
                "link": link,
                "author": writer,
                "category": category
            })

        # 요청 간격을 두기 위해 1초 대기
        time.sleep(1)

    except requests.exceptions.RequestException as e:
        print(f"요청 중 오류 발생: {e}")

# DataFrame으로 변환하고 CSV 파일 저장
csv_file_path = "data.csv"
try:
    df = pd.DataFrame(data)
    df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
    print(f"CSV 파일 '{csv_file_path}'로 저장되었습니다.")
except Exception as e:
    print(f"CSV 파일 저장 중 오류 발생: {e}")
