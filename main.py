import streamlit as st
import google.generativeai as genai
import os
from PIL import Image
from io import BytesIO

# 환경 설정 초기화
def init_settings():
    if 'gemini_api_key' not in st.session_state:
        st.session_state['gemini_api_key'] = ''
    if 'system_prompt' not in st.session_state:
        st.session_state['system_prompt'] = '당신은 친절한 챗봇입니다.'
    if 'selected_model' not in st.session_state:
        st.session_state['selected_model'] = 'gemini-pro' # gemini-pro-vision 으로 변경가능

# Gemini API 초기화
def init_gemini():
    if 'gemini_api_key' in st.session_state and st.session_state['gemini_api_key']:
        genai.configure(api_key=st.session_state['gemini_api_key'])
        return True
    else:
        st.warning("API 키를 먼저 설정해주세요.")
        return False

# 환경 설정 페이지
def settings_page():
    st.title("환경 설정")

    # API 키 입력
    api_key = st.text_input("Gemini API 키", type="password", value=st.session_state['gemini_api_key'])

    # 시스템 프롬프트 수정
    system_prompt = st.text_area("시스템 프롬프트", value=st.session_state['system_prompt'])

    # 모델 선택
    available_models = ['gemini-pro', 'gemini-pro-vision']
    selected_model = st.selectbox("모델 선택", options=available_models, index=available_models.index(st.session_state['selected_model']))

    if st.button("저장"):
        st.session_state['gemini_api_key'] = api_key
        st.session_state['system_prompt'] = system_prompt
        st.session_state['selected_model'] = selected_model
        st.success("저장되었습니다.")

# 챗봇 페이지
def chatbot_page():
    st.title("챗봇")
    if not init_gemini():
        return

    # 모델 선택
    model = genai.GenerativeModel(st.session_state['selected_model'])
    chat = model.start_chat(history=[]) # 이전 대화 기록을 위해 history 사용
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = [] # 이전 대화 기록 초기화

    # 파일 업로드
    uploaded_files = st.file_uploader("이미지 또는 PDF 파일을 업로드하세요.", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

    # 텍스트 입력창
    user_input = st.text_input("질문을 입력하세요.")

    if st.button("전송"):
        if user_input:
            contents = []
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.read()
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(BytesIO(file_bytes))
                        contents.append(image)
                    elif uploaded_file.type == 'application/pdf':
                        contents.append({"mime_type": "application/pdf", "data": file_bytes})
            contents.append(user_input)
            
            try:
                with st.spinner("답변 생성 중..."): # 로딩 표시
                    response = chat.send_message(contents)
                st.session_state['chat_history'].extend(chat.history) # 대화 기록 저장
                st.write(response.text)
            except Exception as e:
                st.error(f"오류 발생: {e}")
        else:
            st.warning("질문을 입력해주세요.")
    
    if 'chat_history' in st.session_state and st.session_state['chat_history']:
        st.subheader("대화 기록")
        for item in st.session_state['chat_history']:
          if 'parts' in item:
            for part in item['parts']:
                if hasattr(part, 'text'):
                  st.write(f"사용자: {part.text}")
                elif hasattr(part, 'data'):
                  st.write(f"파일")
          elif 'text' in item:
              st.write(f"봇: {item['text']}")


# 메인 함수
def main():
    st.set_page_config(page_title="Gemini 챗봇", page_icon=":robot:")
    init_settings()
    menu = ["설정", "챗봇"]
    choice = st.sidebar.selectbox("메뉴", menu)

    if choice == "설정":
        settings_page()
    elif choice == "챗봇":
        chatbot_page()

if __name__ == "__main__":
    main()