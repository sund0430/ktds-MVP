#실제 구글 플레이스토어에서 리뷰를 수집하여 취합 및 개선안 제안

import os
from openai import OpenAI
from dotenv import load_dotenv
from google_play_scraper import reviews

load_dotenv()

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# 1. Azure OpenAI 클라이언트 생성
client = OpenAI(
    api_key=AZURE_OPENAI_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/",
    default_query={"api-version": "2024-05-01-preview"}
)

# 2. 구글 플레이스토어에서 리뷰 수집
result, _ = reviews(
    "com.kakao.talk",  # 앱 ID
    lang="ko",         # 한국어
    country="kr",      # 한국 스토어
    count=10           # 가져올 리뷰 개수
)

reviews_list = [r["content"] for r in result]

# 3. 리뷰 합치기
reviews_text = "\n".join(reviews_list)

# 4. GPT 프롬프트
prompt = f"""
아래는 우리 앱에 대한 실제 사용자 리뷰입니다:

{reviews_text}

이 리뷰들을 분석해서 아래 항목을 포함한 보고서를 작성해주세요:
1. 주요 불만사항
2. 긍정적 피드백
3. 개선 제안
"""

# 5. OpenAI 모델 호출
response = client.chat.completions.create(
    model=AZURE_OPENAI_DEPLOYMENT,
    messages=[{"role": "user", "content": prompt}]
)

# 6. 결과 출력
print("\n=== 분석 보고서 ===\n")
print(response.choices[0].message.content)

