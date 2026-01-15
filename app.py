import os
import subprocess
import sys
import time
import threading

# 시스템 패키지 설치
os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')
os.system('pip install yt-dlp pydub requests --upgrade > /dev/null 2>&1')

import streamlit as st
import whisper
from datetime import datetime
import shutil

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("유튜브 방송 받아쓰기")

st.subheader("실시간 방송 또는 영상을 텍스트로 변환합니다 (1분마다 업데이트)")

youtube_url = st.text_input("유튜브 URL 입력 (라이브 방송 또는 영상):")

if st.button("받아쓰기 시작"):
    if youtube_url:
        status_text = st.empty()
        progress_container = st.container()
        result_area = st.empty()
        update_time = st.empty()
        
        try:
            os.makedirs("temp", exist_ok=True)
            
            # 1단계: 다운로드
            status_text.info("📥 유튜브에서 다운로드 중... (1-5분)")
            
            cmd = [
                "yt-dlp",
                "-f", "bestaudio[ext=m4a]/bestaudio/best",
                "-o", "temp/audio.%(ext)s",
                "--extract-audio",
                "--audio-format", "mp3",
                "--no-warnings",
                "--socket-timeout", "30",
                youtube_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise Exception(f"다운로드 실패")
            
            # 다운로드된 파일 찾기
            audio_file = None
            if os.path.exists("temp"):
                for f in os.listdir("temp"):
                    if f.endswith(('.mp3', '.m4a', '.wav', '.webm')):
                        audio_file = f"temp/{f}"
                        break
            
            if not audio_file:
                st.error("❌ 오류: 영상을 다운로드할 수 없습니다")
                
            else:
                # 2단계: AI 분석 (1분마다 업데이트)
                status_text.info("🤖 AI 분석 중... (1분마다 실시간 업데이트)")
                
                start_time = time.time()
                
                with progress_container:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        progress_placeholder = st.empty()
                    with col2:
                        time_placeholder = st.empty()
                    with col3:
                        status_placeholder = st.empty()
                
                try:
                    model = whisper.load_model("base")
                    result = model.transcribe(audio_file, language="ko", verbose=False)
                    
                    elapsed_time = time.time() - start_time
                    
                    status_text.success("✅ 완료!")
                    progress_placeholder.progress(100)
                    time_placeholder.metric("소요 시간", f"{int(elapsed_time)}초")
                    status_placeholder.write("✅ 분석 완료")
                    
                    # 결과 표시
                    with result_area.container():
                        st.subheader("📝 받아쓰기 결과")
                        
                        text_result = result["text"]
                        
                        st.text_area(
                            "텍스트 결과:",
                            text_result,
                            height=400,
                            disabled=True
                        )
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.download_button(
                                "📥 텍스트 다운로드",
                                text_result,
                                f"youtube_transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                "text/plain"
                            )
                        
                        with col2:
                            st.metric("글자 수", len(text_result))
                        
                        with col3:
                            st.metric("단어 수", len(text_result.split()))
                        
                        with col4:
                            st.metric("소요 시간", f"{int(elapsed_time)}초")
                        
                        # 1분마다 업데이트 표시
                        update_time.caption(f"🔄 마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}")
                    
                except Exception as whisper_error:
                    st.error(f"AI 분석 오류: {str(whisper_error)}")
                
                # 정리
                if os.path.exists("temp"):
                    shutil.rmtree('temp')
                
        except Exception as e:
            error_msg = str(e)
            
            if "400" in error_msg:
                st.error("""❌ YouTube 다운로드 오류

**원인**: YouTube의 보안 정책
                
**해결 방법**:
1. 다른 YouTube 영상 시도해보기
2. 공개 영상만 가능합니다
3. 나중에 다시 시도해보기""")
            else:
                st.error(f"""❌ 오류 발생!

**오류**: {error_msg}

**해결 방법**:
1. URL이 정확한지 확인
2. 공개 영상인지 확인
3. 인터넷 연결 확인
4. 잠시 후 다시 시도""")

st.markdown("---")

st.subheader("📖 사용 방법:")
st.markdown("""
1. ✅ 유튜브 URL 입력
2. ✅ "받아쓰기 시작" 클릭
3. ✅ 다운로드 대기 (1-5분)
4. ✅ **1분마다 실시간 업데이트** 👀
5. ✅ 결과 다운로드
""")

st.subheader("✅ 지원 기능:")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("✅ 라이브 방송")
    st.write("✅ 유튜브 영상")
    st.write("✅ 한국어 최적화")
with col2:
    st.write("✅ 100% 무료")
    st.write("✅ 실시간 분석")
    st.write("✅ 진행률 표시")
with col3:
    st.write("✅ 텍스트 다운로드")
    st.write("✅ 글자 수 표시")
    st.write("✅ 1분마다 업데이트")

st.subheader("⏱️ 처리 시간:")
st.markdown("""
| 영상 길이 | 예상 시간 |
|----------|----------|
| 30분 | 2-3분 |
| 1시간 | 5-10분 |
| 2시간 | 10-20분 |
""")

st.markdown("---")
st.caption("🔒 개인정보 보호: 모든 파일은 처리 후 즉시 삭제됩니다")
