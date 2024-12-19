import streamlit as st
import os
import json
from pathlib import Path

# 설정 파일 경로
CONFIG_PATH = Path("config.json")

# 기본 시스템 프롬프트
DEFAULT_SYSTEM_PROMPT = """당신은 유용한 AI 어시스턴트입니다. 
사용자의 질문에 정확하고 도움이 되는 답변을 제공합니다.
부적절하거나 유해한 내용은 답변하지 않습니다."""

def load_config():
    """설정 파일 로드"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"api_key": "", "system_prompt": DEFAULT_SYSTEM_PROMPT}

def save_config(api_key, system_prompt):
    """설정 파일 저장"""
    config = {"api_key": api_key, "system_prompt": system_prompt}
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 페이지 설정
st.set_page_config(page_title="Gemini 챗봇", layout="wide")

# 세션 상태 초기화
if "page" not in st.session_state:
    st.session_state.page = "settings"

# 네비게이션
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("⚙️ 설정"):
        st.session_state.page = "settings"
with col2:
    if st.button("💬 채팅"):
        st.session_state.page = "chat"

# 설정 페이지
if st.session_state.page == "settings":
    st.title("설정")
    
    # 현재 설정 로드
    config = load_config()
    
    # API 키 입력
    api_key = st.text_input(
        "Gemini API 키",
        value=config["api_key"],
        type="password",
        help="Google AI Studio에서 발급받은 API 키를 입력하세요"
    )
    
    # 시스템 프롬프트 입력
    system_prompt = st.text_area(
        "시스템 프롬프트",
        value=config["system_prompt"],
        height=200,
        help="AI의 기본 행동과 응답 방식을 설정하는 프롬프트입니다"
    )
    
    # 저장 버튼
    if st.button("설정 저장"):
        save_config(api_key, system_prompt)
        st.success("설정이 저장되었습니다!")
        
# 채팅 페이지
elif st.session_state.page == "chat":
    import google.generativeai as genai
    from PIL import Image
    
    # 설정 로드
    config = load_config()
    
    if not config["api_key"]:
        st.error("API 키가 설정되지 않았습니다. 설정 페이지에서 API 키를 입력해주세요.")
    else:
        # Gemini 설정
        genai.configure(api_key=config["api_key"])
        model = genai.GenerativeModel("gemini-1.5-pro")
        
        st.title("Gemini 챗봇")
        
        # 사이드바에 파일 업로드
        with st.sidebar:
            st.header("파일 업로드")
            uploaded_file = st.file_uploader(
                "이미지 파일을 업로드하세요",
                type=['png', 'jpg', 'jpeg']
            )
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                st.image(image, caption="업로드된 이미지")
        
        # 채팅 히스토리 초기화
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # 시스템 프롬프트 추가
            st.session_state.messages.append({
                "role": "assistant",
                "content": "안녕하세요! 무엇을 도와드릴까요?"
            })
        
        # 채팅 히스토리 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # 사용자 입력 처리
        if prompt := st.chat_input("메시지를 입력하세요"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            try:
                # 이미지가 있는 경우와 없는 경우 분리
                if uploaded_file:
                    response = model.generate_content([
                        config["system_prompt"],
                        {"role": "user", "content": prompt},
                        image
                    ])
                else:
                    response = model.generate_content([
                        config["system_prompt"],
                        {"role": "user", "content": prompt}
                    ])
                
                # 응답 표시 및 저장
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.text
                })
                with st.chat_message("assistant"):
                    st.write(response.text)
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
        
        # 채팅 초기화 버튼
        if st.button("대화 초기화"):
            st.session_state.messages = []
            st.experimental_rerun()