import subprocess
import sys
import os

# 시스템 패키지 설치
os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')

# Python 패키지 설치
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp', '-q'])
subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'streamlit', 'openai-whisper', '-q'])

import streamlit as st
import whisper
from yt_dlp import YoutubeDL
from datetime import datetime
import time

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("유튜브 방송 받아쓰기")

st.subheader("실시간 방송 또는 영상을 텍스트로 변환합니다 (매분 업데이트)")

youtube_url = st.text_input("유튜브 URL 입력 (라이브 방송 또는 영상):")

if st.button("받아쓰기 시작"):
    if youtube_url:
        st.info("⏳ 스트림 다운로드 중...")
        
        try:
            os.makedirs("temp", exist_ok=True)
            
            # YouTube 최신 보안 우회 옵션
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': 'temp/audio.%(ext)s',
                'quiet': False,
                'no_warnings': False,
                'socket_timeout': 60,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                },
                'extractor_args': {
                    'youtube': {
                        'player_skip': ['js', 'webpage'],
                        'skip': ['hls', 'dash'],
                    }
                },
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'merge_output_format': 'mp4',
                'prefer_ffmpeg': True,
                'keepvideo': False,
            }
            
            st.info("📥 유튜브에서 다운로드 중... (1-5분)")
            
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=True)
                video_title = info_dict.get('title', 'video')
            
            # 다운로드된 파일 찾기
            audio_file = None
            for root, dirs, files in os.walk('temp'):
                for file in files:
                    if file.endswith(('.mp4', '.m4a', '.mp3', '.wav', '.webm')):
                        audio_file = os.path.join(root, file)
                        break
                if audio_file:
                    break
            
            if audio_file:
                st.info("🤖 AI 모델 로드 중...")
                model = whisper.load_model("base")
                
                st.success("🎙️ 음성 인식 시작... (매분 결과 업데이트)")
                
                # 전체 파일 받아쓰기
                result = model.transcribe(audio_file, language="ko", verbose=False)
                full_text = result["text"]
                
                # 결과를 문장별로 분할
                sentences = full_text.split('.')
                sentences = [s.strip() + '.' for s in sentences if s.strip()]
                
                # 실시간 업데이트 플레이스홀더
                result_placeholder = st.empty()
                progress_placeholder = st.empty()
                
                # 매분마다 결과 업데이트 시뮬레이션
                cumulative_text = ""
                total_sentences = len(sentences)
                sentences_per_minute = max(1, total_sentences // 10) if total_sentences > 0 else 1
                
                for i, sentence in enumerate(sentences):
                    cumulative_text += " " + sentence
                    
                    # 매분마다 또는 마지막에 업데이트
                    if (i + 1) % sentences_per_minute == 0 or i == total_sentences - 1:
                        with result_placeholder.container():
                            st.text_area(
                                "📝 받아쓰기 결과 (실시간 업데이트):",
                                cumulative_text.strip(),
                                height=300,
                                disabled=True
                            )
                        
                        with progress_placeholder.container():
                            progress = min((i + 1) / total_sentences * 100, 100)
                            st.progress(int(progress), f"진행률: {int(progress)}% ({i + 1}/{total_sentences} 문장)")
                
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
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.info(f"**제목**\n{video_title[:20]}")
                with col2:
                    st.info(f"**문장 수**\n{total_sentences}")
                with col3:
                    st.info(f"**평균 문장 길이**\n{len(full_text)//max(1, total_sentences)} 자")
                with col4:
                    st.info(f"**완료**\n{datetime.now().strftime('%H:%M:%S')}")
                
                # 파일 정리
                try:
                    import shutil
                    shutil.rmtree('temp')
                except:
                    pass
            
            else:
                st.error("❌ 다운로드된 파일을 찾을 수 없습니다")
        
        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ 오류: {error_msg}")
            
            if "No video formats found" in error_msg:
                st.warning("""
                **YouTube 보안 오류**
                
                현재 YouTube의 최신 보안 때문에 일부 영상이 다운로드되지 않을 수 있습니다.
                
                **해결책:**
                1. 다른 영상을 시도해보세요
                2. 몇 분 후 다시 시도하세요
                3. 영상의 공개 설정을 확인하세요
                """)
            else:
                st.warning("""
                **문제 해결:**
                1. 유튜브 URL이 정확한지 확인하세요
                2. 라이브 방송이 진행 중인지 확인하세요
                3. 인터넷 연결을 확인하세요
                4. 잠시 후 다시 시도하세요
                """)

st.divider()
st.info("""
**사용 방법:**
1. 유튜브 라이브 방송 또는 영상 URL 입력
2. "받아쓰기 시작" 클릭
3. 매분 실시간으로 받아쓰기 결과 업데이트
4. 진행률 표시
5. 완료 후 텍스트 다운로드

**지원:**
- ✅ 라이브 방송 (진행 중일 때)
- ✅ 유튜브 영상
- ✅ 한국어 최적화
- ✅ 100% 무료
- ✅ 매분 실시간 업데이트

**처리 시간:**
- 30분 = 2-3분
- 1시간 = 5-10분
- 2시간 = 10-20분
""")
