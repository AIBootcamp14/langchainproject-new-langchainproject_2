"""
트렌드 분석 도구
Naver DataLab API를 활용한 검색 트렌드 분석
"""
import json
import logging
import os
import re
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests

from app.tools.llm import call_llm_with_context

logger = logging.getLogger(__name__)

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_DATALAB_URL = os.getenv(
    "NAVER_DATALAB_URL",
    "https://openapi.naver.com/v1/datalab/search",
)

STOPWORDS = {
    "최근",
    "요즘",
    "트렌드",
    "trend",
    "분석",
    "알려줘",
    "해주세요",
    "해줘",
    "데이터",
    "시장",
    "어떻게",
    "요청",
    "보고",
    "정보",
    "관련",
    "대한",
    "입니다",
    "주세요",
    "please",
    "tell",
    "show",
    "about",
    "analysis",
    "정리",
    "해줘요",
    "알려주세요",
}


def extract_trend_keyword(user_message: str, fallback_to_llm: bool = True) -> Optional[str]:
    """사용자 메시지에서 분석 대상 키워드를 추출한다."""
    if not user_message:
        return None

    text = user_message.strip()
    if not text:
        return None

    quoted_matches = re.findall(r"[\"“”'‘’]([^\"“”'‘’]{2,})[\"“”'‘’]", text)
    for candidate in quoted_matches:
        cleaned = _clean_keyword(candidate)
        if cleaned:
            return cleaned

    hashtags = re.findall(r"#([A-Za-z0-9가-힣]+)", text)
    if hashtags:
        cleaned = _clean_keyword(hashtags[0])
        if cleaned:
            return cleaned

    patterns = (
        r"(?P<keyword>[가-힣A-Za-z0-9&\s]+?)\s*(?:트렌드|trend)\s*(?:분석|알려줘|데이터|현황|보고|파악)?",
        r"(?P<keyword>[가-힣A-Za-z0-9&\s]+?)\s*(?:시장|수요)\s*(?:전망|분석|어떻게|추이)",
        r"(?P<keyword>[가-힣A-Za-z0-9&\s]+?)\s*(?:에 대한|관련)\s*(?:트렌드|분석)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            cleaned = _clean_keyword(match.group("keyword"))
            if cleaned:
                return cleaned

    tokens = [token for token in re.split(r"[,\s]+", text) if token]
    filtered = [token for token in tokens if _is_meaningful_token(token)]
    if filtered:
        candidate = " ".join(filtered[:2]) if len(filtered) > 1 else filtered[0]
        cleaned = _clean_keyword(candidate)
        if cleaned:
            return cleaned

    if fallback_to_llm:
        return _extract_keyword_with_llm(text)

    return None


def resolve_time_window(user_message: str) -> Dict[str, Any]:
    """사용자 문장에서 분석 기간을 추정한다."""
    now = datetime.utcnow()
    default_days = 180
    default = {
        "start_date": (now - timedelta(days=default_days)).strftime("%Y-%m-%d"),
        "end_date": now.strftime("%Y-%m-%d"),
        "time_unit": "week",
        "days": default_days,
    }

    if not user_message:
        return default

    text = user_message.lower()
    days: Optional[int] = None

    match = re.search(r"(\d+)\s*(?:일|일간|일동안|days?)", text)
    if match:
        days = max(1, int(match.group(1)))

    if days is None:
        match = re.search(r"(\d+)\s*(?:주|주간|weeks?)", text)
        if match:
            days = int(match.group(1)) * 7

    if days is None:
        match = re.search(r"(\d+)\s*(?:개월|달|months?)", text)
        if match:
            days = int(match.group(1)) * 30

    if days is None:
        match = re.search(r"(\d+)\s*(?:년|years?)", text)
        if match:
            days = int(match.group(1)) * 365

    if days is None:
        condensed = text.replace(" ", "")
        if "분기" in text:
            days = 90
        elif "반년" in text:
            days = 180
        elif "1년" in condensed or "일년" in condensed:
            days = 365
        elif "3년" in condensed:
            days = 365 * 3
        elif "5년" in condensed:
            days = 365 * 5

    if days is None:
        return default

    days = max(7, min(days, 365 * 10))
    start = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    time_unit = "date"
    if days > 120:
        time_unit = "week"
    if days > 365 * 2:
        time_unit = "month"

    return {
        "start_date": start,
        "end_date": now.strftime("%Y-%m-%d"),
        "time_unit": time_unit,
        "days": days,
    }


def get_naver_datalab_trends(
    keywords: List[str],
    start_date: str,
    end_date: str,
    time_unit: str = "date",
) -> Dict[str, Any]:
    """Naver DataLab API로 트렌드 조회 (실패 시 모의 데이터)."""
    logger.info("Naver DataLab 조회: %s (%s~%s)", keywords, start_date, end_date)

    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        payload = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": [
                {"groupName": kw, "keywords": [kw]}
                for kw in keywords[:5]
            ],
            "device": "",
            "gender": "",
            "ages": [],
        }
        try:
            response = requests.post(
                NAVER_DATALAB_URL,
                headers={
                    "X-Naver-Client-Id": NAVER_CLIENT_ID,
                    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            if results:
                normalized: Dict[str, Any] = {
                    "keywords": keywords[:5],
                    "period": {"start": start_date, "end": end_date},
                    "time_unit": time_unit,
                    "results": [],
                    "is_mock": False,
                }
                for entry in results:
                    series = [
                        {"date": item.get("period"), "value": item.get("ratio")}
                        for item in entry.get("data", [])
                        if item.get("ratio") is not None
                    ]
                    normalized["results"].append(
                        {
                            "group": entry.get("title") or entry.get("groupName") or keywords[0],
                            "keywords": entry.get("keywords", []),
                            "series": series,
                        }
                    )
                return normalized
        except requests.RequestException as exc:
            logger.warning("Naver DataLab API 호출 실패: %s", exc)
        except ValueError as exc:
            logger.warning("Naver DataLab 응답 파싱 실패: %s", exc)

    return _generate_mock_naver_trends(keywords, start_date, end_date, time_unit)


def analyze_trend_data(trend_data: Dict[str, Any]) -> Dict[str, Any]:
    """수집한 트렌드 데이터를 분석해 핵심 지표와 인사이트를 생성한다."""
    logger.info("트렌드 데이터 분석 시작")

    keyword = trend_data.get("keyword")
    start_date = trend_data.get("start_date")
    end_date = trend_data.get("end_date")
    time_unit = trend_data.get("time_unit")

    naver_data = trend_data.get("naver") or {}

    naver_series: List[Dict[str, Any]] = []
    if naver_data:
        if "results" in naver_data:
            for entry in naver_data["results"]:
                naver_series.extend(entry.get("series", []))
        elif "data" in naver_data:
            for item in naver_data["data"]:
                naver_series.append({"date": item.get("period"), "value": item.get("ratio")})

    naver_metrics = _compute_series_metrics(naver_series)

    if naver_metrics["has_data"]:
        summary_lines = [
            f"- 검색 지수 {naver_metrics['momentum_label']} 흐름 (최근 변화 {format_percentage(naver_metrics['momentum_pct'])})",
            f"- 첫 시점 대비 변화율 {format_percentage(naver_metrics['growth_pct'])}",
        ]
    else:
        summary_lines = ["- 신뢰할 수 있는 데이터 포인트를 찾지 못했습니다."]

    signal = _infer_signal(naver_metrics)
    insight = _generate_insights_with_llm(
        keyword,
        summary_lines,
        naver_metrics,
        time_unit,
        start_date,
        end_date,
    )
    if not insight:
        insight = _generate_rule_based_insight(keyword, naver_metrics)

    confidence = "높음" if naver_metrics["has_data"] and not naver_data.get("is_mock", True) else (
        "중간" if naver_metrics["has_data"] else "낮음"
    )

    return {
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "time_unit": time_unit,
        "naver": {
            **naver_metrics,
            "time_unit": naver_data.get("time_unit"),
            "is_mock": naver_data.get("is_mock", True),
        },
        "summary": "\n".join(summary_lines),
        "insight": insight,
        "signal": signal,
        "confidence": confidence,
    }


def format_percentage(value: Optional[float]) -> str:
    if isinstance(value, (int, float)):
        return f"{value:+.1f}%"
    return "N/A"


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _clean_keyword(keyword: str) -> Optional[str]:
    if not keyword:
        return None
    cleaned = _normalize_whitespace(keyword)
    cleaned = re.sub(r"(?:트렌드|trend|분석|시장|데이터)$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"^(?:최근|요즘|대한|관련|국내|해외)\s+", "", cleaned).strip(' "\'()[]')
    if len(cleaned) < 2:
        return None
    if cleaned.lower() in STOPWORDS:
        return None
    return cleaned


def _is_meaningful_token(token: str) -> bool:
    stripped = token.strip(' "\'()[]{}.,!?')
    if not stripped:
        return False
    lower = stripped.lower()
    if lower in STOPWORDS:
        return False
    if "트렌드" in lower or "trend" in lower or "분석" in lower:
        return False
    if len(stripped) == 1 and not stripped.isdigit():
        return False
    return True


def _extract_keyword_with_llm(text: str) -> Optional[str]:
    try:
        response = call_llm_with_context(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 마케팅 데이터 분석 보조 도구입니다. "
                        "사용자가 요청한 문장에서 분석할 핵심 키워드 또는 제품명을 한 줄로만 출력하세요. "
                        "불필요한 설명과 따옴표는 제거하세요."
                    ),
                },
                {"role": "user", "content": text},
            ]
        )
        if response.get("success"):
            raw = response.get("reply_text", "").strip()
            if not raw:
                return None
            keyword = raw.splitlines()[0]
            return _clean_keyword(keyword)
    except Exception as exc:
        logger.debug("LLM 키워드 추출 실패: %s", exc)
    return None


def _generate_mock_naver_trends(
    keywords: List[str],
    start_date: str,
    end_date: str,
    time_unit: str,
) -> Dict[str, Any]:
    logger.info("Naver DataLab 모의 데이터 사용: %s", keywords)
    start_dt = _parse_date(start_date) or (datetime.utcnow() - timedelta(days=90))
    end_dt = _parse_date(end_date) or datetime.utcnow()
    if end_dt <= start_dt:
        end_dt = start_dt + timedelta(days=30)

    total_days = max(1, (end_dt - start_dt).days)
    if time_unit == "date":
        steps = max(8, min(20, total_days // 5 or 8))
        step_days = max(1, total_days // max(steps - 1, 1))
    elif time_unit == "week":
        steps = max(8, min(20, total_days // 7 or 8))
        step_days = 7
    else:
        steps = max(6, min(20, total_days // 30 or 6))
        step_days = 30

    results = []
    for idx, keyword in enumerate(keywords[:5]):
        series = []
        baseline = 40 + (hash((keyword, idx)) % 40)
        slope = (hash((keyword, "trend")) % 5) - 2
        for i in range(steps):
            dt = start_dt + timedelta(days=i * step_days)
            if dt > end_dt:
                dt = end_dt
            jitter = (hash((keyword, i)) % 10) - 5
            value = max(5, min(100, baseline + slope * (i - steps // 2) + jitter))
            series.append({"date": dt.strftime("%Y-%m-%d"), "value": value})
        results.append(
            {
                "group": keyword,
                "keywords": [keyword],
                "series": series,
            }
        )

    return {
        "keywords": keywords[:5],
        "period": {"start": start_date, "end": end_date},
        "time_unit": time_unit,
        "results": results,
        "is_mock": True,
    }


def _compute_series_metrics(series: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not series:
        return {
            "has_data": False,
            "data_points": 0,
            "average": None,
            "latest_value": None,
            "latest_date": None,
            "growth_pct": None,
            "momentum_pct": None,
            "momentum_label": "데이터 부족",
            "peak": None,
            "volatility": None,
            "series_tail": [],
            "first_value": None,
        }

    cleaned = []
    for idx, point in enumerate(series):
        value = point.get("value")
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        date_obj = _parse_date(point.get("date"))
        cleaned.append((date_obj or (datetime.min + timedelta(days=idx)), idx, point.get("date"), numeric))

    if not cleaned:
        return {
            "has_data": False,
            "data_points": 0,
            "average": None,
            "latest_value": None,
            "latest_date": None,
            "growth_pct": None,
            "momentum_pct": None,
            "momentum_label": "데이터 부족",
            "peak": None,
            "volatility": None,
            "series_tail": [],
            "first_value": None,
        }

    cleaned.sort(key=lambda item: (item[0], item[1]))
    ordered_dates = [item[2] for item in cleaned]
    values = [item[3] for item in cleaned]

    data_points = len(values)
    average = sum(values) / data_points
    first_value = values[0]
    latest_value = values[-1]
    growth_pct = ((latest_value - first_value) / first_value * 100) if first_value else None

    window = min(3, data_points)
    early_avg = sum(values[:window]) / window if window else None
    recent_avg = sum(values[-window:]) / window if window else None
    momentum_pct = ((recent_avg - early_avg) / early_avg * 100) if early_avg else None
    momentum_label = _momentum_label(momentum_pct)

    peak_index = max(range(data_points), key=lambda i: values[i])
    peak = {"date": ordered_dates[peak_index], "value": values[peak_index]}

    try:
        volatility = statistics.stdev(values) if data_points > 1 else 0.0
    except statistics.StatisticsError:
        volatility = 0.0

    series_tail = [
        {"date": ordered_dates[i], "value": values[i]}
        for i in range(max(0, data_points - 5), data_points)
    ]

    return {
        "has_data": True,
        "data_points": data_points,
        "average": average,
        "latest_value": latest_value,
        "latest_date": ordered_dates[-1],
        "growth_pct": growth_pct,
        "momentum_pct": momentum_pct,
        "momentum_label": momentum_label,
        "peak": peak,
        "volatility": volatility,
        "series_tail": series_tail,
        "first_value": first_value,
    }


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    return None


def _momentum_label(momentum_pct: Optional[float]) -> str:
    if not isinstance(momentum_pct, (int, float)):
        return "데이터 부족"
    if momentum_pct > 5:
        return "상승"
    if momentum_pct < -5:
        return "하락"
    return "보합"


def _infer_signal(metrics: Dict[str, Any]) -> str:
    if not metrics.get("has_data"):
        return "데이터 부족"

    score = 0.0
    weight = 0.0

    growth = metrics.get("growth_pct")
    momentum = metrics.get("momentum_pct")
    latest = metrics.get("latest_value")

    if isinstance(growth, (int, float)):
        score += growth * 0.6
        weight += 0.6
    if isinstance(momentum, (int, float)):
        score += momentum * 0.4
        weight += 0.4
    if isinstance(latest, (int, float)) and latest >= 70:
        score += 5

    if weight == 0:
        return "데이터 부족"

    normalized = score / weight
    if normalized >= 20:
        return "🚀 강한 상승세"
    if normalized >= 8:
        return "↗️ 완만한 상승"
    if normalized <= -20:
        return "📉 강한 하락"
    if normalized <= -8:
        return "↘️ 완만한 하락"
    return "➖ 보합세"


def _generate_insights_with_llm(
    keyword: Optional[str],
    summary_lines: List[str],
    naver_metrics: Dict[str, Any],
    time_unit: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Optional[str]:
    if not keyword:
        return None

    try:
        metrics_brief = {
            "naver": {
                "average": naver_metrics.get("average"),
                "growth_pct": naver_metrics.get("growth_pct"),
                "momentum_pct": naver_metrics.get("momentum_pct"),
                "latest_value": naver_metrics.get("latest_value"),
                "peak": naver_metrics.get("peak"),
            }
        }

        summary_text = "\n".join(summary_lines)

        response = call_llm_with_context(
            [
                {
                    "role": "system",
                    "content": (
                        "당신은 디지털 마케팅 전략가입니다. Naver 검색 지표를 바탕으로 "
                        "핵심 인사이트와 대응 전략을 간결하게 제시하세요."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"키워드: {keyword}\n"
                        f"기간: {start_date} ~ {end_date} (단위: {time_unit})\n"
                        f"요약: {summary_text}\n"
                        f"지표: {json.dumps(metrics_brief, ensure_ascii=False)}\n"
                        "증가/감소 원인과 대응 전략을 bullet 2-3개로 정리해주세요."
                    ),
                },
            ]
        )

        if response.get("success"):
            return response.get("reply_text", "").strip() or None
    except Exception as exc:
        logger.debug("LLM 인사이트 생성 실패: %s", exc)

    return None


def _generate_rule_based_insight(
    keyword: Optional[str],
    naver_metrics: Dict[str, Any],
) -> str:
    if not naver_metrics.get("has_data"):
        return "유의미한 검색 데이터를 찾지 못했습니다. 기간을 넓혀 다시 시도하거나 다른 키워드를 입력해 보세요."

    lines: List[str] = []
    momentum_label = naver_metrics.get("momentum_label")
    momentum_pct = format_percentage(naver_metrics.get("momentum_pct"))
    growth_pct = format_percentage(naver_metrics.get("growth_pct"))

    lines.append(
        f"'{keyword}' 검색 지수는 최근 {momentum_label} 흐름이며 단기 변화율은 {momentum_pct}입니다."
    )
    lines.append(
        f"분석 시작 시점 대비 변화율은 {growth_pct}로 나타났습니다. 검색 피크 시점과 최신 지수를 참고해 콘텐츠 타이밍을 조정하세요."
    )
    lines.append("상승 구간에서는 캠페인을 확대하고, 하락 국면에서는 연관 키워드를 발굴해 관심을 유지하세요.")
    return "\n".join(lines)
