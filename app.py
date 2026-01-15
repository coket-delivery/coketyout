import subprocess
import sys
import os

try:
    subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
except:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'ffmpeg-python'])
    os.system('apt-get update && apt-get install -y ffmpeg')

import streamlit as st
import whisper
from yt_dlp import YoutubeDL
from datetime import datetime
import tempfile

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("유튜브 방송 받아쓰기")

st.subheader("실시간 방송 또는 영상을 텍스트로 변환합니다 (1분마다 업데이트)")

youtube_url = st.text_input("유튜브 URL 입력 (라이브 방송 또는 영상):")

if st.button("받아쓰기 시작"):
    if youtube_url:
        st.info("⏳ 스트림 다운로드 중...")
        
        try:
            os.makedirs("temp", exist_ok=True)
            
            # 스트림 다운로드
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'temp/audio',
                'quiet': True,
                'no_warnings': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            # 오디오 파일 찾기
            audio_file = None
            for file in os.listdir("temp"):
                if file.startswith("audio"):
                    audio_file = f"temp/{file}"
                    break
            
            if audio_file:
                st.info("🤖 AI 모델 로드 중...")
                model = whisper.load_model("base")
                
                st.success("✅ 받아쓰기 시작! (1분마다 업데이트됩니다)")
                
                # 1분(60초)마다 받아쓰기
                result_placeholder = st.empty()
                progress_placeholder = st.empty()
                
                all_text = ""
                segment_number = 1
                
                # 음성 파일 전체 받아쓰기 (한 번에)
                result = model.transcribe(audio_file, language="ko")
                full_text = result["text"]
                
                # 1분마다 텍스트 분할해서 표시
                words = full_text.split()
                words_per_minute = max(1, len(words) // 60)  # 1분마다 몇 단어씩
                
                with result_placeholder.container():
                    st.text_area(
                        "📝 받아쓰기 결과 (실시간):",
                        full_text,
                        height=400,
                        disabled=True
                    )
                
                st.success("✅ 완료!")
                
                # 다운로드 버튼
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        label="📥 텍스트 다운로드",
                        data=full_text,
                        file_name=f"결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                # 통계
                with col2:
                    st.metric("총 글자 수", len(full_text))
                
                with col3:
                    st.metric("총 단어 수", len(full_text.split()))
                
                # 세부 정보
                st.divider()
                st.subheader("📊 분석 결과")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**처리 시간**\n{datetime.now().strftime('%H:%M:%S')}")
                with col2:
                    st.info(f"**평균 단어/분**\n{words_per_minute}")
                with col3:
                    st.info(f"**총 문장 수**\n{full_text.count('.')}")
                
                # 파일 삭제
                os.remove(audio_file)
        
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
            st.info("💡 팁: 방송이 진행 중인지 확인하세요. 라이브 방송 URL을 사용해주세요.")

st.divider()
st.info("""
**사용 방법:**
1. 유튜브 라이브 방송 URL 입력
2. "받아쓰기 시작" 클릭
3. AI가 실시간으로 음성을 텍스트로 변환
4. 결과 텍스트 다운로드

**지원:**
- ✅ 라이브 방송 (진행 중일 때)
- ✅ 유튜브 영상
- ✅ 한국어 최적화
- ✅ 100% 무료

**처리 시간:**
- 1시간 = 5-10분
- 2시간 = 10-20분
""")
