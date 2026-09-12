"""네이버 API (NAVER API HUB 및 네이버 개발자센터) 엔드포인트 및 메타데이터 정의"""

# 1. NAVER API HUB (네이버 클라우드 플랫폼 ncloud.com)
NCP_APIHUB_BASE = "https://naverapihub.apigw.ntruss.com"
NCP_SEARCH_BASE = f"{NCP_APIHUB_BASE}/search/v1"
NCP_TREND_URL = f"{NCP_APIHUB_BASE}/search-trend/v1/search"

# 2. 네이버 개발자센터 (developers.naver.com) 오픈API
DEV_OPENAPI_BASE = "https://openapi.naver.com/v1"

SEARCH_CHANNELS = {
    "news": {
        "name": "뉴스",
        "ncp_url": f"{NCP_SEARCH_BASE}/news",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/news.json",
        "description": "네이버 뉴스 검색 결과",
        "icon": "📰",
    },
    "blog": {
        "name": "블로그",
        "ncp_url": f"{NCP_SEARCH_BASE}/blog",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/blog.json",
        "description": "네이버 블로그 포스트 검색 결과",
        "icon": "📝",
    },
    "cafearticle": {
        "name": "카페글",
        "ncp_url": f"{NCP_SEARCH_BASE}/cafearticle",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/cafearticle.json",
        "description": "네이버 카페 게시글 검색 결과",
        "icon": "☕",
    },
    "kin": {
        "name": "지식iN",
        "ncp_url": f"{NCP_SEARCH_BASE}/kin",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/kin.json",
        "description": "네이버 지식iN 질문/답변 검색 결과",
        "icon": "💡",
    },
    "webkr": {
        "name": "웹문서",
        "ncp_url": f"{NCP_SEARCH_BASE}/webkr",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/webkr.json",
        "description": "국내 웹문서 검색 결과",
        "icon": "🌐",
    },
    "image": {
        "name": "이미지",
        "ncp_url": f"{NCP_SEARCH_BASE}/image",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/image",
        "description": "네이버 이미지 검색 결과",
        "icon": "🖼️",
    },
    "local": {
        "name": "지역(플레이스)",
        "ncp_url": f"{NCP_SEARCH_BASE}/local",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/local.json",
        "description": "지역 업체 및 장소 검색 결과",
        "icon": "📍",
    },
    "encyc": {
        "name": "백과사전",
        "ncp_url": f"{NCP_SEARCH_BASE}/encyc",
        "dev_url": f"{DEV_OPENAPI_BASE}/search/encyc.json",
        "description": "네이버 백과사전 표제어 검색 결과",
        "icon": "📚",
    },
}
