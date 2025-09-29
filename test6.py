# 실제 구글 플레이스토어에서 리뷰를 수집하여 취합 및 개선안 제안
# Streamlit 배포

import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from google_play_scraper import search, reviews, Sort

# 환경 변수 로드
load_dotenv()

# Azure OpenAI 정보
AZURE_OPENAI_KEY = st.secrets["AZURE_OPENAI_KEY"]
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

# OpenAI 클라이언트 생성
client = OpenAI(
    api_key=AZURE_OPENAI_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/",
    default_query={"api-version": "2025-01-01-preview"}
)

# Streamlit UI
st.set_page_config(page_title="앱 리뷰 분석기", layout="centered")
st.title("📱 구글 플레이 앱 리뷰 분석기")
st.write("앱 이름을 입력하면 사용자 리뷰를 분석해 보고서를 생성합니다.")

# 앱 이름 입력
app_name = st.text_input("리뷰를 보고 싶은 앱 이름을 입력하세요", "")

if app_name:
    # 앱 검색
    with st.spinner("앱 정보를 불러오는 중..."):
        search_results = search(app_name, lang="ko", country="kr")

    if not search_results:
        st.error("❌ 앱을 찾을 수 없습니다. 이름을 다시 확인해 주세요.")
    else:
        app_info = search_results[0]
        package_name = app_info["appId"]
        st.success(f"✅ 선택된 앱: {app_info['title']} (패키지명: {package_name})")

        # 리뷰 수집
        with st.spinner("리뷰 수집 중..."):
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

        st.info(f"💬 총 {len(reviews_list)}개의 리뷰를 수집했습니다.")

        # GPT 프롬프트 구성
        prompt = f"""
아래는 '{app_info['title']}' 앱에 대한 실제 사용자 리뷰입니다:

{reviews_text}

이 리뷰들을 분석해서 아래 항목을 포함한 보고서를 작성해주세요:
1. 주요 불만사항
2. 긍정적 피드백
3. 개선 제안
"""

        # GPT 호출
        with st.spinner("AI 분석 중..."):
            response = client.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT,
                messages=[{"role": "user", "content": prompt}]
            )
            report = response.choices[0].message.content

        # 결과 출력
        st.subheader("📝 분석 보고서")
        st.write(report)

