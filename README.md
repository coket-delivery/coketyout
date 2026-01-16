# 🎬 동영상 한국말 받아쓰기 (Video Korean Transcriber)

Streamlit과 OpenAI Whisper를 사용하여 동영상의 한국어 음성을 텍스트로 변환하는 웹 앱입니다.

## ✨ 주요 기능

- 📤 **다중 포맷 지원**: MP4, AVI, MOV, MKV, FLV, WMV, WebM, M4V
- 🎙️ **정확한 한국어 인식**: OpenAI Whisper 모델 사용
- ⏱️ **타임스탬프 포함**: 각 구간별로 시간 표기
- 📥 **다양한 출력 형식**:
  - 일반 텍스트 (.txt)
  - JSON 형식 (.json)
  - SRT 자막 (.srt)
- 📊 **실시간 진행률 표시**: 처리 상태 확인
- 🔧 **모델 선택**: tiny ~ large 중 선택 가능

## 🚀 설치 및 실행

### 로컬 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/video-korean-transcriber.git
cd video-korean-transcriber

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# Streamlit 실행
streamlit run app.py
