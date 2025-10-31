# 법인세 에이전트 (Corporate Tax Agent)

법인세 계산 및 리포트 생성 AI 에이전트 (로컬 실행 가능)

## ⚠️ 중요 면책 사항

**본 시스템은 연구 및 시뮬레이션 목적으로만 사용됩니다.**

- 실제 세무 신고에 사용할 수 없습니다.
- 세무 자문 용도로 사용할 수 없습니다.
- 법인세 파라미터는 임시 템플릿이며 실제 법령과 다를 수 있습니다.
- 정식 세무 업무는 반드시 공인 세무사와 상담하세요.

## 주요 기능

- 🏢 DART(전자공시) API를 통한 기업 재무 정보 조회
- 💰 법인세 자동 계산 (하드코딩 템플릿 기반)
- 📊 PDF 리포트 생성
- 🔍 과거 계산 결과 검색 및 비교 (RAG + FTS5)
- 💬 멀티턴 채팅 지원

## 기술 스택

### 백엔드
- FastAPI
- SQLAlchemy + SQLite + FTS5
- OpenAI API (Chat Completions + Embeddings)
- ReportLab (PDF 생성)

### 프론트엔드
- Vite + React + TypeScript
- 간단한 채팅 UI

## 설치 및 실행

### 사전 요구사항

- Python 3.10 이상
- Node.js 18 이상
- OpenAI API 키
- DART API 키 (선택)

### 1. 백엔드 설정

```bash
# 가상환경 생성 (권장)
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 의존성 설치
cd backend
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력

# 백엔드 실행
python -m app.main
# 또는
uvicorn app.main:app --reload --port 8000
```

백엔드가 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 설정

```bash
# 새 터미널 열기
cd frontend

# 의존성 설치
npm install

# 프론트엔드 실행
npm run dev
```

프론트엔드가 `http://localhost:5173`에서 실행됩니다.

### 3. 브라우저 접속

`http://localhost:5173`에 접속하여 채팅 시작

## 사용 예시

### 기본 사용

```
사용자: 현재 법인세 관련 법령 기준으로 삼성전자의 법인세를 계산하고 pdf로 저장해줘
```

에이전트가 다음 작업을 수행합니다:
1. DART에서 삼성전자 재무 정보 조회
2. 하드코딩된 법령 파라미터로 법인세 계산
3. 결과 평가 및 검증
4. PDF 리포트 생성
5. DB 및 RAG 저장소에 결과 저장

### 비교 분석

```
사용자: 지난번 결과랑 이번 결과를 비교표로 보여줘
```

에이전트가 RAG 검색을 통해 과거 결과를 조회하고 비교표를 생성합니다.

## 프로젝트 구조

```
corp-tax-agent/
├─ backend/
│  ├─ app/
│  │  ├─ main.py              # FastAPI 메인
│  │  ├─ config.py            # 설정
│  │  ├─ routes/
│  │  │  ├─ chat.py           # 채팅 엔드포인트
│  │  │  └─ report.py         # 리포트 다운로드
│  │  ├─ schemas/
│  │  │  └─ dto.py            # Pydantic 스키마
│  │  ├─ db/
│  │  │  ├─ models.py         # SQLAlchemy 모델
│  │  │  ├─ session.py        # DB 세션
│  │  │  └─ crud.py           # CRUD 함수
│  │  ├─ agents/
│  │  │  └─ corp_tax_agent.py # 에이전트 그래프
│  │  ├─ tools/
│  │  │  ├─ llm.py            # OpenAI 래퍼
│  │  │  ├─ dart.py           # DART API
│  │  │  ├─ tax_rules.py      # 법령 템플릿
│  │  │  ├─ tax_calc.py       # 계산 로직
│  │  │  ├─ rag_store.py      # RAG 저장/검색
│  │  │  └─ pdf_maker.py      # PDF 생성
│  │  └─ utils/
│  │     └─ timeutil.py       # 시간 유틸
│  ├─ requirements.txt
│  └─ .env.example
│
├─ frontend/
│  ├─ src/
│  │  ├─ main.tsx
│  │  ├─ App.tsx              # 메인 채팅 UI
│  │  ├─ App.css
│  │  └─ api.ts               # API 클라이언트
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.ts
│
└─ README.md
```

## API 엔드포인트

### POST /chat
채팅 메시지 전송

**요청:**
```json
{
  "message": "삼성전자 법인세 계산해줘",
  "session_id": "optional-session-id"
}
```

**응답:**
```json
{
  "session_id": "uuid",
  "reply_text": "계산 결과 텍스트",
  "report_id": "uuid",
  "download_url": "/report/uuid"
}
```

### GET /report/{report_id}
PDF 리포트 다운로드

### GET /healthz
헬스체크

## 데이터베이스 스키마

- **sessions**: 채팅 세션
- **messages**: 채팅 메시지 (멀티턴)
- **law_param_snapshots**: 법령 파라미터 스냅샷
- **dart_cache**: DART API 응답 캐시
- **calc_results**: 법인세 계산 결과
- **rag_docs**: RAG 문서 저장
- **rag_fts**: FTS5 전문 검색 인덱스

## 에이전트 그래프

```
Plan → Fetch(DART) → LawParam → Calc → Eval → Report
                                         ↓
                                    (재계산?)
```

- **Plan**: LLM이 사용자 요청 분석
- **Fetch**: DART에서 재무 정보 조회
- **LawParam**: 현재 법령 파라미터 로드
- **Calc**: 법인세 계산
- **Eval**: 결과 평가 (신뢰도 체크)
- **Report**: PDF 생성 및 RAG 저장

## 환경 변수

`.env` 파일:

```env
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

# DART API (없으면 모의 데이터 사용)
DART_API_KEY=your-dart-key

# DB
DB_URL=sqlite:///./corp_tax_agent.db

# 리포트
REPORT_DIR=./reports
```

## 테스트 시나리오

1. **기본 계산**
   - "삼성전자 법인세 계산해줘"
   - PDF 다운로드 확인

2. **멀티턴**
   - "이제 SK하이닉스도 계산해줘"
   - 세션 유지 확인

3. **비교 분석**
   - "삼성전자 과거 결과랑 비교해줘"
   - RAG 검색 및 비교표 생성 확인

4. **DB 확인**
   - `corp_tax_agent.db` 파일 생성 확인
   - `reports/` 폴더에 PDF 생성 확인

## 제한 사항

- DART API 키가 없으면 모의 데이터 사용
- 법인세 계산은 간략화된 근사치
- 세액공제 및 세무조정 미반영
- 실제 세무 신고에 사용 불가

## 라이선스

MIT License (연구 및 교육 목적)

## 문의

프로젝트 관련 문의는 이슈를 통해 제출해주세요.
