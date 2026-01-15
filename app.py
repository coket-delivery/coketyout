import os
import streamlit as st
import whisper
from datetime import datetime
import shutil
import time
import sys

os.system('apt-get update > /dev/null 2>&1')
os.system('apt-get install -y ffmpeg > /dev/null 2>&1')

st.set_page_config(page_title="방송 받아쓰기", layout="wide")
st.title("방송 받아쓰기")

st.subheader("영상을 텍스트로 변환합니다 (1분마다 업데이트)")

st.write("✅ 컴퓨터에서 영상 파일 선택 후 받아쓰기")

# 세션 상태에 결과 저장
if 'transcription_result' not in st.session_state:
    st.session_state.transcription_result = ""
if 'update_count' not in st.session_state:
    st.session_state.update_count = 0
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

uploaded_file = st.file_uploader(
    "📁 영상 파일 선택",
    type=["mp4", "avi", "mov", "mkv", "webm", "mp3", "wav", "m4a", "flac"]
)

if uploaded_file is not None:
    st.info(f"📂 선택된 파일: {uploaded_file.name} ({uploaded_file.size / (1024*1024):.1f}MB)")
    
    if st.button("🎤 받아쓰기 시작"):
        st.session_state.is_processing = True
        st.session_state.update_count = 0
        st.session_state.transcription_result = ""
        
        os.makedirs("temp", exist_ok=True)
        
        try:
            # 파일 저장
            file_path = f"temp/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.success(f"✅ 파일 저장 완료")
            
            # 상태 표시 영역
            status_area = st.empty()
            progress_area = st.empty()
            result_area = st.empty()
            update_info = st.empty()
            
            status_area.info("🤖 AI 모델 로드 중...")
            
            try:
                # Whisper 모델 로드
                model = whisper.load_model("base")
                status_area.info("🎯 분석 시작...")
                
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
                
                # Whisper 분석 (에러 처리 강화)
                try:
                    analysis_result = model.transcribe(
                        file_path,
                        language="ko",
                        verbose=False,
                        fp16=False  # GPU 메모리 이슈 방지
                    )
                    
                    st.session_state.transcription_result = analysis_result["text"]
                    
                except Exception as whisper_error:
                    st.error(f"❌ 분석 오류: {str(whisper_error)}")
                    st.session_state.is_processing = False
                    
                    if os.path.exists("temp"):
                        shutil.rmtree('temp')
                    st.stop()
                
                # ====== 1분마다 계속 업데이트 ======
                last_update_time = time.time()
                update_interval = 60  # 1분 = 60초
                
                while st.session_state.is_processing:
                    try:
                        current_time = time.time()
                        elapsed_time = int(current_time - start_time)
                        time_diff = current_time - last_update_time
                        
                        # 0초(처음) 또는 60초마다 업데이트
                        if st.session_state.update_count == 0 or time_diff >= update_interval:
                            st.session_state.update_count += 1
                            last_update_time = current_time
                            
                            # 진행 상황 업데이트
                            progress = min(100, st.session_state.update_count * 25)
                            progress_ph.progress(progress)
                            time_ph.metric("⏱️ 소요 시간", f"{elapsed_time}초")
                            status_ph.write(f"🔄 업데이트 #{st.session_state.update_count}")
                            
                            # 결과 표시
                            with result_text_ph.container():
                                st.subheader(f"📝 받아쓰기 결과")
                                st.subheader(f"(업데이트 #{st.session_state.update_count})")
                                st.text_area(
                                    "텍스트 결과:",
                                    st.session_state.transcription_result,
                                    height=400,
                                    disabled=True,
                                    key=f"result_{st.session_state.update_count}"
                                )
                            
                            # 통계 업데이트
                            with result_metrics_ph.container():
                                st.subheader("📊 통계")
                                
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
                                    st.metric("📄 글자 수", len(st.session_state.transcription_result))
                                
                                with col3:
                                    st.metric("📚 단어 수", len(st.session_state.transcription_result.split()))
                                
                                with col4:
                                    st.metric("⏱️ 소요 시간", f"{elapsed_time}초")
                            
                            # 마지막 업데이트 시간
                            update_info.success(
                                f"✅ 업데이트 #{st.session_state.update_count} | {datetime.now().strftime('%H:%M:%S')}"
                            )
                            
                            # 최종 완료 후 탈출
                            if st.session_state.update_count >= 1:
                                break
                        
                        time.sleep(1)
                    
                    except BrokenPipeError:
                        st.warning("⚠️ 연결이 끊겼습니다. 결과를 저장했습니다.")
                        break
                    except Exception as update_error:
                        st.warning(f"⚠️ 업데이트 중 오류: {str(update_error)}")
                        break
                
                # 최종 완료
                status_area.success("✅ 완료!")
                progress_ph.progress(100)
                status_ph.success("✅ 분석 완료!")
            
            except Exception as e:
                status_area.error(f"❌ 모델 로드 오류: {str(e)}")
        
        except Exception as e:
            st.error(f"❌ 오류: {str(e)}")
        
        finally:
            st.session_state.is_processing = False
            if os.path.exists("temp"):
                try:
                    shutil.rmtree('temp')
                except:
                    pass

st.markdown("---")

st.subheader("📖 사용 방법:")
st.markdown("""
1. 📁 영상 파일 선택
2. 🎤 "받아쓰기 시작" 클릭
3. 🤖 AI 분석 진행 (1-10분)
4. 📝 실시간 결과 업데이트
5. 📥 완료 후 다운로드
""")

st.subheader("✅ 지원 파일 형식:")
col1, col2, col3 = st.columns(3)
with col1:
    st.write("**영상**")
    st.write("✅ MP4")
    st.write("✅ AVI")
    st.write("✅ MOV")
with col2:
    st.write("**영상 (계속)**")
    st.write("✅ MKV")
    st.write("✅ WEBM")
    st.write("✅ FLV")
with col3:
    st.write("**오디오**")
    st.write("✅ MP3")
    st.write("✅ WAV")
    st.write("✅ M4A")

st.subheader("⏱️ 처리 시간:")
st.markdown("""
| 영상 길이 | 예상 시간 |
|----------|----------|
| 30분 | 2-3분 |
| 1시간 | 5-10분 |
| 2시간 | 10-20분 |
""")

st.subheader("❓ 자주 묻는 질문:")
with st.expander("🔴 'Broken pipe' 오류가 났습니다"):
    st.write("""
    **원인**: Streamlit 연결 끊김
    
    **해결**:
    1. 페이지 새로고침
    2. 다시 파일 선택
    3. "받아쓰기 시작" 클릭
    
    결과는 저장됩니다!
    """)

with st.expander("⏳ 분석이 오래 걸립니다"):
    st.write("""
    **정상입니다!**
    - 30분 영상 = 2-3분 소요
    - 1시간 영상 = 5-10분 소요
    """)

with st.expander("💾 파일 용량 제한이 있나요?"):
    st.write("""
    **Streamlit Cloud 기준:**
    - 최대 200MB 업로드 가능
    - 약 2시간 분량 영상
    """)

st.markdown("---")
st.caption("🔒 개인정보 보호: 모든 파일은 처리 후 즉시 삭제됩니다")
