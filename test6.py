import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from google_play_scraper import search, reviews, Sort
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from langchain.agents import initialize_agent, Tool, AgentType

load_dotenv()

AZURE_OPENAI_KEY = st.secrets["AZURE_OPENAI_KEY"]
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

# OpenAI 클라이언트 생성
client = OpenAI(
    api_key=AZURE_OPENAI_KEY,
    base_url=f"{AZURE_OPENAI_ENDPOINT}openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/",
    default_query={"api-version": "2025-01-01-preview"}
)

# Streamlit 설정
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

# 앱 이름 입력과 검색 버튼을 나란히 배치
col1, col2 = st.columns([3, 1])  # 두 개의 열로 배치 (입력란은 넓고 버튼은 좁게)

# `app_name`을 세션 상태에서 가져오도록 설정
with col1:
    app_name = st.text_input("리뷰를 보고 싶은 앱 이름을 입력하세요", key="app_name_input", value=st.session_state.app_name)

with col2:
    search_button = st.button("검색", key="search_btn")

# 앱 이름이 변경되었을 경우, 세션 상태 초기화 및 검색 수행
if app_name != st.session_state.app_name:
    st.session_state.app_name = app_name  # 앱 이름 업데이트
    st.session_state.search_index = 0
    st.session_state.search_results = []
    st.session_state.confirmed = False
    st.session_state.disable_buttons = False
    st.session_state.no_count = 0

    # 앱 검색
    if app_name:
        with st.spinner("앱 정보를 불러오는 중..."):
            st.session_state.search_results = search(app_name, lang="ko", country="kr")
            
# 검색 버튼이 눌렸을 때 추가 동작
if search_button and app_name:
    # 이미 검색 결과가 없다면 다시 검색을 시도
    if not st.session_state.search_results:
        with st.spinner("앱 정보를 불러오는 중..."):
            st.session_state.search_results = search(app_name, lang="ko", country="kr")

# 앱 후보 확인
if st.session_state.search_results and not st.session_state.confirmed:
    if st.session_state.no_count >= 5:
        # 5번 연속 "아니요" 클릭 시
        st.write("❌ 앱을 찾을 수 없습니다. 앱 이름을 다시 확인해주세요.")
        st.session_state.disable_buttons = True
        st.session_state.search_results = [] 
        st.session_state.no_count = 0  
        st.session_state.search_index = 0  
        st.stop()

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
                st.session_state.no_count = 0 
                st.rerun()  

        with col2:
            if st.button("❌ 아니요, 다음 앱 보기", key="next_btn", disabled=disable_buttons):
                st.session_state.search_index += 1
                st.session_state.disable_buttons = False
                st.session_state.no_count += 1  
                st.rerun()  

# 리뷰 수집 및 분석
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

    # GPT 프롬프트 템플릿 설정
    prompt_template = """
    아래는 '{app_name}' 앱에 대한 실제 사용자 리뷰입니다:

    {reviews_text}

    이 리뷰들을 분석해서 아래 항목을 포함한 보고서를 작성해주세요:
    1. 주요 불만사항
    2. 긍정적 피드백
    3. 개선 제안

    [주의사항]
    1. 보고서 작성 후 추가 문의는 받지 않습니다. 추가 정보 제공과 관련된 답변은 제외해주세요.
    """

    # LangChain을 이용한 분석 프로세스 설정
    prompt = prompt_template.format(app_name=app_info['title'], reviews_text=reviews_text)
    
    # Prompt 템플릿과 LLMChain을 사용하여 분석 요청
    prompt_template = PromptTemplate(input_variables=["app_name", "reviews_text"], template=prompt_template)
    llm = ChatOpenAI(api_key=AZURE_OPENAI_KEY)
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # 분석 실행
    with st.spinner("AI 분석 중..."):
        report = chain.run(app_name=app_info['title'], reviews_text=reviews_text)

    # 결과 출력
    st.subheader("📝 분석 보고서")
    st.write(report)
