"""
PDF 리포트 생성 도구
ReportLab을 사용한 세그먼트 및 트렌드 분석 리포트 생성 (한글 지원)
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import re
import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

# 한글 폰트 전역 변수
_FONT_REGISTERED = False


def register_korean_font() -> None:
    """한글 폰트 등록 (프로젝트 로컬 폰트 우선)"""
    global _FONT_REGISTERED

    if _FONT_REGISTERED:
        return

    try:
        backend_root = Path(__file__).resolve().parents[2]
        local_font_dir = backend_root / "font"

        regular_path = local_font_dir / "malgun.ttf"
        bold_path = local_font_dir / "malgunbd.ttf"

        fonts_loaded = False

        if regular_path.exists():
            pdfmetrics.registerFont(TTFont("MalgunGothic", str(regular_path)))
            logger.info("한글 폰트 등록 성공: %s", regular_path)
            fonts_loaded = True
        else:
            logger.warning("맑은 고딕 Regular 폰트를 찾을 수 없습니다: %s", regular_path)

        if bold_path.exists():
            pdfmetrics.registerFont(TTFont("MalgunGothic-Bold", str(bold_path)))
            logger.info("한글 폰트 등록 성공: %s", bold_path)
            fonts_loaded = True
        else:
            logger.warning("맑은 고딕 Bold 폰트를 찾을 수 없습니다: %s", bold_path)

        if not fonts_loaded:
            logger.warning("backend/font 디렉터리에서 폰트를 찾지 못했습니다. 시스템 기본 경로를 시도합니다.")
            fallback_regular = Path(r"C:\\Windows\\Fonts\\malgun.ttf")
            fallback_bold = Path(r"C:\\Windows\\Fonts\\malgunbd.ttf")

            if fallback_regular.exists():
                pdfmetrics.registerFont(TTFont("MalgunGothic", str(fallback_regular)))
                logger.info("fallback 폰트 등록 성공: %s", fallback_regular)
                fonts_loaded = True
            if fallback_bold.exists():
                pdfmetrics.registerFont(TTFont("MalgunGothic-Bold", str(fallback_bold)))
                logger.info("fallback 폰트 등록 성공: %s", fallback_bold)
                fonts_loaded = True

        if not fonts_loaded:
            raise FileNotFoundError("맑은 고딕 폰트를 찾지 못했습니다. backend/font 디렉터리를 확인하세요.")

        _FONT_REGISTERED = True

    except Exception as exc:  # pragma: no cover - 폰트 로딩 문제는 런타임 확인
        logger.error("한글 폰트 등록 실패: %s", exc)
        raise


def create_segment_report_pdf(segments: Dict[str, Any], product_name: str) -> str:
    """세그먼트 분석 PDF 리포트 생성"""
    logger.info("PDF 생성 시작: %s", product_name)

    register_korean_font()

    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        logger.info("리포트 폴더 생성: %s", reports_dir)

    file_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"segment_report_{timestamp}_{file_id}.pdf"
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story: List[Any] = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontName="MalgunGothic-Bold",
        fontSize=24,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontName="MalgunGothic-Bold",
        fontSize=16,
        textColor=colors.HexColor("#34495E"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontName="MalgunGothic",
        fontSize=10,
        leading=16,
    )
    segment_title_style = ParagraphStyle(
        "SegmentTitle",
        parent=styles["Heading3"],
        fontName="MalgunGothic-Bold",
        fontSize=14,
        textColor=colors.HexColor("#3498DB"),
        spaceAfter=10,
    )

    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("고객 세그먼트 분석 리포트", title_style))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(f"제품: {product_name}", heading_style))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", body_style))
    story.append(PageBreak())

    story.append(Paragraph("요약", heading_style))
    story.append(Spacer(1, 0.3 * cm))

    overview_text = (
        f"총 세그먼트 수: {segments.get('total_segments', 0)}<br/><br/>"
        f"전체 인사이트: {segments.get('overall_insights', 'N/A')}"
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("세그먼트 상세 분석", heading_style))
    story.append(Spacer(1, 0.5 * cm))

    for index, segment in enumerate(segments.get("segments", []), start=1):
        segment_title = f"{index}. {segment.get('name', f'세그먼트 {index}')} ({segment.get('percentage', 0)}%)"
        story.append(Paragraph(segment_title, segment_title_style))

        segment_data = [
            ["특성", segment.get("characteristics", "N/A")],
            ["인구통계", segment.get("demographics", "N/A")],
            ["니즈", segment.get("needs", "N/A")],
            ["마케팅 전략", segment.get("marketing_strategy", "N/A")],
        ]

        segment_table = Table(segment_data, colWidths=[4 * cm, 13 * cm])
        segment_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ECF0F1")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "MalgunGothic-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "MalgunGothic"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(segment_table)
        story.append(Spacer(1, 0.8 * cm))

    story.append(PageBreak())

    story.append(Paragraph("세그먼트 요약 테이블", heading_style))
    story.append(Spacer(1, 0.5 * cm))

    summary_data = [["세그먼트", "비율", "주요 특성"]]
    for segment in segments.get("segments", []):
        characteristics = segment.get("characteristics", "N/A")
        if len(characteristics) > 60:
            characteristics = characteristics[:60] + "..."
        summary_data.append(
            [segment.get("name", "N/A"), f"{segment.get('percentage', 0)}%", characteristics]
        )

    summary_table = Table(summary_data, colWidths=[5 * cm, 3 * cm, 9 * cm])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498DB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "MalgunGothic-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "MalgunGothic"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, 0), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
            ]
        )
    )

    story.append(summary_table)
    story.append(Spacer(1, 1 * cm))

    story.append(Spacer(1, 2 * cm))
    disclaimer = (
        "<b>면책 조항</b><br/>"
        "본 리포트는 온라인 리뷰 데이터 분석을 기반으로 AI/ML 기술을 사용하여 생성되었습니다."\
        " 제공된 인사이트와 권장사항은 참고용이며, 실제 마케팅 전략 수립 전에"\
        " 시장 조사 및 검증을 권장합니다."
    )
    story.append(
        Paragraph(
            disclaimer,
            ParagraphStyle(
                "Disclaimer",
                parent=styles["Normal"],
                fontName="MalgunGothic",
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                leading=12,
            ),
        )
    )

    try:
        doc.build(story)
        logger.info("PDF 생성 완료: %s", filepath)
        return filepath
    except Exception as exc:  # pragma: no cover - ReportLab 내부 오류는 런타임 확인
        logger.error("PDF 빌드 실패: %s", exc, exc_info=True)
        raise


def create_trend_report_pdf(keyword: str, trend_data: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """트렌드 분석 PDF 리포트 생성"""
    logger.info("트렌드 리포트 PDF 생성 시작: %s", keyword)

    register_korean_font()

    reports_dir = "reports"
    os.makedirs(reports_dir, exist_ok=True)

    safe_keyword = re.sub(r"[^0-9A-Za-z가-힣]+", "_", keyword).strip("_") or "trend"
    file_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"trend_report_{safe_keyword[:20]}_{timestamp}_{file_id}.pdf"
    filepath = os.path.join(reports_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story: List[Any] = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TrendTitle",
        parent=styles["Heading1"],
        fontName="MalgunGothic-Bold",
        fontSize=24,
        textColor=colors.HexColor("#1B4F72"),
        spaceAfter=24,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "TrendHeading",
        parent=styles["Heading2"],
        fontName="MalgunGothic-Bold",
        fontSize=16,
        textColor=colors.HexColor("#2E86C1"),
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "TrendBody",
        parent=styles["BodyText"],
        fontName="MalgunGothic",
        fontSize=10,
        leading=16,
    )

    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("트렌드 분석 리포트", title_style))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"키워드: {keyword}", heading_style))
    period_text = f"분석 기간: {analysis.get('start_date', 'N/A')} ~ {analysis.get('end_date', 'N/A')}"
    if analysis.get("time_unit"):
        period_text += f" (단위: {analysis.get('time_unit')})"
    story.append(Paragraph(period_text, body_style))
    story.append(Paragraph(f"생성일시: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}", body_style))
    story.append(PageBreak())

    story.append(Paragraph("요약", heading_style))
    story.append(Spacer(1, 0.2 * cm))

    summary_lines: List[str] = []
    if analysis.get("signal"):
        summary_lines.append(f"• 추세 해석: {analysis['signal']}")
    if analysis.get("confidence"):
        summary_lines.append(f"• 데이터 신뢰도: {analysis['confidence']}")

    summary_body = analysis.get("summary")
    if summary_body:
        summary_lines.append("• 핵심 요약:")
        for sub_line in _split_lines(summary_body):
            bullet_text = sub_line.lstrip("• ").strip()
            summary_lines.append(f"   • {bullet_text}")

    if summary_lines:
        for line in summary_lines:
            story.append(Paragraph(_strip_markdown(line), body_style))
        story.append(Spacer(1, 0.3 * cm))
    else:
        story.append(Paragraph("요약 정보를 생성할 수 없습니다.", body_style))

    if analysis.get("insight"):
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("추천 인사이트", heading_style))
        for line in _split_lines(analysis["insight"]):
            story.append(Paragraph(line, body_style))

    story.append(PageBreak())

    story.append(Paragraph("핵심 지표", heading_style))
    story.append(Spacer(1, 0.2 * cm))
    naver_metrics = analysis.get("naver", {}) or {}
    metrics_data = [
        [Paragraph("<b>지표</b>", body_style), Paragraph("<b>값</b>", body_style)],
        [Paragraph("평균 지수", body_style), Paragraph(_format_metric(naver_metrics.get("average")), body_style)],
        [Paragraph("최신 지수", body_style), Paragraph(_format_metric(naver_metrics.get("latest_value"), integer=True), body_style)],
        [Paragraph("최근 모멘텀", body_style), Paragraph(_format_percentage(naver_metrics.get("momentum_pct"), naver_metrics.get("momentum_label")), body_style)],
        [Paragraph("첫 시점 대비 변화", body_style), Paragraph(_format_percentage(naver_metrics.get("growth_pct")), body_style)],
    ]

    peak = naver_metrics.get("peak")
    if peak:
        metrics_data.append(
            [
                Paragraph("검색 피크", body_style),
                Paragraph(
                    f"{peak.get('date', 'N/A')} / {_format_metric(peak.get('value'), integer=True)}",
                    body_style,
                ),
            ]
        )

    metrics_table = Table(metrics_data, colWidths=[5 * cm, 11 * cm])
    metrics_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E86C1")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "MalgunGothic-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 1), (-1, -1), "MalgunGothic"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8F9F9")),
            ]
        )
    )
    story.append(metrics_table)

    clusters = analysis.get("clusters") or []
    if clusters:
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph("연관 키워드 클러스터", heading_style))
        story.append(Spacer(1, 0.2 * cm))

        cluster_headers = [
            Paragraph("<b>클러스터</b>", body_style),
            Paragraph("<b>대표 키워드</b>", body_style),
            Paragraph("<b>추세</b>", body_style),
            Paragraph("<b>변화율</b>", body_style),
            Paragraph("<b>인사이트</b>", body_style),
        ]

        cluster_rows: List[List[Any]] = [cluster_headers]
        for cluster in clusters:
            keywords = cluster.get("keywords", [])[:6]
            keywords_text = ", ".join(keywords)
            change_text = _format_percentage(cluster.get("change_pct"))
            insight_text = _strip_markdown(cluster.get("insight", "")).replace("\n", " ")
            if len(insight_text) > 220:
                insight_text = insight_text[:220] + "..."

            cluster_rows.append(
                [
                    Paragraph(_strip_markdown(cluster.get("name", "클러스터")), body_style),
                    Paragraph(_strip_markdown(keywords_text or "-"), body_style),
                    Paragraph(_strip_markdown(cluster.get("trend_label", "N/A")), body_style),
                    Paragraph(change_text, body_style),
                    Paragraph(insight_text, body_style),
                ]
            )

        cluster_table = Table(cluster_rows, colWidths=[3.5 * cm, 4.5 * cm, 2.2 * cm, 2.2 * cm, 5.6 * cm])
        cluster_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5B2C6F")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "MalgunGothic-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "MalgunGothic"),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("ALIGN", (0, 1), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("FONTSIZE", (0, 1), (-1, -1), 8.5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4ECF7")]),
                ]
            )
        )
        story.append(cluster_table)

    story.append(PageBreak())

    story.append(Paragraph("최근 검색 추이", heading_style))
    story.append(Spacer(1, 0.2 * cm))
    recent_rows = [["날짜", "검색 지수"]]
    tail_series = naver_metrics.get("series_tail") or []
    if tail_series:
        for point in tail_series:
            recent_rows.append([point.get("date", "N/A"), _format_metric(point.get("value"), integer=True)])
    else:
        recent_rows.append(["데이터 없음", "-"])

    recent_table = Table(recent_rows, colWidths=[8 * cm, 8 * cm])
    recent_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1ABC9C")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "MalgunGothic-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "MalgunGothic"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F7")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(recent_table)

    detailed_rows = _build_detailed_series_rows(trend_data.get("naver"), keyword)
    if detailed_rows:
        story.append(PageBreak())
        story.append(Paragraph("상세 시계열 데이터", heading_style))
        story.append(Spacer(1, 0.2 * cm))
        detail_table = Table(detailed_rows, colWidths=[5.5 * cm, 5.5 * cm, 5 * cm])
        detail_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7D3C98")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "MalgunGothic-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "MalgunGothic"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9EBEA")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(detail_table)

    story.append(Spacer(1, 1.5 * cm))
    disclaimer = (
        "<b>면책 조항</b><br/>"
        "본 리포트는 Naver DataLab 공개 데이터를 기반으로 AI가 생성한 분석 자료입니다.<br/>"
        "전략 수립 시 추가적인 시장 조사 및 검증을 병행하시기를 권장드립니다."
    )
    story.append(
        Paragraph(
            disclaimer,
            ParagraphStyle(
                "TrendDisclaimer",
                parent=styles["Normal"],
                fontName="MalgunGothic",
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                leading=12,
            ),
        )
    )

    try:
        doc.build(story)
        logger.info("트렌드 리포트 PDF 생성 완료: %s", filepath)
        return filepath
    except Exception as exc:  # pragma: no cover - ReportLab 내부 오류는 런타임 확인
        logger.error("트렌드 리포트 PDF 생성 실패: %s", exc, exc_info=True)
        raise


def get_pdf_download_url(pdf_path: str) -> Optional[str]:
    """PDF 다운로드 URL 생성"""
    if not pdf_path:
        return None
    filename = os.path.basename(pdf_path)
    return f"/report/{filename}"


def _format_metric(value: Optional[float], integer: bool = False) -> str:
    if value is None:
        return "N/A"
    try:
        if integer:
            return f"{float(value):.0f}"
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return str(value)


def _format_percentage(value: Optional[float], label: Optional[str] = None) -> str:
    if value is None:
        return "N/A"
    try:
        pct_text = f"{float(value):+.1f}%"
    except (TypeError, ValueError):
        pct_text = str(value)
    if label:
        return f"{label} ({pct_text})"
    return pct_text


def _build_detailed_series_rows(naver_data: Optional[Dict[str, Any]], keyword: str) -> List[List[str]]:
    if not naver_data:
        return []

    rows: List[List[str]] = [["그룹", "날짜", "지수"]]
    if "results" in naver_data:
        for entry in naver_data.get("results", []):
            group = entry.get("group") or entry.get("title") or entry.get("keywords", [""])[0]
            for point in entry.get("series", [])[:60]:
                rows.append(
                    [
                        group,
                        point.get("date", "N/A"),
                        _format_metric(point.get("value"), integer=True),
                    ]
                )
    elif "data" in naver_data:
        for item in naver_data.get("data", [])[:60]:
            rows.append(
                [
                    keyword,
                    item.get("period", "N/A"),
                    _format_metric(item.get("ratio"), integer=True),
                ]
            )

    return rows if len(rows) > 1 else []


def _strip_markdown(text: Optional[str]) -> str:
    if not text:
        return ""

    cleaned = str(text).replace("\r\n", "\n")
    cleaned = re.sub(r"```.*?```", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"_(.*?)_", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]*)`", r"\1", cleaned)
    cleaned = re.sub(r"^-\s+", "• ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^>\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+(\n)", r"\1", cleaned)
    return cleaned.strip()


def _split_lines(text: Optional[str]) -> List[str]:
    cleaned = _strip_markdown(text)
    return [line.strip() for line in cleaned.split("\n") if line.strip()]
