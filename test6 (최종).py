# 실제 구글 플레이스토어에서 리뷰를 수집하여 취합 및 개선안 제안
# Streamlit 배포 (사용성 개선)
# langchin 적용
# https://ktds-mvp-jhn9u67fzk7mbrumwmlzct.streamlit.app/

import time
import streamlit as st
import re
from dotenv import load_dotenv
from google_play_scraper import search, reviews, Sort

from langchain.prompts import PromptTemplate
from langchain_community.chat_models import AzureChatOpenAI
from langchain.chains import LLMChain

load_dotenv()

AZURE_OPENAI_KEY = st.secrets["AZURE_OPENAI_KEY"]
AZURE_OPENAI_ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]

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

# 사용자에게 앱 이름 받기
col1, col2 = st.columns([3, 1])

with col1:
    app_name = st.text_input("리뷰를 보고 싶은 앱 이름을 입력하세요", key="app_name_input", value=st.session_state.app_name)
with col2:
    search_button = st.button("검색", key="search_btn")

# 앱 이름 변경 시 세션 초기화 및 검색
if app_name != st.session_state.app_name:
    st.session_state.app_name = app_name
    st.session_state.search_index = 0
    st.session_state.search_results = []
    st.session_state.confirmed = False
    st.session_state.disable_buttons = False
    st.session_state.no_count = 0

    if app_name:
        with st.spinner("앱 정보를 불러오는 중..."):
            st.session_state.search_results = search(app_name, lang="ko", country="kr")

# 검색 버튼 클릭 시
if search_button and app_name:
    if not st.session_state.search_results:
        with st.spinner("앱 정보를 불러오는 중..."):
            st.session_state.search_results = search(app_name, lang="ko", country="kr")

# 앱 후보 확인
if st.session_state.search_results and not st.session_state.confirmed:
    if st.session_state.no_count >= 5:
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

    # GPT 프롬프트
    prompt_template_str = """
    아래는 '{app_name}' 앱에 대한 실제 사용자 리뷰입니다:

    {reviews_text}

    이 리뷰들을 분석해서 아래 항목을 포함한 보고서를 작성해주세요:
    1. 주요 불만사항
    2. 긍정적 피드백
    3. 개선 제안

    [주의사항]
    1. 보고서 작성 후 추가 문의는 받지 않습니다. 추가 정보 제공과 관련된 답변은 제외해주세요.
    """

    prompt_template = PromptTemplate(
        input_variables=["app_name", "reviews_text"],
        template=prompt_template_str
    )

    # Azure OpenAI LLM 설정
    llm = AzureChatOpenAI(
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        openai_api_key=AZURE_OPENAI_KEY,
        openai_api_version="2025-01-01-preview",
        temperature=0.7,
        max_tokens=1000,
    )


    chain = LLMChain(llm=llm, prompt=prompt_template)

    with st.spinner("AI 분석 중..."):
        report = chain.run(app_name=app_info['title'], reviews_text=reviews_text)

    st.subheader("📝 분석 보고서")    
    
    content_dict = {}
    pattern = re.compile(r'^#+\s*\d+\.\s+.*')
    current_title = None
    
    for line in report.split('\n'):
        stripped = line.strip()
        if pattern.match(stripped):
            current_title = stripped.replace("###", "").strip()
            content_dict[current_title] = []
        elif current_title:
            content_dict[current_title].append(line)
    
    # 출력
    if content_dict:
        for title, contents in content_dict.items():
            st.markdown(f"### {title}")  # 제목 크고 굵게
            st.write("\n".join(contents).strip())
    else:
        st.warning("보고서를 분석할 수 없습니다. 출력 형식을 다시 확인하세요.")



