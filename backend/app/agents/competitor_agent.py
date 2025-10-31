"""
경쟁사 분석 에이전트
경쟁 제품/서비스의 가격, 스펙, 리뷰 비교 분석
"""
import logging
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.db.crud import append_message, create_session, get_session

logger = logging.getLogger(__name__)


class CompetitorAgentContext:
    """경쟁사 분석 컨텍스트"""

    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.products: list = []
        self.comparison_result: Optional[Dict[str, Any]] = None
        self.swot_analysis: Optional[Dict[str, Any]] = None
        self.errors: list = []


class CompetitorAgent:
    """경쟁사 분석 에이전트"""

    def __init__(self):
        self.name = "CompetitorAgent"

    def run(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """에이전트 실행"""
        logger.info(f"경쟁사 분석 시작 (세션: {session_id})")

        context = CompetitorAgentContext(session_id, user_message)

        try:
            with get_db() as db:
                if not session_id:
                    session = create_session(db)
                    context.session_id = session.id
                else:
                    session = get_session(db, session_id)
                    if not session:
                        session = create_session(db)
                        context.session_id = session.id

                append_message(db, context.session_id, "system", "--- 경쟁사 분석 시작 ---")
                append_message(db, context.session_id, "user", context.user_message)

            # TODO: 팀원이 구현
            # 1. 경쟁 제품 URL 또는 정보 입력
            # 2. 가격, 스펙, 리뷰 점수 수집
            # 3. 비교 테이블 생성
            # 4. SWOT 분석
            # 5. 차별화 포인트 제안

            reply_text = self._generate_mock_response(context)

            with get_db() as db:
                append_message(db, context.session_id, "assistant", reply_text)

            return {
                "success": True,
                "session_id": context.session_id,
                "reply_text": reply_text,
                "result_data": {
                    "comparison": context.comparison_result,
                    "swot": context.swot_analysis
                },
                "errors": context.errors
            }

        except Exception as e:
            logger.error(f"경쟁사 분석 실패: {e}", exc_info=True)
            return {
                "success": False,
                "session_id": context.session_id,
                "reply_text": f"오류 발생: {str(e)}",
                "result_data": None,
                "errors": [str(e)]
            }

    def _generate_mock_response(self, context: CompetitorAgentContext) -> str:
        """모의 응답"""
        return f"""🔍 **경쟁사 분석**

요청: {context.user_message}

**현재 상태:** 🚧 개발 중

팀원이 구현할 기능:
1. 경쟁 제품 정보 수집 (크롤링/API)
2. 가격 비교 분석
3. 스펙/기능 비교 테이블 생성
4. 리뷰 점수 비교
5. SWOT 분석
6. 차별화 포인트 및 전략 제안

**필요 API:**
- 네이버쇼핑 API
- 쿠팡 파트너스 API
- BeautifulSoup / Selenium (크롤링)

**파일 수정:**
- `backend/app/agents/competitor_agent.py`
- `backend/app/tools/competitor_tools.py`
"""


agent = CompetitorAgent()


def run_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    if not session_id:
        with get_db() as db:
            session = create_session(db)
            session_id = session.id
    return agent.run(session_id, user_message)
