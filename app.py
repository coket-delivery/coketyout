import streamlit as st
import whisper
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
import tempfile
import numpy as np
from moviepy.editor import VideoFileClip
import math

# 페이지 설정
st.set_page_config(
    page_title="동영상 한국말 받아쓰기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 동영상 한국말 받아쓰기")
st.markdown("Whisper AI를 사용한 정확한 한국어 음성 인식")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    model_size = st.selectbox(
        "Whisper 모델 선택",
        ["tiny", "base", "small", "medium", "large"],
        help="작은 모델: 빠르지만 정확도 낮음\n큰 모델: 느리지만 정확도 높음"
    )
    
    output_format = st.selectbox(
        "결과 형식",
        ["텍스트 (.txt)", "JSON (.json)", "SRT 자막 (.srt)"],
        help="받아쓰기 결과의 저장 형식을 선택하세요"
    )

# 주요 함수들
@st.cache_resource
def load_whisper_model(model_name):
    """Whisper 모델 로드"""
    return whisper.load_model(model_name)

def get_audio_from_video(video_path):
    """동영상에서 음성 추출"""
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        
        if audio is None:
            return None, "동영상에 음성이 없습니다."
        
        duration = video.duration
        video.close()
        return audio, duration
    except Exception as e:
        return None, f"음성 추출 오류: {str(e)}"

def transcribe_audio(audio, model, progress_bar=None):
    """음성 받아쓰기"""
    try:
        # 임시 오디오 파일 저장
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
            audio.write_audiofile(tmp_audio.name, verbose=False, logger=None)
            tmp_audio_path = tmp_audio.name
        
        # Whisper로 받아쓰기
        result = model.transcribe(
            tmp_audio_path,
            language="ko",
            verbose=False
        )
        
        # 임시 파일 삭제
        os.remove(tmp_audio_path)
        
        return result, None
    except Exception as e:
        return None, f"받아쓰기 오류: {str(e)}"

def format_time(seconds):
    """초를 HH:MM:SS 형식으로 변환"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def create_srt_content(segments):
    """SRT 자막 형식 생성"""
    srt_lines = []
    for i, segment in enumerate(segments, 1):
        start = format_time(segment['start'])
        end = format_time(segment['end'])
        text = segment['text'].strip()
        
        srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    
    return "\n".join(srt_lines)

def create_json_content(segments, metadata=None):
    """JSON 형식 생성"""
    data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": "whisper",
            "language": "ko"
        },
        "segments": [
            {
                "id": i,
                "start": round(seg['start'], 2),
                "end": round(seg['end'], 2),
                "text": seg['text'].strip()
            }
            for i, seg in enumerate(segments, 1)
        ],
        "full_text": " ".join([seg['text'].strip() for seg in segments])
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def create_txt_content(segments):
    """텍스트 형식 생성"""
    lines = []
    for segment in segments:
        start = format_time(segment['start'])
        end = format_time(segment['end'])
        text = segment['text'].strip()
        lines.append(f"[{start} ~ {end}] {text}")
    
    return "\n".join(lines)

# 메인 UI
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📤 동영상 업로드")
    uploaded_file = st.file_uploader(
        "동영상 파일을 선택하세요",
        type=["mp4", "avi", "mov", "mkv", "flv", "wmv", "webm", "m4v"],
        help="지원 포맷: MP4, AVI, MOV, MKV, FLV, WMV, WebM, M4V"
    )

# 받아쓰기 처리
if uploaded_file is not None:
    # 파일 저장
    with tempfile.NamedTemporaryFile(suffix=Path(uploaded_file.name).suffix, delete=False) as tmp_video:
        tmp_video.write(uploaded_file.getbuffer())
        tmp_video_path = tmp_video.name
    
    try:
        # 동영상 정보 표시
        with col2:
            st.subheader("📊 파일 정보")
            st.info(f"**파일명:** {uploaded_file.name}\n**파일 크기:** {uploaded_file.size / (1024*1024):.2f} MB")
        
        # 진행 상황 표시
        st.subheader("🔄 처리 진행도")
        
        # 음성 추출 단계
        st.write("**1단계: 음성 추출 중...**")
        audio, duration_or_error = get_audio_from_video(tmp_video_path)
        
        if audio is None:
            st.error(duration_or_error)
        else:
            st.success("✓ 음성 추출 완료")
            st.write(f"📹 동영상 길이: {format_time(duration_or_error)}")
            
            # 모델 로드 및 받아쓰기
            st.write("**2단계: Whisper 모델 로드 중...**")
            with st.spinner(f"📥 {model_size} 모델을 다운로드하고 있습니다..."):
                model = load_whisper_model(model_size)
            st.success("✓ 모델 로드 완료")
            
            # 받아쓰기 시작
            st.write("**3단계: 음성 인식 중...**")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("🎙️ Whisper가 음성을 인식하고 있습니다..."):
                result, error = transcribe_audio(audio, model, progress_bar)
            
            if error:
                st.error(error)
            else:
                progress_bar.progress(100)
                st.success("✓ 음성 인식 완료!")
                
                # 결과 처리
                segments = result['segments']
                
                # 결과 탭
                tab1, tab2, tab3 = st.tabs(["📝 결과 보기", "⏱️ 타임스탬프 포함", "📥 다운로드"])
                
                with tab1:
                    st.subheader("전체 받아쓰기 결과")
                    full_text = " ".join([seg['text'].strip() for seg in segments])
                    st.text_area(
                        "받아쓰기 결과",
                        value=full_text,
                        height=300,
                        disabled=True
                    )
                
                with tab2:
                    st.subheader("타임스탬프와 함께")
                    for segment in segments:
                        start = format_time(segment['start'])
                        end = format_time(segment['end'])
                        text = segment['text'].strip()
                        st.markdown(f"**[{start} ~ {end}]** {text}")
                
                with tab3:
                    st.subheader("📥 결과 다운로드")
                    
                    # 파일명 생성
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    base_filename = f"transcription_{timestamp}"
                    
                    # 선택된 형식에 따라 내용 생성
                    if output_format == "텍스트 (.txt)":
                        content = create_txt_content(segments)
                        filename = f"{base_filename}.txt"
                    elif output_format == "JSON (.json)":
                        content = create_json_content(segments)
                        filename = f"{base_filename}.json"
                    else:  # SRT
                        content = create_srt_content(segments)
                        filename = f"{base_filename}.srt"
                    
                    # 다운로드 버튼
                    st.download_button(
                        label=f"📥 {filename} 다운로드",
                        data=content,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                    # 통계
                    st.divider()
                    st.subheader("📊 통계")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 세그먼트", len(segments))
                    with col2:
                        word_count = len(full_text.split())
                        st.metric("단어 수", word_count)
                    with col3:
                        st.metric("문자 수", len(full_text))
    
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
    
    finally:
        # 임시 파일 정리
        if os.path.exists(tmp_video_path):
            os.remove(tmp_video_path)

else:
    st.info("💡 **사용방법:**\n1. 왼쪽에서 동영상 파일을 업로드하세요\n2. Whisper 모델과 출력 형식을 선택하세요\n3. 자동으로 받아쓰기가 진행됩니다\n4. 원하는 형식으로 결과를 다운로드하세요")
