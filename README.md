# NovelWriter Local

로컬 AI를 활용하여 한국 웹소설을 자동 생성하는 개인용 데스크톱 애플리케이션입니다.

## 주요 기능

- **프로젝트 관리**: 작품별 프로젝트 생성·편집·삭제
- **챕터 편집기**: 텍스트 에디터 + 자동 저장 (30초 간격)
- **AI 챕터 생성**: 로컬 LLM(Ollama / LM Studio)을 이용해 다음 챕터 자동 생성
- **캐릭터 관리**: 이름·나이·성격·외모·배경 등 캐릭터 정보 관리
- **세계관 관리**: 용어·지명·조직 등 세계관 설정 문서 작성
- **생성 히스토리**: 버전별 저장 및 롤백
- **내보내기**: 단일 챕터 또는 전체 챕터를 `txt` / `docx`로 저장

## 기술 스택

| 영역 | 기술 |
|------|------|
| GUI | PyQt6 |
| 데이터베이스 | SQLite (내장) |
| AI 연동 | Ollama API / OpenAI 호환 API (LM Studio) |
| 내보내기 | python-docx |

## 설치 방법

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 애플리케이션 실행
python main.py
```

## LLM 설정 가이드

### Ollama 사용 (권장)

```bash
# Ollama 설치 후 모델 다운로드
ollama pull mistral          # 영어 범용
ollama pull llama3.1         # 최신 Llama
ollama pull EEVE-Korean-10.8B  # 한국어 특화
ollama pull solar            # 한국어 강화
```

Ollama 서버는 기본적으로 `http://localhost:11434`에서 실행됩니다.

### LM Studio 사용

LM Studio를 실행하고 **로컬 서버**를 시작한 뒤, 앱 설정에서 엔드포인트를 LM Studio 포트로 변경하세요.

### 앱 내 설정

`도구 > 설정`에서 다음 항목을 구성할 수 있습니다.

- **LLM 엔드포인트**: 기본값 `http://localhost:11434`
- **모델 이름**: Ollama에서 내려받은 모델 이름 입력
- **Temperature**: 창의성 수준 (0.0 ~ 1.0, 기본 0.8)
- **Max Tokens**: 최대 생성 토큰 수 (기본 4096)

## 프로젝트 구조

```
novelwriter-local/
├── main.py                      # 엔트리 포인트
├── requirements.txt
├── README.md
└── src/
    ├── gui/                     # GUI 위젯
    │   ├── main_window.py       # 메인 윈도우
    │   ├── project_dialog.py    # 프로젝트 생성/편집
    │   ├── chapter_editor.py    # 챕터 편집기
    │   ├── character_panel.py   # 캐릭터 관리
    │   ├── worldbuilding_panel.py # 세계관 관리
    │   └── generation_dialog.py  # AI 생성 다이얼로그
    ├── database/                # 데이터베이스 레이어
    │   ├── db_manager.py        # CRUD 연산
    │   ├── models.py            # 데이터 모델
    │   └── schema.sql           # DB 스키마
    ├── ai/                      # AI 엔진
    │   ├── llm_client.py        # LLM API 클라이언트
    │   ├── prompt_builder.py    # 프롬프트 생성
    │   └── context_manager.py   # 컨텍스트 관리
    └── utils/                   # 유틸리티
        ├── export.py            # txt/docx 내보내기
        └── config.py            # 설정 관리
```

## 데이터 저장 위치

설정 및 데이터베이스 파일은 사용자 홈 디렉토리에 저장됩니다.

```
~/.novelwriter_local/
├── config.json      # 앱 설정
└── novelwriter.db   # SQLite 데이터베이스
```

## 최소 사양

- Python 3.10+
- RAM 8GB (LLM 실행 시)
- 저장공간 20GB (모델 포함)
- GPU 없이도 실행 가능 (생성 속도가 느릴 수 있음)

## 사용 방법

1. `python main.py`로 앱 실행
2. **새 프로젝트** 버튼으로 작품 정보 입력 (제목, 장르, 플롯 등)
3. **+ 챕터** 버튼으로 챕터 추가
4. **✨ AI 생성** 버튼으로 AI 자동 챕터 생성
5. 생성된 내용을 편집하고 **저장** (Ctrl+S)
6. 오른쪽 패널에서 캐릭터 및 세계관 정보 관리
7. `파일 > 내보내기`로 txt 또는 docx 파일로 저장