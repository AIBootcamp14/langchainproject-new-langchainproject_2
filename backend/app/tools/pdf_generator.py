"""
PDF 리포트 생성 도구
ReportLab을 사용한 세그먼트 분석 리포트 생성 (한글 지원)
"""
import logging
from typing import Dict, Any
from datetime import datetime
import os
import uuid

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

# 한글 폰트 전역 변수
_FONT_REGISTERED = False


def register_korean_font():
    """한글 폰트 등록 (윈도우 맑은 고딕 사용)"""
    global _FONT_REGISTERED

    if _FONT_REGISTERED:
        return

    try:
        # 윈도우 기본 폰트 경로
        font_paths = [
            r"C:\Windows\Fonts\malgun.ttf",  # 맑은 고딕 Regular
            r"C:\Windows\Fonts\malgunbd.ttf",  # 맑은 고딕 Bold
        ]

        # Regular 폰트 등록
        if os.path.exists(font_paths[0]):
            pdfmetrics.registerFont(TTFont('MalgunGothic', font_paths[0]))
            logger.info("한글 폰트 등록 성공: 맑은 고딕 Regular")
        else:
            logger.warning(f"맑은 고딕 Regular 폰트를 찾을 수 없습니다: {font_paths[0]}")

        # Bold 폰트 등록
        if os.path.exists(font_paths[1]):
            pdfmetrics.registerFont(TTFont('MalgunGothic-Bold', font_paths[1]))
            logger.info("한글 폰트 등록 성공: 맑은 고딕 Bold")
        else:
            logger.warning(f"맑은 고딕 Bold 폰트를 찾을 수 없습니다: {font_paths[1]}")

        _FONT_REGISTERED = True

    except Exception as e:
        logger.error(f"한글 폰트 등록 실패: {e}")
        raise


def create_segment_report_pdf(segments: Dict[str, Any], product_name: str) -> str:
    """
    세그먼트 분석 PDF 리포트 생성 (한글 지원)

    Args:
        segments: 세그먼트 분석 결과
        product_name: 제품명

    Returns:
        생성된 PDF 파일 경로
    """
    logger.info(f"PDF 생성 시작: {product_name}")

    # 한글 폰트 등록
    register_korean_font()

    # reports 폴더 확인/생성
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        logger.info(f"리포트 폴더 생성: {reports_dir}")

    # 파일명 생성
    file_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"segment_report_{timestamp}_{file_id}.pdf"
    filepath = os.path.join(reports_dir, filename)

    # PDF 문서 생성
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []

    # 스타일 정의 (한글 폰트 적용)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName='MalgunGothic-Bold',
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName='MalgunGothic-Bold',
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='MalgunGothic',
        fontSize=10,
        leading=16
    )

    segment_title_style = ParagraphStyle(
        'SegmentTitle',
        parent=styles['Heading3'],
        fontName='MalgunGothic-Bold',
        fontSize=14,
        textColor=colors.HexColor('#3498DB'),
        spaceAfter=10
    )

    # 표지
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph(f"고객 세그먼트 분석 리포트", title_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"제품: {product_name}", heading_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", body_style))
    story.append(PageBreak())

    # 개요 섹션
    story.append(Paragraph("요약", heading_style))
    story.append(Spacer(1, 0.3 * cm))

    overview_text = f"총 세그먼트 수: {segments.get('total_segments', 0)}<br/><br/>"
    overview_text += f"전체 인사이트: {segments.get('overall_insights', 'N/A')}"
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 1 * cm))

    # 세그먼트별 상세 분석
    story.append(Paragraph("세그먼트 상세 분석", heading_style))
    story.append(Spacer(1, 0.5 * cm))

    for i, segment in enumerate(segments.get('segments', []), 1):
        # 세그먼트 제목
        segment_title = f"{i}. {segment.get('name', f'세그먼트 {i}')} ({segment.get('percentage', 0)}%)"
        story.append(Paragraph(segment_title, segment_title_style))

        # 세그먼트 정보 테이블
        segment_data = [
            ["특성", segment.get('characteristics', 'N/A')],
            ["인구통계", segment.get('demographics', 'N/A')],
            ["니즈", segment.get('needs', 'N/A')],
            ["마케팅 전략", segment.get('marketing_strategy', 'N/A')]
        ]

        segment_table = Table(segment_data, colWidths=[4 * cm, 13 * cm])
        segment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'MalgunGothic-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'MalgunGothic'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        story.append(segment_table)
        story.append(Spacer(1, 0.8 * cm))

    # 페이지 나누기
    story.append(PageBreak())

    # 요약 테이블
    story.append(Paragraph("세그먼트 요약 테이블", heading_style))
    story.append(Spacer(1, 0.5 * cm))

    summary_data = [["세그먼트", "비율", "주요 특성"]]
    for segment in segments.get('segments', []):
        characteristics = segment.get('characteristics', 'N/A')
        # 긴 텍스트 줄이기
        if len(characteristics) > 60:
            characteristics = characteristics[:60] + "..."

        summary_data.append([
            segment.get('name', 'N/A'),
            f"{segment.get('percentage', 0)}%",
            characteristics
        ])

    summary_table = Table(summary_data, colWidths=[5 * cm, 3 * cm, 9 * cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'MalgunGothic-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'MalgunGothic'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 1 * cm))

    # 면책 문구
    story.append(Spacer(1, 2 * cm))
    disclaimer = """
    <b>면책 조항</b><br/>
    본 리포트는 온라인 리뷰 데이터 분석을 기반으로 AI/ML 기술을 사용하여 생성되었습니다.
    제공된 인사이트와 권장사항은 참고용이며, 실제 마케팅 전략 수립 전에
    시장 조사 및 검증을 권장합니다.
    """
    story.append(Paragraph(disclaimer, ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='MalgunGothic',
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
        leading=12
    )))

    # PDF 빌드
    try:
        doc.build(story)
        logger.info(f"PDF 생성 완료: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"PDF 빌드 실패: {e}", exc_info=True)
        raise


def get_pdf_download_url(pdf_path: str) -> str:
    """
    PDF 다운로드 URL 생성

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        다운로드 URL
    """
    if not pdf_path:
        return None

    # 파일명만 추출
    filename = os.path.basename(pdf_path)
    return f"/report/{filename}"
