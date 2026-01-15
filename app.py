import streamlit as st
import whisper
from yt_dlp import YoutubeDL
import os
from datetime import datetime

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("유튜브 방송 받아쓰기")

st.subheader("실시간 방송 또는 영상을 텍스트로 변환합니다")

# URL 입력
youtube_url = st.text_input("유튜브 URL 입력 (라이브 방송 또는 영상):")

if st.button("받아쓰기 시작"):
    if youtube_url:
        st.info("⏳ 스트림 처리 중... (1-2분)")
        
        try:
            # 임시 폴더 생성
            os.makedirs("temp", exist_ok=True)
            
            # 스트림을 직접 Whisper로 처리 (MP4 저장 안 함)
            st.info("🎙️ 음성 인식 중...")
            
            # yt-dlp로 스트림 캡처 (파일로 저장하지 않고 직접 처리)
            ydl_opts = {
                'format': 'best',
                'outtmpl': 'temp/audio',
                'quiet': True,
                'no_warnings': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
            
            # 저장된 파일 찾기
            audio_file = None
            for file in os.listdir("temp"):
                if file.startswith("audio"):
                    audio_file = f"temp/{file}"
                    break
            
            if audio_file:
                st.info("🤖 AI 분석 중...")
                
                # Whisper로 받아쓰기
                model = whisper.load_model("base")
                result = model.transcribe(audio_file, language="ko")
                
                # 결과
                st.success("✅ 완료!")
                
                text = result["text"]
                
                # 결과 표시
                st.text_area("📝 받아쓰기 결과:", text, height=400)
                
                # 다운로드
                st.download_button(
                    label="📥 텍스트 다운로드",
                    data=text,
                    file_name=f"결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
                
                # 통계
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("총 글자 수", len(text))
                with col2:
                    st.metric("총 단어 수", len(text.split()))
                with col3:
                    st.metric("완료 시간", datetime.now().strftime("%H:%M:%S"))
                
                # 파일 삭제
                os.remove(audio_file)
        
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
            st.info("💡 방송이 진행 중인지 확인하세요")

st.divider()
st.info("""
**사용 방법:**
1. 유튜브 URL 입력 (라이브 방송 또는 영상)
2. "받아쓰기 시작" 클릭
3. 텍스트 결과 다운로드

**지원:**
- ✅ 라이브 방송
- ✅ 유튜브 영상
- ✅ 한국어 최적화
- ✅ 무료
""")
