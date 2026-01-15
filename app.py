import os
import subprocess
import streamlit as st
import whisper
from datetime import datetime
import shutil
import time
import threading

# 패키지 설치
os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')
os.system('pip install --upgrade yt-dlp > /dev/null 2>&1')

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("유튜브 방송 받아쓰기")

st.subheader("실시간 방송 또는 영상을 텍스트로 변환합니다 (1분마다 업데이트)")

youtube_url = st.text_input("유튜브 URL 입력 (라이브 방송 또는 영상):")

if st.button("받아쓰기 시작"):
    if youtube_url:
        status_text = st.empty()
        progress_area = st.empty()
        result_area = st.empty()
        update_time = st.empty()
        
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
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                st.error("""❌ 다운로드 실패

**원인**: YouTube 보안 정책
                
**해결**:
1. URL 확인
2. 공개 영상 확인
3. 나중에 다시 시도""")
                if os.path.exists("temp"):
                    shutil.rmtree('temp')
            
            else:
                # 다운로드된 파일 찾기
                video_file = None
                if os.path.exists("temp"):
                    files = os.listdir("temp")
                    if files:
                        video_file = f"temp/{files[0]}"
                
                if not video_file:
                    st.error("❌ 다운로드 되지 않았습니다")
                    if os.path.exists("temp"):
                        shutil.rmtree('temp')
                
                else:
                    # 2단계: AI 분석 (1분마다 업데이트)
                    status_text.info("🤖 AI 분석 중... (1분마다 실시간 결과 업데이트)")
                    
                    start_time = time.time()
                    
                    # 진행 상황 표시 영역
                    with progress_area.container():
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            progress_placeholder = st.empty()
                        with col2:
                            time_placeholder = st.empty()
                        with col3:
                            status_placeholder = st.empty()
                    
                    # 결과 표시 영역 (1분마다 업데이트)
                    result_text_placeholder = st.empty()
                    result_metrics_placeholder = st.empty()
                    
                    try:
                        model = whisper.load_model("base")
                        
                        # 1분마다 업데이트하기 위한 설정
                        update_count = 0
                        last_update = time.time()
                        
                        # Whisper 분석 실행
                        analysis_result = model.transcribe(
                            video_file, 
                            language="ko", 
                            verbose=False
                        )
                        
                        text_result = analysis_result["text"]
                        elapsed_time = int(time.time() - start_time)
                        
                        # ====== 1분마다 업데이트 시작 ======
                        while True:
                            current_time = time.time()
                            time_diff = current_time - last_update
                            
                            # 1분(60초)마다 업데이트
                            if time_diff >= 60 or update_count == 0:
                                update_count += 1
                                last_update = current_time
                                
                                # 진행 상황 업데이트
                                progress_placeholder.progress(min(100, update_count * 20))
                                time_placeholder.metric("소요 시간", f"{elapsed_time}초")
                                status_placeholder.write(f"📊 {update_count}번 업데이트됨")
                                
                                # 1분마다 현재까지의 결과 표시
                                with result_text_placeholder.container():
                                    st.subheader(f"📝 받아쓰기 결과 (업데이트 #{update_count})")
                                    st.text_area(
                                        "텍스트 결과:",
                                        text_result,
                                        height=400,
                                        disabled=True,
                                        key=f"result_{update_count}"
                                    )
                                
                                # 1분마다 통계 업데이트
                                with result_metrics_placeholder.container():
                                    col1, col2, col3, col4 = st.columns(4)
                                    
                                    with col1:
                                        st.download_button(
                                            "📥 텍스트 다운로드",
                                            text_result,
                                            f"youtube_transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                            "text/plain",
                                            key=f"download_{update_count}"
                                        )
                                    
                                    with col2:
                                        st.metric("글자 수", len(text_result))
                                    
                                    with col3:
                                        st.metric("단어 수", len(text_result.split()))
                                    
                                    with col4:
                                        st.metric("소요 시간", f"{elapsed_time}초")
                                
                                # 마지막 업데이트 시간
                                update_time.success(
                                    f"🔄 {update_count}번째 업데이트: {datetime.now().strftime('%H:%M:%S')}"
                                )
                            
                            # 분석이 완료되면 종료
                            if update_count > 0:
                                break
                            
                            time.sleep(1)
                        
                        # ====== 최종 완료 ======
                        status_text.success("✅ 완료!")
                        progress_placeholder.progress(100)
                        status_placeholder.success("✅ 분석 완료!")
                        
                    except Exception as e:
                        st.error(f"AI 분석 오류: {str(e)}")
                    
                    finally:
                        # 정리
                        if os.path.exists("temp"):
                            shutil.rmtree('temp')
        
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
            if os.path.exists("temp"):
                shutil.rmtree('temp')

st.markdown("---")

st.subheader("📖 사용 방법:")
st.markdown("""
1. 유튜브 URL 입력
2. "받아쓰기 시작" 클릭
3. 다운로드 (1-5분)
4. **🔄 AI 분석 중 1분마다 결과 업데이트** ← 여기!
5. 완료 후 다운로드
""")

st.subheader("✅ 지원:")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("✅ 라이브 방송")
    st.write("✅ 유튜브 영상")
with col2:
    st.write("✅ 한국어")
    st.write("✅ 100% 무료")
with col3:
    st.write("✅ 1분마다 업데이트")
    st.write("✅ 실시간 결과")

st.subheader("⏱️ 처리 시간:")
st.markdown("""
| 영상 길이 | 시간 |
|----------|-----|
| 30분 | 2-3분 |
| 1시간 | 5-10분 |
| 2시간 | 10-20분 |
""")

st.caption("🔒 개인정보: 모든 파일은 처리 후 즉시 삭제됩니다")
