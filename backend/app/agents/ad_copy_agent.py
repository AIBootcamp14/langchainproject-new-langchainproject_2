"""
광고 문구 생성 에이전트
LLM을 활용한 다양한 광고 카피 생성
"""
import logging
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.db.crud import append_message, create_session, get_session

logger = logging.getLogger(__name__)


class AdCopyAgentContext:
    """광고 문구 생성 컨텍스트"""

    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.product_info: Optional[str] = None
        self.ad_variations: list = []
        self.errors: list = []


class AdCopyAgent:
    """광고 문구 생성 에이전트"""

    def __init__(self):
        self.name = "AdCopyAgent"

    def run(self, session_id: str, user_message: str) -> Dict[str, Any]:
        """에이전트 실행"""
        logger.info(f"광고 문구 생성 시작 (세션: {session_id})")

        context = AdCopyAgentContext(session_id, user_message)

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

                append_message(db, context.session_id, "system", "--- 광고 문구 생성 시작 ---")
                append_message(db, context.session_id, "user", context.user_message)

            # TODO: 팀원이 구현
            # 1. 제품 정보 추출
            # 2. LLM으로 다양한 광고 문구 생성
            # 3. 길이별/톤앤매너별 배리에이션 생성

            reply_text = self._generate_mock_response(context)

            with get_db() as db:
                append_message(db, context.session_id, "assistant", reply_text)

            return {
                "success": True,
                "session_id": context.session_id,
                "reply_text": reply_text,
                "result_data": {"variations": context.ad_variations},
                "errors": context.errors
            }

        except Exception as e:
            logger.error(f"광고 문구 생성 실패: {e}", exc_info=True)
            return {
                "success": False,
                "session_id": context.session_id,
                "reply_text": f"오류 발생: {str(e)}",
                "result_data": None,
                "errors": [str(e)]
            }

    def _generate_mock_response(self, context: AdCopyAgentContext) -> str:
        """모의 응답"""
        return f"""✍️ **광고 문구 생성**

요청: {context.user_message}

**현재 상태:** 🚧 개발 중

팀원이 구현할 기능:
1. 제품/서비스 정보 추출
2. LLM 기반 광고 문구 생성 (다양한 배리에이션)
3. 길이별 생성 (짧은/중간/긴 카피)
4. 톤앤매너 조절 (공식적/친근함/유머)
5. A/B 테스트용 다중 버전 생성

**파일 수정:**
- `backend/app/agents/ad_copy_agent.py`
- `backend/app/tools/ad_tools.py`
"""


agent = AdCopyAgent()


def run_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    if not session_id:
        with get_db() as db:
            session = create_session(db)
            session_id = session.id
    return agent.run(session_id, user_message)
