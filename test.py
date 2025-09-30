# 직접 입력한 샘플 리뷰를 가지고 취합 및 개선안 제안

import os
from openai import AzureOpenAI
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# 1. 클라이언트 생성
client = OpenAI(
    api_key=AZURE_OPENAI_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/",
    default_query={"api-version": "2024-05-01-preview"}) # 최신 API 버전

# 2. 리뷰 (연습용 직접 입력)
reviews = [
    "앱이 자꾸 멈춰서 불편합니다.",
    "업데이트 이후 속도가 빨라졌어요. 만족합니다!",
    "광고가 너무 많아요.",
    "UI가 헷갈리고 직관적이지 않아요.",
    "고객센터 응답이 빨라서 좋았습니다."
]

# 3. 리뷰 합치기
reviews_text = "\n".join(reviews)

# 4. GPT 프롬프트
prompt = f"""
아래는 우리 앱에 대한 사용자 리뷰입니다:

{reviews_text}

이 리뷰들을 분석해서 아래 항목을 포함한 보고서를 작성해주세요:
1. 주요 불만사항
2. 긍정적 피드백
3. 개선 제안
"""

# 5. OpenAI 모델 호출
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}]
)

# 6. 결과 출력
print(response.choices[0].message.content)

