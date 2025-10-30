"""
소비 트렌드 분석 에이전트
Google Trends, Naver DataLab 등을 활용한 트렌드 분석
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.db.session import get_db
from app.db.crud import append_message, create_session, get_session

logger = logging.getLogger(__name__)


class TrendAgentContext:
    """트렌드 분석 에이전트 컨텍스트"""

    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.keyword: Optional[str] = None
        self.trend_data: Optional[Dict[str, Any]] = None
        self.analysis_result: Optional[str] = None
        self.errors: list = []


class TrendAgent:
    """트렌드 분석 에이전트"""

    def __init__(self):
        self.name = "TrendAgent"

    def run(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """
        에이전트 실행

        Args:
            session_id: 세션 ID
            user_message: 사용자 메시지

        Returns:
            실행 결과
        """
        logger.info(f"트렌드 분석 에이전트 시작 (세션: {session_id})")

        context = TrendAgentContext(session_id, user_message)

        try:
            # 세션 확인/생성
            with get_db() as db:
                if not session_id:
                    session = create_session(db)
                    context.session_id = session.id
                else:
                    session = get_session(db, session_id)
                    if not session:
                        session = create_session(db)
                        context.session_id = session.id

                # 사용자 메시지 저장
                append_message(db, context.session_id, "system", "--- 트렌드 분석 시작 ---")
                append_message(db, context.session_id, "user", context.user_message)

            # TODO: 팀원이 구현할 로직
            # 1. 사용자 메시지에서 키워드 추출
            # 2. Google Trends API 또는 Naver DataLab API 호출
            # 3. 트렌드 데이터 분석
            # 4. LLM으로 인사이트 생성

            # 현재는 모의 응답
            reply_text = self._generate_mock_response(context)

            # 응답 저장
            with get_db() as db:
                append_message(db, context.session_id, "assistant", reply_text)

            return {
                "success": True,
                "session_id": context.session_id,
                "reply_text": reply_text,
                "result_data": {
                    "keyword": context.keyword,
                    "trend_data": context.trend_data
                },
                "errors": context.errors
            }

        except Exception as e:
            logger.error(f"트렌드 분석 실패: {e}", exc_info=True)
            return {
                "success": False,
                "session_id": context.session_id,
                "reply_text": f"트렌드 분석 중 오류가 발생했습니다: {str(e)}",
                "result_data": None,
                "errors": [str(e)]
            }

    def _generate_mock_response(self, context: TrendAgentContext) -> str:
        """모의 응답 생성 (팀원이 실제 구현으로 교체)"""
        return f"""📈 **트렌드 분석 결과**

요청하신 내용: {context.user_message}

**현재 상태:** 🚧 개발 중

팀원이 구현할 기능:
1. 키워드 추출 및 트렌드 데이터 조회
2. Google Trends / Naver DataLab API 연동
3. 시계열 데이터 분석
4. 연관 검색어 추출
5. LLM 기반 인사이트 생성

**다음 단계:**
- `backend/app/agents/trend_agent.py`를 수정하세요
- `backend/app/tools/trend_tools.py`에 도구 함수를 추가하세요
- `.env`에 필요한 API 키를 추가하세요
"""


# 싱글톤 인스턴스
agent = TrendAgent()


def run_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    """헬퍼 함수"""
    if not session_id:
        with get_db() as db:
            session = create_session(db)
            session_id = session.id

    return agent.run(session_id, user_message)
