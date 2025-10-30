"""
리뷰 감성 분석 에이전트
제품 리뷰의 감성 분석 및 주요 토픽 추출
"""
import logging
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.db.crud import append_message, create_session, get_session

logger = logging.getLogger(__name__)


class ReviewAgentContext:
    """리뷰 감성 분석 컨텍스트"""

    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.reviews: list = []
        self.sentiment_result: Optional[Dict[str, Any]] = None
        self.topics: list = []
        self.errors: list = []


class ReviewAgent:
    """리뷰 감성 분석 에이전트"""

    def __init__(self):
        self.name = "ReviewAgent"

    def run(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """에이전트 실행"""
        logger.info(f"리뷰 감성 분석 시작 (세션: {session_id})")

        context = ReviewAgentContext(session_id, user_message)

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

                append_message(db, context.session_id, "system", "--- 리뷰 감성 분석 시작 ---")
                append_message(db, context.session_id, "user", context.user_message)

            # TODO: 팀원이 구현
            # 1. 제품 URL 또는 리뷰 텍스트 입력
            # 2. 리뷰 크롤링 (필요시)
            # 3. 감성 분석 (긍정/부정/중립)
            # 4. 주요 키워드/토픽 추출
            # 5. 개선점 요약

            reply_text = self._generate_mock_response(context)

            with get_db() as db:
                append_message(db, context.session_id, "assistant", reply_text)

            return {
                "success": True,
                "session_id": context.session_id,
                "reply_text": reply_text,
                "result_data": {
                    "sentiment": context.sentiment_result,
                    "topics": context.topics
                },
                "errors": context.errors
            }

        except Exception as e:
            logger.error(f"리뷰 감성 분석 실패: {e}", exc_info=True)
            return {
                "success": False,
                "session_id": context.session_id,
                "reply_text": f"오류 발생: {str(e)}",
                "result_data": None,
                "errors": [str(e)]
            }

    def _generate_mock_response(self, context: ReviewAgentContext) -> str:
        """모의 응답"""
        return f"""😊 **리뷰 감성 분석**

요청: {context.user_message}

**현재 상태:** 🚧 개발 중

팀원이 구현할 기능:
1. 리뷰 데이터 수집 (크롤링 또는 직접 입력)
2. 감성 분석 (긍정/부정/중립 분류)
3. 주요 토픽 추출 (LDA, LLM 활용)
4. 키워드 빈도 분석
5. 개선점 및 강점 요약

**필요 API/라이브러리:**
- OpenAI API (감성 분석)
- BeautifulSoup / Selenium (크롤링)
- KoNLPy (한국어 형태소 분석)

**파일 수정:**
- `backend/app/agents/review_agent.py`
- `backend/app/tools/review_tools.py`
"""


agent = ReviewAgent()


def run_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    if not session_id:
        with get_db() as db:
            session = create_session(db)
            session_id = session.id
    return agent.run(session_id, user_message)
