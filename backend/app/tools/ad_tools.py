"""
광고 문구 생성 도구
LLM을 활용한 광고 카피 생성
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def generate_ad_copy_variations(
    product_name: str,
    product_features: List[str],
    tone: str = "friendly",
    num_variations: int = 3
) -> List[str]:
    """
    광고 문구 배리에이션 생성

    Args:
        product_name: 제품명
        product_features: 제품 특징 리스트
        tone: 톤앤매너 (friendly, professional, humorous)
        num_variations: 생성할 배리에이션 개수

    Returns:
        광고 문구 리스트
    """
    logger.info(f"광고 문구 생성: {product_name}")

    # TODO: LLM (OpenAI API) 호출
    # from app.tools.llm import call_llm_with_context
    # prompt = f"다음 제품의 광고 문구를 {num_variations}개 생성하세요..."
    # result = call_llm_with_context([{"role": "user", "content": prompt}])

    # 모의 데이터
    return [
        f"{product_name} - {', '.join(product_features[:2])}의 완벽한 조화!",
        f"지금 바로 경험하세요, {product_name}",
        f"{product_name}와 함께하는 새로운 일상"
    ]


def generate_headline(product_name: str, max_length: int = 30) -> str:
    """
    헤드라인 생성 (짧은 광고 문구)

    Args:
        product_name: 제품명
        max_length: 최대 길이

    Returns:
        헤드라인
    """
    logger.info(f"헤드라인 생성: {product_name}")

    # TODO: LLM 호출 (짧은 임팩트 있는 문구)

    return f"{product_name}, 당신의 선택"


def check_ad_compliance(ad_text: str) -> Dict[str, Any]:
    """
    광고 문구 규제 체크 (금지어 등)

    Args:
        ad_text: 광고 문구

    Returns:
        체크 결과
    """
    logger.info("광고 규제 체크")

    # TODO: 금지어 목록 확인
    # TODO: Naver 광고 API 등으로 검증

    forbidden_words = ["최고", "최저", "1등"]  # 예시
    found_issues = [word for word in forbidden_words if word in ad_text]

    return {
        "is_compliant": len(found_issues) == 0,
        "issues": found_issues,
        "message": "문제 없음" if len(found_issues) == 0 else f"금지어 발견: {found_issues}"
    }
