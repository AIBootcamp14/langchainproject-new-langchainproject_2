# 🛍️ 커머스 마케팅 AI 에이전트

로컬 실행 가능한 멀티 태스크 커머스 마케팅 AI 에이전트 시스템입니다.

## 📋 개요

이 프로젝트는 **5가지 커머스 마케팅 태스크**를 수행하는 AI 에이전트 시스템입니다:

1. **소비 트렌드 분석** - 제품/키워드의 트렌드 분석
2. **광고 문구 생성** - AI 기반 광고 카피 생성
3. **사용자 세그먼트 분류** - 고객 데이터 클러스터링 및 분류
4. **리뷰 감성 분석** - 제품 리뷰 감성 분석 및 요약
5. **경쟁사 분석** - 경쟁 제품 비교 및 SWOT 분석

## 🏗️ 아키텍처

```
사용자 메시지 → 라우터 (키워드 감지) → 적절한 에이전트 실행 → 결과 반환
```

### 주요 구성 요소

- **Frontend**: Vite + React (채팅 UI)
- **Backend**: FastAPI
- **LLM**: OpenAI Chat Completions API
- **DB**: SQLite + SQLAlchemy + FTS5 (RAG용)
- **외부 API**: Naver쇼핑, Google Trends 등 (태스크별 선택)

## 🚀 빠른 시작

### 1. 필수 요구사항

- Python 3.10+
- Node.js 16+
- OpenAI API 키

### 2. 설치 및 실행

**백엔드:**
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

**프론트엔드:**
```bash
cd frontend
npm install
npm run dev
```

### 3. 사용 예시

채팅창에 다음과 같이 입력하세요:

- **트렌드 분석**: "최근 반려동물 관련 트렌드 분석해줘"
- **광고 문구**: "친환경 세제 광고 문구 만들어줘"
- **세그먼트 분류**: "이 고객 데이터를 세그먼트로 나눠줘"
- **리뷰 분석**: "이 제품 리뷰 감성 분석해줘"
- **경쟁사 분석**: "경쟁사 제품과 가격 비교해줘"

## 📁 프로젝트 구조

```
├── backend/
│   └── app/
│       ├── agents/
│       │   ├── router.py              # 키워드 기반 라우터
│       │   ├── trend_agent.py         # 트렌드 분석 에이전트
│       │   ├── ad_copy_agent.py       # 광고 문구 생성 에이전트
│       │   ├── segment_agent.py       # 세그먼트 분류 에이전트
│       │   ├── review_agent.py        # 리뷰 감성 분석 에이전트
│       │   └── competitor_agent.py    # 경쟁사 분석 에이전트
│       ├── tools/
│       │   ├── common/                # 공통 도구
│       │   │   ├── web_search.py      # 웹 검색
│       │   │   ├── api_client.py      # 외부 API 클라이언트
│       │   │   └── rag_base.py        # RAG 인프라
│       │   ├── trend_tools.py         # 트렌드 분석 도구
│       │   ├── ad_tools.py            # 광고 문구 도구
│       │   ├── segment_tools.py       # 세그먼트 분류 도구
│       │   ├── review_tools.py        # 리뷰 분석 도구
│       │   └── competitor_tools.py    # 경쟁사 분석 도구
│       ├── db/                        # 데이터베이스
│       ├── routes/                    # API 라우트
│       └── schemas/                   # DTO
└── frontend/                          # React 채팅 UI
```

## 👥 팀 협업 가이드

### 각 팀원의 작업 범위

**팀원 1: 트렌드 분석**
- `backend/app/agents/trend_agent.py` 구현
- `backend/app/tools/trend_tools.py` 구현
- Google Trends, Naver DataLab API 연동

**팀원 2: 광고 문구 생성**
- `backend/app/agents/ad_copy_agent.py` 구현
- `backend/app/tools/ad_tools.py` 구현
- LLM 프롬프트 최적화

**팀원 3: 사용자 세그먼트 분류**
- `backend/app/agents/segment_agent.py` 구현
- `backend/app/tools/segment_tools.py` 구현
- scikit-learn 클러스터링 알고리즘 적용

**팀원 4: 리뷰 감성 분석**
- `backend/app/agents/review_agent.py` 구현
- `backend/app/tools/review_tools.py` 구현
- 크롤링 또는 API로 리뷰 수집, 감성 분석

**팀원 5: 경쟁사 분석**
- `backend/app/agents/competitor_agent.py` 구현
- `backend/app/tools/competitor_tools.py` 구현
- 가격 비교, SWOT 분석 로직

### 작업 흐름

1. 각 팀원은 자신의 에이전트/툴 파일을 구현
2. `.env`에 필요한 API 키 추가
3. `backend/app/agents/router.py`에서 에이전트 활성화:
   ```python
   from app.agents.trend_agent import run_agent as run_trend
   AGENT_MAP["trend"]["runner"] = run_trend
   ```
4. 채팅창에서 키워드로 테스트

## 🔑 환경 변수 설정

`backend/.env` 파일에서 설정:

```env
# 필수
OPENAI_API_KEY=your_openai_key_here

# 선택 (태스크별 필요 시)
NAVER_DATALAB_CLIENT_ID=your_naver_client_id_here
NAVER_SHOPPING_CLIENT_ID=your_naver_shopping_client_id_here
GOOGLE_CUSTOM_SEARCH_API_KEY=your_google_search_key_here
```

## 🧪 테스트

백엔드가 실행된 상태에서:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "트렌드 분석해줘", "session_id": ""}'
```

## 📝 라이선스

MIT License

## 🤝 기여

이슈나 PR을 환영합니다!

## 📞 문의

프로젝트 관련 문의는 이슈로 남겨주세요.
