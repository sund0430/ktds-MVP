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

# Streamlit UI 설정
st.set_page_config(page_title="앱 리뷰 분석기", layout="centered")
st.title("📱 구글 플레이 앱 리뷰 분석기")
st.write("앱 이름을 입력하면 사용자 리뷰를 분석해 보고서를 생성합니다.")

# 세션 상태 초기화
if "search_index" not in st.session_state:
    st.session_state.search_index = 0
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "confirmed" not in st.session_state:
    st.session_state.confirmed = False
if "disable_buttons" not in st.session_state:
    st.session_state.disable_buttons = False
if "app_name" not in st.session_state:
    st.session_state.app_name = ""
if "no_count" not in st.session_state:
    st.session_state.no_count = 0  # "아니요" 클릭 횟수 카운팅

# 앱 이름 입력
app_name = st.text_input("리뷰를 보고 싶은 앱 이름을 입력하세요", key="app_name", value=st.session_state.app_name)

# 앱 이름이 변경되면 세션 상태 초기화
if app_name != st.session_state.app_name:
    st.session_state.app_name = app_name
    st.session_state.search_index = 0
    st.session_state.search_results = []
    st.session_state.confirmed = False
    st.session_state.disable_buttons = False
    st.session_state.no_count = 0  # "아니요" 클릭 횟수 초기화

# 앱 검색
if st.session_state.app_name and not st.session_state.search_results:
    with st.spinner("앱 정보를 불러오는 중..."):
        st.session_state.search_results = search(st.session_state.app_name, lang="ko", country="kr")

# 앱 후보 확인
if st.session_state.search_results and not st.session_state.confirmed:
    if st.session_state.search_index >= 5:
        st.error("❌ 5개의 앱을 확인했지만 원하는 앱을 찾을 수 없습니다. 이름을 다시 확인해주세요.")
        st.session_state.search_results = []
        st.session_state.no_count = 0  # "아니요" 클릭 횟수 초기화
        st.session_state.search_index = 0  # 앱 후보 인덱스 초기화
        st.session_state.app_name = ""  # 앱 이름 초기화
        st.session_state.confirmed = False  # 앱 확정 여부 초기화
        st.experimental_rerun()  # 상태 초기화 후 페이지 새로고침

    else:
        app_info = st.session_state.search_results[st.session_state.search_index]
        st.write(f"🔍 앱 후보 {st.session_state.search_index + 1}: **{app_info['title']}**")
        st.image(app_info["icon"], width=100)
        st.write(f"설명: {app_info.get('summary', '')}")
        st.write(f"패키지명: `{app_info['appId']}`")

        disable_buttons = st.session_state.disable_buttons

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 이 앱이 맞아요", key="confirm_btn", disabled=disable_buttons):
                st.session_state.confirmed = True
                st.session_state.disable_buttons = True
                st.session_state.no_count = 0  # "아니요" 클릭 횟수 초기화
                st.experimental_rerun()  # 상태 변경 후 페이지를 다시 로드

        with col2:
            if st.button("❌ 아니요, 다음 앱 보기", key="next_btn", disabled=disable_buttons):
                # 상태 업데이트 후 버튼 클릭 반영
                st.session_state.search_index += 1
                st.session_state.disable_buttons = False
                st.session_state.no_count += 1  # "아니요" 클릭 횟수 증가

                # 5번 연속 "아니요" 클릭 시 앱 이름을 다시 입력하게 안내
                if st.session_state.no_count >= 5:
                    st.warning("❌ 5번 연속으로 '아니요'를 클릭하셨습니다. 다시 앱 이름을 입력해주세요.")
                    st.session_state.search_results = []  # 앱 목록 초기화
                    st.session_state.no_count = 0  # "아니요" 클릭 횟수 초기화
                    st.session_state.search_index = 0  # 앱 후보 인덱스 초기화
                    st.experimental_rerun()  # 상태 초기화 후 페이지 새로고침

                else:
                    # 상태 업데이트 후 페이지 새로고침
                    st.experimental_rerun()

# 리뷰 수집 및 분석 (확정된 앱에 대해서만)
if st.session_state.confirmed:
    app_info = st.session_state.search_results[st.session_state.search_index]
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
