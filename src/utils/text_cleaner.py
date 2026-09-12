import html
import re


def clean_html_tags(text: str) -> str:
    """
    네이버 검색 API 결과 텍스트에서 <b> 태그 및 HTML 엔티티를 제거하고 정제합니다.
    """
    if not text or not isinstance(text, str):
        return ""
    # HTML 엔티티 디코딩 (&quot;, &amp; 등)
    unescaped = html.unescape(text)
    # 태그 (<...>) 제거
    clean = re.sub(r"<[^>]+>", "", unescaped)
    # 중복 공백 제거
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def extract_keywords_simple(text: str, min_len: int = 2) -> list[str]:
    """
    기본 한글/영문 단어 추출 (정규식 기반 fallback 용도)
    """
    cleaned = clean_html_tags(text)
    # 한글, 영문, 숫자 단어 추출
    tokens = re.findall(r"[가-힣a-zA-Z0-9]+", cleaned)
    return [t for t in tokens if len(t) >= min_len]
