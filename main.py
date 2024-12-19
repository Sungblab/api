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

# 사용 가능한 모델 목록
MODELS = {
    "Gemini 1.5 Flash": "gemini-1.5-flash",
    "Gemini 1.5 Pro": "gemini-1.5-pro"
}

def load_config():
    """설정 파일 로드"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "api_key": "",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "selected_model": "gemini-1.5-flash"
    }

def save_config(api_key, system_prompt, selected_model):
    """설정 파일 저장"""
    config = {
        "api_key": api_key,
        "system_prompt": system_prompt,
        "selected_model": selected_model
    }
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
    
    # 모델 선택
    selected_model = st.selectbox(
        "사용할 모델",
        options=list(MODELS.keys()),
        index=list(MODELS.values()).index(config["selected_model"]),
        help="Flash: 빠른 응답, Pro: 고성능"
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
        save_config(api_key, system_prompt, MODELS[selected_model])
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
        model = genai.GenerativeModel(config["selected_model"])
        
        st.title("Gemini 챗봇")
        
        # 현재 사용 중인 모델 표시
        st.info(f"현재 모델: {[k for k, v in MODELS.items() if v == config['selected_model']][0]}")
        
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
        
        # 채팅 히스토리 표시
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # 사용자 입력 처리
        if prompt := st.chat_input("메시지를 입력하세요"):
            # 사용자 메시지 표시 및 저장
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            try:
                # 시스템 프롬프트 포함하여 메시지 생성
                messages = [{
                    "parts": [config["system_prompt"]],
                    "role": "user"
                }]
                
                # 이전 대화 기록 추가
                for msg in st.session_state.messages:
                    messages.append({
                        "parts": [msg["content"]],
                        "role": "model" if msg["role"] == "assistant" else "user"
                    })
                
                # 이미지가 있는 경우
                if uploaded_file:
                    response = model.generate_content([prompt, image])
                else:
                    chat = model.start_chat(history=messages)
                    response = chat.send_message(prompt)
                
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