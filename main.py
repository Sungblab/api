import streamlit as st
from anthropic import Anthropic

# 페이지 설정
st.set_page_config(page_title="Claude 챗봇", page_icon="🤖", layout="wide")

# 세션 상태 초기화
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.messages = []
    st.session_state.settings_confirmed = False

def initialize_settings():
    st.title("초기 설정 ⚙️")
    
    # API 키 설정
    api_key = st.text_input("Anthropic API 키를 입력하세요:", type="password")
    
    # 시스템 프롬프트 설정
    default_instruction = """You are a helpful AI assistant. Please provide accurate and helpful responses."""
    system_prompt = st.text_area("시스템 프롬프트를 입력하세요:", value=default_instruction, height=150)
    
    # 파일 업로드
    uploaded_file = st.file_uploader("참고할 문서를 업로드하세요", type=['pdf'])

    # 설정 확인 버튼
    if st.button("설정 완료"):
        if not api_key:
            st.error("API 키를 입력해주세요!")
            return
        
        # 세션 상태 저장
        st.session_state.anthropic_api_key = api_key
        st.session_state.system_prompt = system_prompt
        if uploaded_file:
            st.session_state.uploaded_file = uploaded_file.read()
        st.session_state.settings_confirmed = True
        st.session_state.initialized = True
        st.success("설정이 완료되었습니다!")
        st.rerun()

def chat_interface():
    st.title("Claude 챗봇 💬")
    
    # 채팅 기록 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # 사용자 입력
    if prompt := st.chat_input("메시지를 입력하세요"):
        # 사용자 메시지 표시
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            client = Anthropic(api_key=st.session_state.anthropic_api_key)
            
            messages = [{"role": "system", "content": st.session_state.system_prompt}]
            
            # 파일이 업로드된 경우 첨부
            if hasattr(st.session_state, 'uploaded_file'):
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.7,
                    messages=messages + [{"role": "user", "content": prompt}],
                    files=[
                        {
                            "file": st.session_state.uploaded_file,
                            "file_name": "document.pdf",
                            "file_type": "application/pdf"
                        }
                    ]
                )
            else:
                response = client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    temperature=0.7,
                    messages=messages + [{"role": "user", "content": prompt}]
                )
            
            # 응답 표시
            with st.chat_message("assistant"):
                st.markdown(response.content)
            st.session_state.messages.append({"role": "assistant", "content": response.content})
            
        except Exception as e:
            st.error(f"에러가 발생했습니다: {str(e)}")

# 메인 앱 로직
def main():
    # 사이드바에 설정 초기화 버튼
    if st.sidebar.button("설정 초기화"):
        st.session_state.initialized = False
        st.session_state.settings_confirmed = False
        st.session_state.messages = []
        if hasattr(st.session_state, 'uploaded_file'):
            del st.session_state.uploaded_file
        st.rerun()
    
    # 초기 설정 또는 채팅 인터페이스 표시
    if not st.session_state.settings_confirmed:
        initialize_settings()
    else:
        chat_interface()

if __name__ == "__main__":
    main()