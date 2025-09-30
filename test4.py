# 실제 구글 플레이스토어에서 리뷰를 수집하여 취합 및 개선안 제안
# 데이터 전처리 (최신순, 최대 100건) 적용

import os
import time
from openai import OpenAI
from dotenv import load_dotenv
from google_play_scraper import search, reviews, Sort

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

print("⚠️ 리뷰 확인은 한 번에 하나의 앱만 가능합니다.")

# 2. 사용자에게 앱 이름 입력받기
app_name = input("리뷰를 보고 싶은 앱 이름을 입력하세요: ")

# 3. 앱 이름으로 appId 검색
search_results = search(app_name, lang="ko", country="kr")

if not search_results:
    print("앱을 찾을 수 없습니다. 이름을 다시 확인해 주세요.")
else:
    # 첫 번째 검색 결과 선택
    app_info = search_results[0]
    package_name = app_info["appId"]
    print(f"선택된 앱: {app_info['title']} (패키지명: {package_name})")

    # 4. 리뷰 수집 (최대 100개, 최신순)
    result, _ = reviews(
        package_name,
        lang="ko",
        country="kr",
        sort=Sort.NEWEST,
        count=100
    )
    time.sleep(2)

    reviews_list = [r["content"] for r in result if r["content"]]
    reviews_text = "\n".join(reviews_list)

    print(f"\n✅ 총 {len(reviews_list)}개의 리뷰를 수집했습니다.")

    # 5. GPT 프롬프트
    prompt = f"""
아래는 '{app_info['title']}' 앱에 대한 실제 사용자 리뷰입니다:

{reviews_text}

이 리뷰들을 분석해서 아래 항목을 포함한 보고서를 작성해주세요:
1. 주요 불만사항
2. 긍정적 피드백
3. 개선 제안
"""

    # 6. OpenAI 모델 호출
    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=[{"role": "user", "content": prompt}]
    )

    # 7. 결과 출력
    print("\n=== 분석 보고서 ===\n")
    print(response.choices[0].message.content)

