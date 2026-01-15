import os
import streamlit as st
from datetime import datetime
import shutil
import time

os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("방송 받아쓰기")

st.subheader("영상을 텍스트로 변환합니다")

st.write("✅ 컴퓨터에서 영상 파일 선택 후 받아쓰기")

uploaded_file = st.file_uploader(
    "📁 영상 파일 선택",
    type=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "m4a"]
)

if uploaded_file is not None:
    st.info(f"📂 선택된 파일: {uploaded_file.name}")
    
    if st.button("🎤 받아쓰기 시작"):
        os.makedirs("temp", exist_ok=True)
        
        try:
            # 파일 저장
            file_path = f"temp/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success("✅ 파일 저장 완료")
            
            # 상태 표시
            status_area = st.empty()
            progress_area = st.empty()
            result_area = st.empty()
            
            status_area.info("🤖 Whisper 모델 로드 중...")
            
            import whisper
            
            model = whisper.load_model("base")
            status_area.info("🎯 분석 중... (1-10분 소요)")
            
            start_time = time.time()
            
            # 진행 상황
            with progress_area.container():
                col1, col2, col3 = st.columns(3)
                progress_ph = col1.empty()
                time_ph = col2.empty()
                status_ph = col3.empty()
            
            # 분석
            analysis_result = model.transcribe(
                file_path,
                language="ko",
                verbose=False
            )
            
            text_result = analysis_result["text"]
            elapsed_time = int(time.time() - start_time)
            
            # 결과 표시
            progress_ph.progress(100)
            time_ph.metric("⏱️ 시간", f"{elapsed_time}초")
            status_ph.success("✅ 완료")
            
            # 텍스트 표시
            with result_area.container():
                st.subheader("📝 받아쓰기 결과")
                st.text_area(
                    "텍스트:",
                    text_result,
                    height=400,
                    disabled=True
                )
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.download_button(
                        "📥 다운로드",
                        text_result,
                        f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        "text/plain"
                    )
                
                with col2:
                    st.metric("글자", len(text_result))
                
                with col3:
                    st.metric("단어", len(text_result.split()))
                
                with col4:
                    st.metric("시간", f"{elapsed_time}초")
            
            status_area.success("✅ 완료!")
        
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
        
        finally:
            if os.path.exists("temp"):
                shutil.rmtree('temp')

st.markdown("---")

st.subheader("📖 사용 방법:")
st.markdown("""
1. 파일 선택
2. "받아쓰기 시작" 클릭
3. 분석 대기 (1-10분)
4. 결과 다운로드
""")

st.subheader("✅ 지원:")
st.write("✅ MP4, AVI, MOV, MKV, WEBM")
st.write("✅ MP3, WAV, M4A")
st.write("✅ 한국어")

st.subheader("⏱️ 시간:")
st.markdown("""
| 길이 | 시간 |
|------|-----|
| 30분 | 2-3분 |
| 1시간 | 5-10분 |
""")

st.caption("🔒 모든 파일은 처리 후 삭제됩니다")
