import streamlit as st
from anthropic import Anthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import tempfile
from PyPDF2 import PdfReader
import docx

# 페이지 설정
st.set_page_config(page_title="Claude RAG 챗봇", page_icon="🤖", layout="wide")

# 세션 상태 초기화
if "initialized" not in st.session_state:
    st.session_state.initialized = False
    st.session_state.messages = []
    st.session_state.vectorstore = None
    st.session_state.settings_confirmed = False

def initialize_settings():
    st.title("초기 설정 ⚙️")
    
    # API 키 설정
    api_key = st.text_input("Anthropic API 키를 입력하세요:", type="password")
    
    # 시스템 프롬프트 설정
    default_instruction = """You are a helpful AI assistant. Please provide accurate and helpful responses based on the given context."""
    system_prompt = st.text_area("시스템 프롬프트를 입력하세요:", value=default_instruction, height=150)
    
    # 파일 업로드
    uploaded_files = st.file_uploader("참고할 문서를 업로드하세요 (PDF, DOCX, TXT)", 
                                    accept_multiple_files=True,
                                    type=['pdf', 'docx', 'txt'])

    # 설정 확인 버튼
    if st.button("설정 완료"):
        if not api_key:
            st.error("API 키를 입력해주세요!")
            return
        
        if uploaded_files:
            with st.spinner("문서를 처리중입니다..."):
                texts = []
                for file in uploaded_files:
                    # 파일 확장자 확인
                    file_extension = os.path.splitext(file.name)[1].lower()
                    
                    # PDF 파일 처리
                    if file_extension == '.pdf':
                        pdf_reader = PdfReader(file)
                        for page in pdf_reader.pages:
                            texts.append(page.extract_text())
                    
                    # DOCX 파일 처리
                    elif file_extension == '.docx':
                        doc = docx.Document(file)
                        for para in doc.paragraphs:
                            texts.append(para.text)
                    
                    # TXT 파일 처리
                    elif file_extension == '.txt':
                        texts.append(file.read().decode('utf-8'))

                # 텍스트 분할
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                chunks = text_splitter.create_documents(texts)

                # 임베딩 및 벡터 저장소 생성
                embeddings = HuggingFaceEmbeddings(model_name="jhgan/ko-sbert-nli")
                vectorstore = FAISS.from_documents(chunks, embeddings)
                st.session_state.vectorstore = vectorstore

        # 세션 상태 저장
        st.session_state.anthropic_api_key = api_key
        st.session_state.system_prompt = system_prompt
        st.session_state.settings_confirmed = True
        st.session_state.initialized = True
        st.success("설정이 완료되었습니다!")
        st.rerun()

def chat_interface():
    st.title("Claude RAG 챗봇 💬")
    
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
            # RAG 컨텍스트 검색
            context = ""
            if st.session_state.vectorstore is not None:
                docs = st.session_state.vectorstore.similarity_search(prompt, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
                
            # Claude API 호출
            client = Anthropic(api_key=st.session_state.anthropic_api_key)
            
            # 시스템 프롬프트와 컨텍스트를 포함한 메시지 생성
            messages = [
                {"role": "system", "content": st.session_state.system_prompt},
                {"role": "user", "content": f"""Context: {context}\n\nQuestion: {prompt}
                Please provide an answer based on the given context. If the context doesn't contain relevant information,
                you can provide a general response."""}
            ]
            
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.7,
                messages=messages
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
        st.rerun()
    
    # 초기 설정 또는 채팅 인터페이스 표시
    if not st.session_state.settings_confirmed:
        initialize_settings()
    else:
        chat_interface()

if __name__ == "__main__":
    main()