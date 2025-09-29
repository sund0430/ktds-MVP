import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from google_play_scraper import search, reviews, Sort

load_dotenv()

AZURE_OPENAI_KEY = st.secrets["AZURE_OPENAI_KEY"]
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

client = OpenAI(
    api_key=AZURE_OPENAI_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/",
    default_query={"api-version": "2025-01-01-preview"}
)

st.set_page_config(page_title="앱 리뷰 분석기", layout="centered")
st.title("📱 구글 플레이 앱 리뷰 분석기")
st.write("앱 이름을 입력하면 사용자 리뷰를 분석해 보고서를 생성합니다.")

# 초기 세션 상태 설정
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

app_name = st.text_input("리뷰를 보고 싶은 앱 이름을 입력하세요", key="app_name", value=st.session_state.app_name)

if app_name != st.session_state.app_name:
    st.session_state.app_name = app_name
    st.session_state.search_index = 0
    st.session_state.search_results = []
    st.session_state.confirmed = False
    st.session_state.disable_buttons = False

if st.session_state.app_name and not st.session_state.search_results:
    with st.spinner("앱 정보를 불러오는 중..."):
        st.session_state.search_results = search(st.session_state.app_name, lang="ko", country="kr")
        st.session_state.search_index = 0

if st.session_state.search_results and not st.session_state.confirmed:
    if st.session_state.search_index >= 5:
        st.error("❌ 5개의 앱을 확인했지만 원하는 앱을 찾을 수 없습니다. 이름을 다시 확인해주세요.")
        st.session_state.search_results = []
    else:
        app_info = st.session_state.search_results[st.session_state.search_index]
        st.write(f"🔍 앱 후보 {st.session_state.search_index + 1}: **{app_info['title']}**")
        st.image(app_info["icon"], width=100)
        st.write(f"설명: {app_info.get('summary', '')}")
        st.write(f"패키지명: `{app_info['appId']}`")

        disable_buttons = st.session_state.disable_buttons

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ 이 앱이 맞아요", disabled=disable_buttons):
                st.session_state.confirmed = True
                st.session_state.disable_buttons = True
                st.experimental_rerun()  # 여기서만 호출
        with col2:
            if st.button("❌ 아니요, 다음 앱 보기", disabled=disable_buttons):
                st.session_state.search_index += 1
                st.experimental_rerun()  # 여기서만 호출

if st.session_state.confirmed:
    app_info = st.session_state.search_results[st.session_state.search_index]
    package_name = app_info["appId"]
