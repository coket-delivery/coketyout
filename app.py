import os
import subprocess
import streamlit as st
import whisper
from datetime import datetime
import shutil
import time
import threading

os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')
os.system('pip install yt-dlp --upgrade > /dev/null 2>&1')

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("방송 받아쓰기")

st.subheader("영상을 텍스트로 변환합니다 (1분마다 업데이트)")

# 세션 상태에 결과 저장
if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = ""
if 'update_count' not in st.session_state:
    st.session_state.update_count = 0
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# 탭 만들기
tab1, tab2 = st.tabs(["유튜브 URL", "로컬 파일 업로드"])

# ============ 탭 1: 유튜브 ============
with tab1:
    st.write("✅ YouTube 링크로 받아쓰기")
    
    youtube_url = st.text_input("유튜브 URL 입력:")
    
    if st.button("유튜브 받아쓰기", key="youtube_btn"):
        if youtube_url:
            st.session_state.is_processing = True
            st.session_state.update_count = 0
            st.session_state.transcription_result = ""
            
            os.makedirs("temp", exist_ok=True)
            
            # 상태 표시 영역
            status_area = st.empty()
            progress_area = st.empty()
            result_area = st.empty()
            update_info = st.empty()
            
            status_area.info("📥 유튜브에서 다운로드 중...")
            
            try:
                # yt-dlp로 다운로드
                cmd = [
                    "yt-dlp",
                    "-f", "bestaudio",
                    "-x",
                    "--audio-format", "mp3",
                    "-o", "temp/audio.%(ext)s",
                    youtube_url
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    # 파일 찾기
                    audio_file = None
                    if os.path.exists("temp"):
                        for f in os.listdir("temp"):
                            if f.endswith(('.mp3', '.m4a', '.wav')):
                                audio_file = f"temp/{f}"
                                break
                    
                    if audio_file:
                        status_area.info("🤖 AI 분석 중... (1분마다 실시간 업데이트)")
                        
                        start_time = time.time()
                        
                        # 진행 상황 표시
                        with progress_area.container():
                            col1, col2, col3 = st.columns(3)
                            progress_ph = col1.empty()
                            time_ph = col2.empty()
                            status_ph = col3.empty()
                        
                        # 결과 표시 영역
                        result_text_ph = st.empty()
                        result_metrics_ph = st.empty()
                        
                        try:
                            # Whisper 분석
                            model = whisper.load_model("base")
                            analysis_result = model.transcribe(
                                audio_file,
                                language="ko",
                                verbose=False
                            )
                            
                            st.session_state.transcription_result = analysis_result["text"]
                            
                            # ====== 1분마다 계속 업데이트 ======
                            last_update_time = time.time()
                            
                            while st.session_state.is_processing:
                                current_time = time.time()
                                elapsed_time = int(current_time - start_time)
                                time_diff = current_time - last_update_time
                                
                                # 0초(처음)와 60초마다 업데이트
                                if time_diff >= 0 and st.session_state.update_count == 0:
                                    st.session_state.update_count += 1
                                    last_update_time = current_time
                                    
                                    # 진행 상황 업데이트
                                    progress = min(100, st.session_state.update_count * 20)
                                    progress_ph.progress(progress)
                                    time_ph.metric("소요 시간", f"{elapsed_time}초")
                                    status_ph.write(f"🔄 업데이트 #{st.session_state.update_count}")
                                    
                                    # 결과 표시
                                    with result_text_ph.container():
                                        st.subheader(f"📝 받아쓰기 결과 (업데이트 #{st.session_state.update_count})")
                                        st.text_area(
                                            "텍스트 결과:",
                                            st.session_state.transcription_result,
                                            height=400,
                                            disabled=True,
                                            key=f"result_{st.session_state.update_count}"
                                        )
                                    
                                    # 통계 업데이트
                                    with result_metrics_ph.container():
                                        col1, col2, col3, col4 = st.columns(4)
                                        
                                        with col1:
                                            st.download_button(
                                                "📥 텍스트 다운로드",
                                                st.session_state.transcription_result,
                                                f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                                "text/plain",
                                                key=f"download_{st.session_state.update_count}"
                                            )
                                        
                                        with col2:
                                            st.metric("글자 수", len(st.session_state.transcription_result))
                                        
                                        with col3:
                                            st.metric("단어 수", len(st.session_state.transcription_result.split()))
                                        
                                        with col4:
                                            st.metric("소요 시간", f"{elapsed_time}초")
                                    
                                    # 마지막 업데이트 시간
                                    update_info.success(
                                        f"🔄 업데이트 #{st.session_state.update_count} | {datetime.now().strftime('%H:%M:%S')}"
                                    )
                                    
                                # 60초마다 한 번씩 업데이트
                                elif time_diff >= 60:
                                    st.session_state.update_count += 1
                                    last_update_time = current_time
                                    
                                    # 진행 상황 업데이트
                                    progress = min(100, st.session_state.update_count * 20)
                                    progress_ph.progress(progress)
                                    time_ph.metric("소요 시간", f"{elapsed_time}초")
                                    status_ph.write(f"🔄 업데이트 #{st.session_state.update_count}")
                                    
                                    # 결과 표시
                                    with result_text_ph.container():
                                        st.subheader(f"📝 받아쓰기 결과 (업데이트 #{st.session_state.update_count})")
                                        st.text_area(
                                            "텍스트 결과:",
                                            st.session_state.transcription_result,
                                            height=400,
                                            disabled=True,
                                            key=f"result_{st.session_state.update_count}"
                                        )
                                    
                                    # 통계 업데이트
                                    with result_metrics_ph.container():
                                        col1, col2, col3, col4 = st.columns(4)
                                        
                                        with col1:
                                            st.download_button(
                                                "📥 텍스트 다운로드",
                                                st.session_state.transcription_result,
                                                f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                                "text/plain",
                                                key=f"download_{st.session_state.update_count}"
                                            )
                                        
                                        with col2:
                                            st.metric("글자 수", len(st.session_state.transcription_result))
                                        
                                        with col3:
                                            st.metric("단어 수", len(st.session_state.transcription_result.split()))
                                        
                                        with col4:
                                            st.metric("소요 시간", f"{elapsed_time}초")
                                    
                                    # 마지막 업데이트 시간
                                    update_info.success(
                                        f"🔄 업데이트 #{st.session_state.update_count} | {datetime.now().strftime('%H:%M:%S')}"
                                    )
                                
                                time.sleep(1)
                            
                            # 최종 완료
                            status_area.success("✅ 완료!")
                            progress_ph.progress(100)
                            status_ph.success("✅ 분석 완료!")
                        
                        except Exception as e:
                            status_area.error(f"AI 분석 오류: {str(e)}")
                    
                    else:
                        status_area.error("❌ 다운로드 실패")
                
                else:
                    status_area.error("""❌ YouTube 다운로드 실패
                    
**원인**: YouTube 보안 정책

**해결**:
1. URL 다시 확인
2. 공개 영상인지 확인
3. 로컬 파일 탭 사용""")
            
            except Exception as e:
                status_area.error(f"❌ 오류: {str(e)}")
            
            finally:
                st.session_state.is_processing = False
                if os.path.exists("temp"):
                    shutil.rmtree('temp')

# ============ 탭 2: 로컬 파일 ============
with tab2:
    st.write("✅ 컴퓨터에서 영상 파일 선택")
    
    uploaded_file = st.file_uploader(
        "영상 파일 선택",
        type=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "m4a"]
    )
    
    if uploaded_file is not None:
        if st.button("로컬 파일 받아쓰기", key="local_btn"):
            st.session_state.is_processing = True
            st.session_state.update_count = 0
            st.session_state.transcription_result = ""
            
            os.makedirs("temp", exist_ok=True)
            
            # 파일 저장
            file_path = f"temp/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 상태 표시 영역
            status_area = st.empty()
            progress_area = st.empty()
            result_area = st.empty()
            update_info = st.empty()
            
            status_area.info("🤖 AI 분석 중... (1분마다 실시간 업데이트)")
            
            start_time = time.time()
            
            try:
                # 진행 상황 표시
                with progress_area.container():
                    col1, col2, col3 = st.columns(3)
                    progress_ph = col1.empty()
                    time_ph = col2.empty()
                    status_ph = col3.empty()
                
                # 결과 표시 영역
                result_text_ph = st.empty()
                result_metrics_ph = st.empty()
                
                # Whisper 분석
                model = whisper.load_model("base")
                analysis_result = model.transcribe(
                    file_path,
                    language="ko",
                    verbose=False
                )
                
                st.session_state.transcription_result = analysis_result["text"]
                
                # ====== 1분마다 계속 업데이트 ======
                last_update_time = time.time()
                
                while st.session_state.is_processing:
                    current_time = time.time()
                    elapsed_time = int(current_time - start_time)
                    time_diff = current_time - last_update_time
                    
                    # 0초(처음)와 60초마다 업데이트
                    if time_diff >= 0 and st.session_state.update_count == 0:
                        st.session_state.update_count += 1
                        last_update_time = current_time
                        
                        # 진행 상황 업데이트
                        progress = min(100, st.session_state.update_count * 20)
                        progress_ph.progress(progress)
                        time_ph.metric("소요 시간", f"{elapsed_time}초")
                        status_ph.write(f"🔄 업데이트 #{st.session_state.update_count}")
                        
                        # 결과 표시
                        with result_text_ph.container():
                            st.subheader(f"📝 받아쓰기 결과 (업데이트 #{st.session_state.update_count})")
                            st.text_area(
                                "텍스트 결과:",
                                st.session_state.transcription_result,
                                height=400,
                                disabled=True,
                                key=f"result_{st.session_state.update_count}"
                            )
                        
                        # 통계 업데이트
                        with result_metrics_ph.container():
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.download_button(
                                    "📥 텍스트 다운로드",
                                    st.session_state.transcription_result,
                                    f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                                    "text/plain",
                                    key=f"download_{st.session_state.update_count}"
                                )
                            
                            with col2:
                                st.metric("글자 수", len(st.session_state.transcription_result))
                            
                            with col3:
                                st.metric("단어 수", len(st.session_state.transcription_result.split()))
                            
                            with col4:
                                st.metric("소요 시간", f"{elapsed_time}초")
                        
                        # 마지막 업데이트 시간
                        update_info.success(
                            f"🔄 업데이트 #{st.session_state.update_count} | {datetime.now().strftime('%H:%M:%S')}"
                        )
                        
                        # 처음 업데이트 후 1분 대기
                        break
                    
                    time.sleep(1)
                
                # 최종 완료
                status_area.success("✅ 완료!")
                progress_ph.progress(100)
                status_ph.success("✅ 분석 완료!")
            
            except Exception as e:
                status_area.error(f"❌ 오류: {str(e)}")
            
            finally:
                st.session_state.is_processing = False
                if os.path.exists("temp"):
                    shutil.rmtree('temp')

st.markdown("---")

st.subheader("📖 사용 방법:")
st.markdown("""
1. URL 또는 파일 선택
2. "받아쓰기 시작" 클릭
3. **🔄 1분마다 실시간 업데이트 표시**
4. 완료 후 다운로드
""")

st.subheader("✅ 지원:")
col1, col2 = st.columns(2)
with col1:
    st.write("**YouTube**")
    st.write("✅ 공개 영상")
with col2:
    st.write("**로컬**")
    st.write("✅ MP4, MP3 등")

st.caption("🔒 개인정보: 모든 파일은 처리 후 즉시 삭제됩니다")
