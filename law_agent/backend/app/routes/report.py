"""
리포트 다운로드 라우트
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import logging
from pathlib import Path

from app.db.session import get_db
from app.db.crud import get_calc_result_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/report/{report_id}")
async def download_report(report_id: str):
    """
    PDF 리포트 다운로드

    Args:
        report_id: 계산 결과 ID

    Returns:
        PDF 파일 스트림
    """
    try:
        logger.info(f"리포트 다운로드 요청: {report_id}")

        # DB에서 리포트 조회 및 데이터 추출 (세션 내에서)
        with get_db() as db:
            result = get_calc_result_by_id(db, report_id)

            if not result:
                raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")

            # 세션 내에서 데이터 추출
            pdf_path_str = result.pdf_path
            corp_name = result.corp_name

        # PDF 경로 확인
        if not pdf_path_str:
            raise HTTPException(status_code=404, detail="PDF 파일이 생성되지 않았습니다.")

        # 파일 존재 확인
        pdf_path = Path(pdf_path_str)
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF 파일이 존재하지 않습니다.")

        logger.info(f"리포트 전송: {pdf_path}")

        # 파일 반환
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"{corp_name}_tax_report.pdf"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"리포트 다운로드 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
