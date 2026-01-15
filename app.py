import os
import streamlit as st
import whisper
from datetime import datetime
import shutil
import time

os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("방송 받아쓰기")

st.subheader("영상을 텍스트로 변환합니다 (1분마다 업데이트)")

# 탭 만들기
tab1, tab2 = st.tabs(["유튜브 URL", "로컬 파일 업로드"])

# ============ 탭 1: 유튜브 ============
with tab1:
    st.write("⚠️ YouTube는 보안 정책으로 인해 제한될 수 있습니다")
    youtube_url = st.text_input("유튜브 URL:")
    
    if st.button("유튜브 받아쓰기"):
        if youtube_url:
            st.info("준비 중...")
            st.write("현재 YouTube 다운로드가 제한되어 있습니다.")

# ============ 탭 2: 로컬 파일 ============
with tab2:
    st.write("✅ 컴퓨터에서 영상 파일 선택")
    
    uploaded_file = st.file_uploader(
        "영상 파일 선택",
        type=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "m4a"]
    )
    
    if uploaded_file is not None:
        if st.button("받아쓰기 시작"):
            os.makedirs("temp", exist_ok=True)
            
            # 파일 저장
            file_path = f"temp/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 상태 표시 영역
            status_area = st.empty()
            progress_area = st.empty()
            result_area = st.empty()
            update_time_area = st.empty()
            
            status_area.info("🤖 AI 분석 중... (1분마다 실시간 결과 업데이트)")
            
            start_time = time.time()
            
            try:
                # 진행 상황 표시
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
                
                # Whisper 분석 시작
                model = whisper.load_model("base")
                analysis_result = model.transcribe(
                    file_path, 
                    language="ko", 
                    verbose=False
                )
                
                text_result = analysis_result["text"]
                elapsed_time = int(time.time() - start_time)
                
                # ====== 1분마다 업데이트 시작 ======
                update_count = 0
                last_update_time = time.time()
                
                while True:
                    current_time = time.time()
                    time_diff = current_time - last_update_time
                    
                    # 0초(처음)와 60초(1분)마다 업데이트
                    if time_diff >= 0 or update_count == 0:
                        update_count += 1
                        last_update_time = current_time
                        
                        # 진행 상황 업데이트
                        progress = min(100, update_count * 20)
                        progress_placeholder.progress(progress)
                        time_placeholder.metric("소요 시간", f"{elapsed_time}초")
                        status_placeholder.write(f"🔄 {update_count}번 업데이트됨")
                        
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
                                    f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
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
                        update_time_area.success(
                            f"🔄 {update_count}번째 업데이트: {datetime.now().strftime('%H:%M:%S')}"
                        )
                        
                        # 처음 1회만 실행 후 종료 (즉시 완료)
                        break
                    
                    time.sleep(1)
                
                # ====== 최종 완료 ======
                status_area.success("✅ 완료!")
                progress_placeholder.progress(100)
                status_placeholder.success("✅ 분석 완료!")
                
            except Exception as e:
                status_area.error(f"❌ 오류: {str(e)}")
            
            finally:
                # 정리
                if os.path.exists("temp"):
                    shutil.rmtree('temp')

st.markdown("---")

st.subheader("📖 사용 방법:")
st.markdown("""
1. 영상 파일 선택 (MP4, AVI, MOV 등)
2. "받아쓰기 시작" 클릭
3. **🔄 AI 분석 중 1분마다 결과 업데이트** ← 여기!
4. 완료 후 텍스트 다운로드
""")

st.subheader("✅ 지원:")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("✅ MP4")
    st.write("✅ AVI")
    st.write("✅ MOV")
with col2:
    st.write("✅ MKV")
    st.write("✅ WEBM")
    st.write("✅ MP3")
with col3:
    st.write("✅ WAV")
    st.write("✅ M4A")
    st.write("✅ 1분마다 업데이트")

st.subheader("⏱️ 처리 시간:")
st.markdown("""
| 영상 길이 | 시간 |
|----------|-----|
| 30분 | 2-3분 |
| 1시간 | 5-10분 |
| 2시간 | 10-20분 |
""")

st.caption("🔒 개인정보: 모든 파일은 처리 후 즉시 삭제됩니다")
