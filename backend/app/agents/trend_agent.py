"""
소비 트렌드 분석 에이전트
Google Trends, Naver DataLab 등을 활용한 트렌드 분석
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from app.db.session import get_db
from app.db.crud import append_message, create_session, get_session
from app.tools.trend_tools import (
    extract_trend_keyword,
    resolve_time_window,
    get_naver_datalab_trends,
    analyze_trend_data,
)
from app.tools.pdf_generator import (
    create_trend_report_pdf,
    get_pdf_download_url,
)

logger = logging.getLogger(__name__)


class TrendAgentContext:
    """트렌드 분석 에이전트 컨텍스트"""

    def __init__(self, session_id: str, user_message: str):
        self.session_id = session_id
        self.user_message = user_message
        self.keyword: Optional[str] = None
        self.start_date: Optional[str] = None
        self.end_date: Optional[str] = None
        self.time_unit: str = "week"
        self.window_days: Optional[int] = None
        self.trend_data: Optional[Dict[str, Any]] = None
        self.analysis_result: Optional[Dict[str, Any]] = None
        self.pdf_path: Optional[str] = None
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

            # Step 1: 키워드 추출
            logger.info("Step 1: 키워드 추출")
            context.keyword = extract_trend_keyword(context.user_message)

            if not context.keyword:
                logger.warning("키워드 추출 실패: %s", context.user_message)
                context.errors.append("키워드를 추출하지 못했습니다.")
                reply_text = (
                    "분석할 키워드를 찾지 못했습니다. "
                    "예: \"스마트워치 트렌드 알려줘\"처럼 제품이나 주제를 포함해 다시 요청해주세요."
                )
                with get_db() as db:
                    append_message(db, context.session_id, "assistant", reply_text)
                return {
                    "success": False,
                    "session_id": context.session_id,
                    "reply_text": reply_text,
                    "result_data": None,
                    "errors": context.errors,
                }

            # Step 2: 기간 해석 및 데이터 수집
            time_window = resolve_time_window(context.user_message)
            context.start_date = time_window["start_date"]
            context.end_date = time_window["end_date"]
            context.time_unit = time_window["time_unit"]
            context.window_days = time_window.get("days")

            logger.info(
                "Step 2: 트렌드 데이터 수집 (keyword=%s, period=%s~%s)",
                context.keyword,
                context.start_date,
                context.end_date,
            )
            naver_data = get_naver_datalab_trends(
                [context.keyword],
                context.start_date,
                context.end_date,
                time_unit=context.time_unit,
            )

            context.trend_data = {
                "keyword": context.keyword,
                "start_date": context.start_date,
                "end_date": context.end_date,
                "naver": naver_data,
                "time_unit": context.time_unit,
                "window_days": context.window_days,
                "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            }

            # Step 3: 데이터 분석 및 응답 생성
            logger.info("Step 3: 트렌드 데이터 분석")
            analysis = analyze_trend_data(context.trend_data)
            context.analysis_result = analysis
            context.trend_data["analysis"] = analysis

            try:
                context.pdf_path = create_trend_report_pdf(
                    context.keyword,
                    context.trend_data,
                    analysis,
                )
            except Exception as pdf_error:
                logger.error("트렌드 리포트 PDF 생성 실패: %s", pdf_error, exc_info=True)
                context.errors.append("트렌드 리포트 PDF 생성에 실패했습니다.")
                context.pdf_path = None

            reply_text = self._generate_final_response(context, analysis)

            # 응답 저장
            with get_db() as db:
                append_message(db, context.session_id, "assistant", reply_text)

            pdf_filename = os.path.basename(context.pdf_path) if context.pdf_path else None
            download_url = get_pdf_download_url(context.pdf_path) if context.pdf_path else None

            return {
                "success": True,
                "session_id": context.session_id,
                "reply_text": reply_text,
                "result_data": {
                    "keyword": context.keyword,
                    "start_date": context.start_date,
                    "end_date": context.end_date,
                    "time_unit": context.time_unit,
                    "trend_data": context.trend_data,
                    "analysis": context.analysis_result,
                },
                "report_id": pdf_filename,
                "download_url": download_url,
                "errors": context.errors,
            }

        except Exception as e:
            logger.error(f"트렌드 분석 실패: {e}", exc_info=True)
            return {
                "success": False,
                "session_id": context.session_id,
                "reply_text": f"트렌드 분석 중 오류가 발생했습니다: {str(e)}",
                "result_data": None,
                "errors": context.errors + [str(e)],
            }

    def _generate_final_response(self, context: TrendAgentContext, analysis: Dict[str, Any]) -> str:
        """최종 응답 생성"""

        def fmt_pct(value: Optional[float]) -> str:
            return f"{value:+.1f}%" if isinstance(value, (int, float)) else "N/A"

        def fmt_avg(value: Optional[float]) -> str:
            return f"{value:.1f}" if isinstance(value, (int, float)) else "N/A"

        def fmt_index(value: Optional[float]) -> str:
            return f"{value:.0f}" if isinstance(value, (int, float)) else "N/A"

        lines = []
        keyword = context.keyword or analysis.get("keyword", "")
        lines.append(f"📈 **'{keyword}' 트렌드 분석 요약**")
        lines.append("")

        if analysis.get("start_date") and analysis.get("end_date"):
            lines.append(
                f"- 분석 기간: {analysis['start_date']} ~ {analysis['end_date']} "
                f"(단위: {analysis.get('time_unit', '주간')})"
            )
        if analysis.get("confidence"):
            lines.append(f"- 데이터 신뢰도: {analysis['confidence']}")
        if analysis.get("signal"):
            lines.append(f"- 추세 해석: {analysis['signal']}")
        lines.append("")

        summary = analysis.get("summary")
        if summary:
            lines.append(summary)
            lines.append("")

        naver = analysis.get("naver", {})
        if naver.get("has_data"):
            lines.append("**Naver DataLab**")
            lines.append(f"- 평균 지수: {fmt_avg(naver.get('average'))}")
            lines.append(f"- 최신 지수: {fmt_index(naver.get('latest_value'))}")
            lines.append(
                f"- 최근 모멘텀: {naver.get('momentum_label')} "
                f"({fmt_pct(naver.get('momentum_pct'))})"
            )
            lines.append(f"- 첫 시점 대비 변화: {fmt_pct(naver.get('growth_pct'))}")
            peak = naver.get("peak")
            if peak and peak.get("date"):
                lines.append(
                    f"- 최고 지점: {peak['date']} (지수 {fmt_index(peak.get('value'))})"
                )
            lines.append("")
        else:
            lines.append("Naver DataLab 데이터가 충분하지 않습니다.")
            lines.append("")

        insight = analysis.get("insight")
        if insight:
            lines.append("**추천 인사이트**")
            lines.append(insight)
            lines.append("")

        sources = []
        if naver.get("has_data"):
            naver_source = "Naver DataLab"
            if naver.get("is_mock"):
                naver_source += " (모의)"
            sources.append(naver_source)
        else:
            sources.append("Naver DataLab (데이터 없음)")

        lines.append(f"🔗 데이터 출처: {', '.join(sources)}")
        lines.append("⚠️ 공개 데이터 기반 추정치이므로 의사결정 시 추가 검증이 필요합니다.")

        if context.pdf_path:
            filename = os.path.basename(context.pdf_path)
            lines.append("")
            lines.append("📄 **트렌드 리포트 PDF가 생성되었습니다.**")
            lines.append(f"파일명: `{filename}` (다운로드 메뉴에서 확인하세요)")

        return "\n".join(lines)


# 싱글톤 인스턴스
agent = TrendAgent()


def run_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    """헬퍼 함수"""
    if not session_id:
        with get_db() as db:
            session = create_session(db)
            session_id = session.id

    return agent.run(session_id, user_message)
