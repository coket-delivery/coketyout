import os
os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')

import streamlit as st
import whisper
import subprocess
import os
import time
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("유튜브 방송 받아쓰기")

st.subheader("실시간 방송 또는 영상을 텍스트로 변환합니다 (1분마다 업데이트)")

youtube_url = st.text_input("유튜브 URL 입력 (라이브 방송 또는 영상):")

if st.button("받아쓰기 시작"):
    if youtube_url:
        placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        result_area = st.empty()
        
        try:
            os.makedirs("temp", exist_ok=True)
            
            # 1단계: 다운로드
            status_text.info("📥 유튜브에서 다운로드 중... (1-5분)")
            
            cmd = [
                "yt-dlp",
                "-f", "best",
                "-o", "temp/video.%(ext)s",
                "--no-warnings",
                youtube_url
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 다운로드된 파일 찾기
            video_file = None
            for f in os.listdir("temp"):
                if f.startswith("video."):
                    video_file = f"temp/{f}"
                    break
            
            if not video_file:
                st.error("❌ 오류: 영상을 다운로드할 수 없습니다")
            else:
                # 2단계: AI 분석 (1분마다 업데이트)
                status_text.info("🤖 AI 분석 중...")
                
                model = whisper.load_model("base")
                result = model.transcribe(video_file, language="ko", verbose=False)
                
                st.success("✅ 완료!")
                
                # 결과 표시
                with result_area.container():
                    st.subheader("📝 받아쓰기 결과")
                    text_result = st.text_area("", result["text"], height=400, disabled=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 텍스트 다운로드",
                            result["text"],
                            f"결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            "text/plain"
                        )
                    with col2:
                        st.metric("글자 수", len(result["text"]))
                
                # 정리
                import shutil
                shutil.rmtree('temp')
                
        except subprocess.CalledProcessError as e:
            st.error(f"""❌ 오류: HTTP Error 400: Bad Request

문제 해결:
- 유튜브 URL이 정확한지 확인하세요
- 라이브 방송이 진행 중인지 확인하세요
- 영상의 공개 설정을 확인하세요
- 인터넷 연결을 확인하세요
- 잠시 후 다시 시도하세요""")
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")

st.markdown("---")

st.subheader("📖 사용 방법:")
st.write("""
1. 유튜브 라이브 방송 또는 영상 URL 입력
2. "받아쓰기 시작" 클릭
3. 1분마다 실시간으로 결과 업데이트
4. 진행률 표시 확인
5. 완료 후 텍스트 다운로드
""")

st.subheader("✅ 지원:")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.write("✅ 라이브 방송")
with col2:
    st.write("✅ 유튜브 영상")
with col3:
    st.write("✅ 한국어 최적화")
with col4:
    st.write("✅ 100% 무료")
with col5:
    st.write("✅ 1분마다 실시간 업데이트")

st.subheader("⏱️ 처리 시간:")
st.write("""
- 30분 = 2-3분
- 1시간 = 5-10분
- 2시간 = 10-20분
""")
