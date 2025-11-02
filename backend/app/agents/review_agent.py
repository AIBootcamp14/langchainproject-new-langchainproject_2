"""
리뷰 감성 분석 에이전트
제품 리뷰의 감성 분석 및 주요 토픽 추출
"""
import logging
import json
from typing import Dict, Any, Optional

from app.db.session import get_db
from app.db.crud import append_message, create_session, get_session
from app.tools.segment_tools import extract_product_name, collect_review_data
from app.tools.review_tools import analyze_sentiment, extract_topics, summarize_reviews, identify_improvement_areas, generate_review_report_pdf

logger = logging.getLogger(__name__)


class ReviewAgentContext:
    """리뷰 감성 분석 컨텍스트"""

    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.product_name: Optional[str] = None
        self.reviews: list = []
        self.sentiment_result: Optional[Dict[str, Any]] = None
        self.topics: list = []
        self.summary: Optional[str] = None
        self.improvements_area: Optional[str] = None
        self.pdf_path: Optional[str] = None
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

                append_message(db, context.session_id, "system", "--- 리뷰 감성 분석 시작 ---")
                append_message(db, context.session_id, "user", context.user_message)

            # Step 1: 제품명 추출
            logger.info("Step 1: 제품명 추출")
            context.product_name = extract_product_name(context.user_message)

            if not context.product_name:
                context.errors.append("제품명을 찾을 수 없습니다.")
                reply_text = "제품명을 명확히 지정해주세요. 예: '에어팟 프로 구매자들의 리뷰 감성 분석을 진행해줘'"
                with get_db() as db:
                    append_message(db, context.session_id, "assistant", reply_text)
                return {
                    "success": False,
                    "session_id": context.session_id,
                    "reply_text": reply_text,
                    "result_data": None,
                    "errors": context.errors
                }

            # Step 2: 리뷰 데이터 수집
            logger.info(f"Step 2: '{context.product_name}' 리뷰 데이터 수집")
            context.reviews = collect_review_data(context.product_name)

            if not context.reviews:
                context.errors.append("리뷰 데이터를 수집할 수 없습니다.")
                reply_text = f"'{context.product_name}'에 대한 데이터를 찾을 수 없습니다. 다른 제품을 시도해보세요."
                with get_db() as db:
                    append_message(db, context.session_id, "assistant", reply_text)
                return {
                    "success": False,
                    "session_id": context.session_id,
                    "reply_text": reply_text,
                    "result_data": None,
                    "errors": context.errors
                }
            
            # Step 3: LLM으로 리뷰 감성 분석
            logger.info(f"Step 3: LLM 리뷰 감성 분석 ({len(context.reviews)}개 리뷰)")
            context.sentiment_result = analyze_sentiment(context.reviews, context.product_name)

            # Step 4: 주요 토픽 추출
            logger.info("Step 4: 주요 토픽 추출")
            context.topics = extract_topics(context.reviews)

            # Step 5: 리뷰 요약
            logger.info("Step 5: 리뷰 요약 생성")
            context.summary = summarize_reviews(context.reviews, context.product_name)

            # Step 6: 개선점 파악
            logger.info("Step 6: 개선점 파악")
            context.improvements_area = identify_improvement_areas(context.reviews)

            # Step 7: 결과 요약 및 리포트 생성
            logger.info("Step 7: 결과 요약 및 리포트 생성")
            context.pdf_path = generate_review_report_pdf(
                sentiment_result=context.sentiment_result,
                topics=context.topics,
                summary=context.summary,
                improvements_area=context.improvements_area,
                product_name=context.product_name
            )

            # Step 8: 최종 응답 생성
            logger.info("Step 8: 최종 응답 생성")
            # reply_text = self._generate_mock_response(context)
            reply_text = self._generate_final_response(context)

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
    
    def _generate_final_response(self, context: ReviewAgentContext) -> str:
        """최종 응답 생성"""
        sentiment = context.sentiment_result
        improvement_area = "\n- ".join(context.improvements_area)

        response = f"""✅ **{context.product_name} 구매자 리뷰 감성 분석 완료**

        
📊 **감성 분석 결과:**
전체 리뷰 수: {sentiment.get("total_reviews")}
긍정 리뷰 수: {sentiment.get("sentiment_distribution").get("positive")}
부정 리뷰 수: {sentiment.get("sentiment_distribution").get("negative")}
중립 리뷰 수: {sentiment.get("sentiment_distribution").get("neutral")}
평균 점수: {sentiment.get("average_score")}

📖 **주요 토픽:**
{", ".join(context.topics)}


✒️ **리뷰 요약:**
{context.summary}

👁️ **전체 인사이트:**
{sentiment.get("overall_insights")}


🛠️ **개선이 필요한 영역:**
- {improvement_area}"""

        if context.pdf_path:
            import os
            pdf_filename = os.path.basename(context.pdf_path)
            response += f"\n\n\n📄 [리뷰 분석 리포트 다운로드](/report/{pdf_filename})"

        return response


agent = ReviewAgent()


def run_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    if not session_id:
        with get_db() as db:
            session = create_session(db)
            session_id = session.id
    return agent.run(session_id, user_message)
