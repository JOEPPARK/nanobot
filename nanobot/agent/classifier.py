"""Message complexity classifier for smart model routing.

Classifies incoming messages into three tiers:
- haiku: simple queries, greetings, general search, translations
- sonnet: complex coding, stock/financial analysis, legal questions
- opus: large-scale data analysis, critical decisions, multi-domain tasks
"""

from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    pass


class ComplexityTier(str, Enum):
    """Message complexity tiers mapped to model capability levels."""

    HAIKU = "haiku"
    SONNET = "sonnet"
    OPUS = "opus"


# ---------------------------------------------------------------------------
# Keyword / pattern rules
# ---------------------------------------------------------------------------

# OPUS: large data, critical importance, multi-step complex tasks
_OPUS_KEYWORDS: list[str] = [
    # Korean
    "대규모", "대량", "빅데이터", "전체 분석", "종합 분석", "심층 분석",
    "전략 수립", "의사결정", "중요한 결정", "핵심 전략",
    "아키텍처 설계", "시스템 설계", "전체 리팩토링",
    "보안 감사", "취약점 분석", "침투 테스트",
    "논문 분석", "연구 분석", "학술",
    "멀티스텝", "복합적",
    "코드베이스",
    # English
    "large-scale", "big data", "comprehensive analysis", "deep analysis",
    "strategic planning", "critical decision", "architecture design",
    "system design", "full refactor", "security audit",
    "vulnerability analysis", "penetration test",
    "research paper", "academic", "multi-step", "multi-domain",
]

_OPUS_PATTERNS: list[re.Pattern] = [
    re.compile(r"전체.*분석", re.IGNORECASE),
    re.compile(r"모든.*데이터", re.IGNORECASE),
    re.compile(r"대규모.*처리", re.IGNORECASE),
    re.compile(r"시스템.*전체.*설계", re.IGNORECASE),
    re.compile(r"(100|천|만)\s*(개|건|줄|라인)", re.IGNORECASE),
    re.compile(r"comprehensive.*review", re.IGNORECASE),
    re.compile(r"full.*system", re.IGNORECASE),
    re.compile(r"entire.*codebase", re.IGNORECASE),
]

# SONNET: coding, financial analysis, legal, technical tasks
_SONNET_KEYWORDS: list[str] = [
    # Coding (Korean)
    "코드", "코딩", "프로그래밍", "구현", "개발",
    "함수", "클래스", "알고리즘", "디버그", "디버깅",
    "리팩토링", "API", "데이터베이스", "쿼리", "SQL",
    "버그", "에러", "오류 수정", "테스트 코드",
    "파이썬", "자바스크립트", "타입스크립트", "자바", "러스트",
    "도커", "쿠버네티스", "CI/CD", "배포",
    # Coding (English)
    "code", "coding", "programming", "implement", "develop",
    "function", "class", "algorithm", "debug", "debugging",
    "refactor", "database", "query", "bug", "error fix",
    "python", "javascript", "typescript", "java", "rust",
    "docker", "kubernetes", "deploy", "git",
    # Stock/Finance (Korean)
    "주식", "주가", "종목", "매수", "매도", "투자",
    "차트 분석", "기술적 분석", "펀더멘탈", "재무제표",
    "수익률", "포트폴리오", "배당", "PER", "PBR", "ROE",
    "코스피", "코스닥", "나스닥", "S&P",
    "환율", "금리", "채권", "선물", "옵션",
    "가상화폐", "비트코인", "이더리움", "암호화폐",
    # Stock/Finance (English)
    "stock", "equity", "trading", "investment", "portfolio",
    "financial analysis", "technical analysis", "fundamental",
    "earnings", "dividend", "market cap", "valuation",
    "cryptocurrency", "bitcoin", "forex",
    # Legal (Korean)
    "법률", "법적", "계약서", "소송", "판례",
    "특허", "저작권", "상표", "지적재산",
    "약관", "규정", "법규", "조항", "면책",
    "노동법", "세법", "형법", "민법", "상법",
    "근로기준법", "공정거래법", "개인정보보호법", "산업안전보건법",
    "변호사", "법무", "고소", "고발",
    # Legal (English)
    "legal", "law", "contract", "lawsuit", "patent",
    "copyright", "trademark", "intellectual property",
    "regulation", "compliance", "liability", "litigation",
    "terms of service", "privacy policy",
    # Technical/analytical
    "분석해", "분석해줘", "분석하", "비교 분석",
    "데이터 분석", "통계", "회귀분석", "머신러닝",
    "analyze", "analysis", "statistical", "machine learning",
    "data science", "regression",
]

_SONNET_PATTERNS: list[re.Pattern] = [
    re.compile(r"코드.*작성", re.IGNORECASE),
    re.compile(r"코드.*수정", re.IGNORECASE),
    re.compile(r"구현.*해\s*(줘|주세요|주실|달라)", re.IGNORECASE),
    re.compile(r"개발.*해\s*(줘|주세요|주실|달라)", re.IGNORECASE),
    re.compile(r"주[가식].*분석", re.IGNORECASE),
    re.compile(r"종목.*추천", re.IGNORECASE),
    re.compile(r"투자.*전략", re.IGNORECASE),
    re.compile(r"법[률적].*검토", re.IGNORECASE),
    re.compile(r"계약서.*검토", re.IGNORECASE),
    re.compile(r"(write|create|build|fix).*code", re.IGNORECASE),
    re.compile(r"(stock|market).*analy", re.IGNORECASE),
    re.compile(r"legal.*review", re.IGNORECASE),
    re.compile(r"```", re.IGNORECASE),  # Code blocks indicate coding context
]


def classify_message(content: str) -> ComplexityTier:
    """Classify a message's complexity tier based on content analysis.

    Args:
        content: The user's message text.

    Returns:
        ComplexityTier indicating which model tier to use.
    """
    if not content or not content.strip():
        return ComplexityTier.HAIKU

    text = content.strip().lower()

    # Check OPUS first (highest priority)
    for kw in _OPUS_KEYWORDS:
        if kw.lower() in text:
            logger.debug("Classified as OPUS (keyword: {})", kw)
            return ComplexityTier.OPUS

    for pattern in _OPUS_PATTERNS:
        if pattern.search(content):
            logger.debug("Classified as OPUS (pattern: {})", pattern.pattern)
            return ComplexityTier.OPUS

    # Check SONNET
    sonnet_hits = 0
    for kw in _SONNET_KEYWORDS:
        if kw.lower() in text:
            sonnet_hits += 1
            if sonnet_hits >= 1:
                logger.debug("Classified as SONNET (keyword: {})", kw)
                return ComplexityTier.SONNET

    for pattern in _SONNET_PATTERNS:
        if pattern.search(content):
            logger.debug("Classified as SONNET (pattern: {})", pattern.pattern)
            return ComplexityTier.SONNET

    # Length heuristic: very long messages likely need more capable models
    if len(content) > 2000:
        logger.debug("Classified as SONNET (long message: {} chars)", len(content))
        return ComplexityTier.SONNET

    # Default: HAIKU for simple queries
    logger.debug("Classified as HAIKU (default)")
    return ComplexityTier.HAIKU


# Model indicator suffixes
MODEL_INDICATORS: dict[ComplexityTier, str] = {
    ComplexityTier.HAIKU: "(h)",
    ComplexityTier.SONNET: "(s)",
    ComplexityTier.OPUS: "(o)",
}

# Fallback order: opus -> sonnet -> haiku
FALLBACK_ORDER: dict[ComplexityTier, ComplexityTier | None] = {
    ComplexityTier.OPUS: ComplexityTier.SONNET,
    ComplexityTier.SONNET: ComplexityTier.HAIKU,
    ComplexityTier.HAIKU: None,  # No fallback from haiku
}
