# 빠른 시작 가이드

## 1분 안에 실행하기

### 1단계: API 키 설정

`backend/.env` 파일을 열어 다음 항목을 수정하세요:

```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
DART_API_KEY=your-dart-key-or-leave-empty-for-mock
```

**중요:** OPENAI_API_KEY는 필수입니다. DART_API_KEY가 없어도 모의 데이터로 작동합니다.

### 2단계: 백엔드 실행

```bash
# 터미널 1
cd backend
pip install -r requirements.txt
python -m app.main
```

서버가 `http://localhost:8000`에서 시작됩니다.

### 3단계: 프론트엔드 실행

```bash
# 터미널 2 (새 창)
cd frontend
npm install
npm run dev
```

브라우저가 자동으로 `http://localhost:5173`을 열거나, 수동으로 접속하세요.

### 4단계: 테스트

채팅창에 입력:

```
현재 법인세 관련 법령 기준으로 삼성전자의 법인세를 계산하고 pdf로 저장해줘
```

에이전트가 자동으로:
1. 재무 정보 조회
2. 법인세 계산
3. PDF 리포트 생성
4. 다운로드 링크 제공

## 문제 해결

### 백엔드 오류

**오류:** `ModuleNotFoundError`
**해결:** 가상환경 활성화 후 `pip install -r requirements.txt` 재실행

**오류:** `OpenAI API 키가 설정되지 않았습니다`
**해결:** `backend/.env` 파일에서 `OPENAI_API_KEY` 확인

### 프론트엔드 오류

**오류:** `Cannot connect to backend`
**해결:** 백엔드가 8000 포트에서 실행 중인지 확인

**오류:** CORS 오류
**해결:** 백엔드 재시작

## 다음 단계

- [README.md](README.md)에서 상세 문서 확인
- API 문서: `http://localhost:8000/docs`
- 헬스체크: `http://localhost:8000/healthz`

## 면책 사항

⚠️ 본 시스템은 연구/시뮬레이션 목적이며 실제 세무 신고에 사용할 수 없습니다.
