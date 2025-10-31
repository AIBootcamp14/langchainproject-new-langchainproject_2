"""
광고 문구 생성 도구
LLM을 활용한 광고 카피 생성 파이프라인
"""
import json
import logging
import textwrap
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.tools.llm import call_llm_with_context

logger = logging.getLogger(__name__)

# 기본 설정 상수
DEFAULT_TONES = ["friendly", "formal", "humor"]
DEFAULT_LENGTHS = ["short", "medium", "long"]

# 금지어 리스트 (확장 가능)
FORBIDDEN_WORDS = [
    "최고",
    "최저",
    "국내 1위",
    "보장",
    "완벽",
    "100%",
    "무조건",
    "전액"
]

# LLM 프롬프트 템플릿
SYSTEM_PROMPT = textwrap.dedent(
    """
    당신은 한국어 마케팅 카피라이터입니다. 사용자가 제공하는 제품 정보를 바탕으로
    광고 문구를 작성합니다. 한국 광고 규제를 고려하여 과장된 표현은 피하고,
    사용자 요청에 맞춰 톤과 길이를 조절하세요.
    """
).strip()

REQUEST_PARSER_PROMPT = textwrap.dedent(
    """
    아래 사용자의 요구사항에서 제품/서비스 광고를 작성하는 데 필요한 정보를 JSON으로 정리하세요.
    필드:
    - product_name: 제품명 또는 서비스명 (문자열)
    - product_description: 제품 특징이나 장점 (문자열)
    - key_features: 핵심 특징 목록 (문자열 배열)
    - target_audience: 주 타겟 고객 (문자열, 없으면 빈 문자열)
    - campaign_goal: 캠페인 목표 (문자열, 없으면 빈 문자열)
    - tone_preferences: 원하는 톤 목록 (문자열 배열, 예: ["friendly", "formal", "humor"])
    - length_preferences: 원하는 길이 목록 (문자열 배열, 예: ["short", "medium", "long"])
    가능한 경우 영어보다 한국어를 사용하세요.

    사용자 입력:
    {user_input}
    """
).strip()

COPY_PROMPT_TEMPLATE = textwrap.dedent(
    """
    제품 정보:
    {product_brief}

    과거 레퍼런스:
    {rag_context}

    요구사항:
    - 톤: {tone_label}
    - 길이: {length_label}
    - 제안 개수: {suggestions}

    조건:
    - 한국어로 작성
    - 과장 표현, 법적 문제가 될 수 있는 표현 피하기
    - 마지막에 해시태그 금지
    - 각 문구는 한 문장으로 작성
    - 친근한 말투를 원하면 "친근한" 느낌을 주되 존칭 사용

    출력 형식:
    JSON 배열. 각 요소는 {"copy": "<문구>"} 형태여야 합니다.
    """
).strip()


def parse_ad_request(user_message: str) -> Dict[str, Any]:
    """
    사용자 메시지에서 제품 정보를 추출

    Args:
        user_message: 사용자 입력 텍스트

    Returns:
        제품 정보 딕셔너리
    """
    logger.info("광고 요청 파싱 시작")

    prompt = REQUEST_PARSER_PROMPT.format(user_input=user_message)
    response = call_llm_with_context(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    if not response.get("success"):
        logger.error(f"LLM 파싱 실패: {response.get('error')}")
        return {}

    raw_text = response.get("reply_text", "").strip()
    try:
        parsed = json.loads(raw_text)
        product_name = parsed.get("product_name", "").strip()
        if not product_name:
            logger.warning("제품명을 찾지 못했습니다.")
            return {}

        parsed.setdefault("key_features", [])
        parsed.setdefault("tone_preferences", DEFAULT_TONES)
        parsed.setdefault("length_preferences", DEFAULT_LENGTHS)
        parsed.setdefault("product_description", "")
        parsed.setdefault("target_audience", "")
        parsed.setdefault("campaign_goal", "")
        return parsed
    except json.JSONDecodeError as json_error:
        logger.error(f"JSON 파싱 실패: {json_error}; 원본 텍스트: {raw_text[:200]}")
        return {}


def generate_ad_copy_matrix(
    product_brief: Dict[str, Any],
    rag_context: Optional[str],
    tone_options: List[str],
    length_options: List[str],
    suggestions_per_slot: int = 2
) -> Dict[str, Dict[str, List[str]]]:
    """
    길이×톤 조합으로 광고 문구 생성

    Args:
        product_brief: 제품 정보
        rag_context: RAG에서 가져온 과거 문구
        tone_options: 사용할 톤 목록
        length_options: 사용할 길이 목록
        suggestions_per_slot: 각 조합당 생성할 문구 수

    Returns:
        {tone: {length: [문구들]}} 구조
    """
    product_summary = _summarize_product_brief(product_brief)
    rag_block = rag_context or "관련된 과거 데이터가 없습니다."

    result: Dict[str, Dict[str, List[str]]] = {tone: {} for tone in tone_options}

    for tone in tone_options:
        for length in length_options:
            prompt = COPY_PROMPT_TEMPLATE.format(
                product_brief=product_summary,
                rag_context=rag_block,
                tone_label=tone,
                length_label=length,
                suggestions=suggestions_per_slot
            )
            response = call_llm_with_context(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            if not response.get("success"):
                logger.error(
                    "카피 생성 실패: tone=%s, length=%s, error=%s",
                    tone,
                    length,
                    response.get("error")
                )
                result.setdefault(tone, {})[length] = []
                continue

            raw_text = response.get("reply_text", "").strip()
            copies = _extract_copies(raw_text)
            result.setdefault(tone, {})[length] = copies

    return result


def batch_check_ad_compliance(variations: Dict[str, Dict[str, List[str]]]) -> Dict[str, Any]:
    """
    광고 문구 컴플라이언스 검사 (금지어 체크)

    Args:
        variations: 톤/길이별 생성 문구

    Returns:
        검사 결과 요약
    """
    details: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for tone, length_map in variations.items():
        for length, copies in length_map.items():
            for copy_text in copies:
                issues = [
                    forbidden for forbidden in FORBIDDEN_WORDS if forbidden in copy_text
                ]
                is_compliant = len(issues) == 0
                if is_compliant:
                    passed += 1
                else:
                    failed += 1
                details.append({
                    "tone": tone,
                    "length": length,
                    "copy": copy_text,
                    "is_compliant": is_compliant,
                    "issues": issues
                })

    summary = {
        "passed": passed,
        "failed": failed,
        "checked": passed + failed
    }

    return {
        "summary": summary,
        "details": details,
        "note": "네이버 광고 API 연동 시 추가 검증 필요"
    }


def prepare_rag_documents(
    product_brief: Dict[str, Any],
    variations: Dict[str, Dict[str, List[str]]]
) -> List[Dict[str, Any]]:
    """
    RAG 저장용 문서 리스트 생성

    Args:
        product_brief: 제품 정보
        variations: 광고 문구 배리에이션

    Returns:
        RAG 문서 리스트
    """
    product_name = product_brief.get("product_name", "제품")
    timestamp = datetime.utcnow().isoformat()
    documents: List[Dict[str, Any]] = []

    for tone, length_map in variations.items():
        for length, copies in length_map.items():
            if not copies:
                continue

            content_lines = [f"[{product_name}] 톤={tone}, 길이={length}"]
            content_lines.extend(f"- {copy_text}" for copy_text in copies)

            metadata = {
                "product_name": product_name,
                "tone": tone,
                "length": length,
                "generated_at": timestamp,
                "key_features": product_brief.get("key_features", []),
                "campaign_goal": product_brief.get("campaign_goal", "")
            }

            documents.append({
                "content": "\n".join(content_lines),
                "metadata": metadata
            })

    return documents


def _extract_copies(raw_text: str) -> List[str]:
    """LLM 응답에서 광고 문구만 추출"""
    try:
        data = json.loads(raw_text)
        if isinstance(data, list):
            return [
                entry.get("copy", "").strip()
                for entry in data
                if isinstance(entry, dict) and entry.get("copy")
            ]
    except json.JSONDecodeError:
        logger.warning("광고 문구 JSON 파싱 실패, 텍스트 기반 추출 시도")

    # JSON 파싱 실패 시 줄 단위 추출 (임시)
    copies = []
    for line in raw_text.splitlines():
        line = line.strip("-• ").strip()
        if line:
            copies.append(line)
    return copies


def _summarize_product_brief(product_brief: Dict[str, Any]) -> str:
    """LLM에 전달할 제품 정보 요약"""
    name = product_brief.get("product_name", "제품명 미상")
    description = product_brief.get("product_description", "")
    features = product_brief.get("key_features", [])
    target = product_brief.get("target_audience", "")
    goal = product_brief.get("campaign_goal", "")

    lines = [
        f"제품명: {name}",
        f"설명: {description or '세부 설명 없음'}",
    ]
    if features:
        lines.append("핵심 특징:")
        for feature in features:
            lines.append(f"- {feature}")
    if target:
        lines.append(f"타겟 고객: {target}")
    if goal:
        lines.append(f"캠페인 목표: {goal}")

    return "\n".join(lines)
