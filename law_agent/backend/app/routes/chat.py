"""
채팅 라우트
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging

from app.schemas.dto import ChatRequest, ChatResponse
from app.agents.corp_tax_agent import run_agent

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    채팅 엔드포인트

    사용자 메시지를 받아 에이전트를 실행하고 응답 반환
    """
    try:
        logger.info(f"채팅 요청 수신: {request.message[:50]}...")

        # 에이전트 실행
        result = run_agent(
            session_id=request.session_id or "",
            user_message=request.message
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("reply_text", "에이전트 실행 실패")
            )

        # 응답 구성
        response = ChatResponse(
            session_id=result["session_id"],
            reply_text=result["reply_text"],
            report_id=result.get("report_id"),
            download_url=result.get("download_url")
        )

        logger.info(f"채팅 응답 반환 (세션: {response.session_id})")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 처리 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
