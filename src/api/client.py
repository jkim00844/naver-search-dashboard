import json
import logging
from typing import Any, Optional
import requests

from src.api.endpoints import SEARCH_CHANNELS, NCP_TREND_URL

logger = logging.getLogger(__name__)


class NaverApiError(Exception):
    """네이버 API 호출 에러 커스텀 예외"""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class NaverApiClient:
    """
    네이버 API 클라이언트 (NAVER API HUB 및 네이버 개발자센터 자동 호환 지원)
    """

    def __init__(self, client_id: str, client_secret: str, timeout: int = 10):
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self.timeout = timeout
        self.session = requests.Session()

        # NCP API Hub 키 (예: 10자리 영소문자+숫자: 'bj18iuzn6c') 판단
        self.is_ncp = len(self.client_id) <= 12 and not self.client_id.isupper()

    def _get_headers(self, is_json: bool = False) -> dict[str, str]:
        if not self.client_id or not self.client_secret:
            raise NaverApiError(
                "네이버 API Client ID 또는 Client Secret이 설정되지 않았습니다. .env 또는 사이드바에서 입력해 주세요.",
                status_code=401,
            )

        if self.is_ncp:
            headers = {
                "X-NCP-APIGW-API-KEY-ID": self.client_id,
                "X-NCP-APIGW-API-KEY": self.client_secret,
                "User-Agent": "NaverMarketInsightDashboard/1.0",
            }
        else:
            headers = {
                "X-Naver-Client-Id": self.client_id,
                "X-Naver-Client-Secret": self.client_secret,
                "User-Agent": "NaverMarketInsightDashboard/1.0",
            }

        if is_json:
            headers["Content-Type"] = "application/json"

        return headers

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """응답 상태 코드 검증 및 에러 메시지 처리"""
        if response.status_code == 200:
            try:
                return response.json()
            except Exception as e:
                raise NaverApiError(f"응답 JSON 파싱 실패: {e}", status_code=200)

        # 오류 응답 처리
        error_msg = f"HTTP {response.status_code}"
        error_code = ""
        try:
            err_json = response.json()
            if "error" in err_json and isinstance(err_json["error"], dict):
                error_code = err_json["error"].get("errorCode", "")
                error_msg = err_json["error"].get("message", error_msg)
            else:
                error_code = err_json.get("errorCode", "")
                error_msg = err_json.get("errorMessage", error_msg)
        except Exception:
            error_msg = response.text or error_msg

        if response.status_code == 401:
            friendly = f"인증 실패(401): Client ID 또는 Secret을 다시 확인하세요. ({error_msg})"
        elif response.status_code == 403:
            friendly = f"접근 거부(403): 네이버 콘솔(NAVER API HUB 또는 개발자센터)에서 해당 API 권한이 활성화되어 있는지 확인하세요. ({error_msg})"
        elif response.status_code == 429:
            friendly = f"호출 한도 초과(429): 일일 검색 쿼터를 초과했습니다. ({error_msg})"
        elif response.status_code == 400:
            friendly = f"잘못된 요청(400): 파라미터 규격을 확인하세요. ({error_msg})"
        else:
            friendly = f"네이버 API 호출 실패 [{response.status_code}]: {error_msg}"

        logger.error(friendly)
        raise NaverApiError(friendly, status_code=response.status_code, error_code=error_code)

    def search(
        self,
        channel: str,
        query: str,
        display: int = 100,
        start: int = 1,
        sort: str = "sim",
    ) -> dict[str, Any]:
        """
        특정 검색 채널(news, blog, cafearticle, kin, webkr, image, local, encyc)에서 검색 실행
        """
        if channel not in SEARCH_CHANNELS:
            raise ValueError(f"지원하지 않는 채널입니다: {channel}. 사용 가능: {list(SEARCH_CHANNELS.keys())}")

        endpoint_info = SEARCH_CHANNELS[channel]
        url = endpoint_info["ncp_url"] if self.is_ncp else endpoint_info["dev_url"]

        display = max(1, min(display, 100))
        start = max(1, min(start, 1000))

        params = {
            "query": query,
            "display": display,
            "start": start,
            "sort": sort,
        }

        # webkr, encyc 채널은 sort 미지원
        if channel in ["webkr", "encyc"]:
            params.pop("sort", None)

        headers = self._get_headers(is_json=False)
        response = self.session.get(url, headers=headers, params=params, timeout=self.timeout)
        return self._handle_response(response)

    def get_datalab_trend(
        self,
        keyword_groups: list[dict[str, Any]],
        start_date: str,
        end_date: str,
        time_unit: str = "date",
        device: str = "",
        gender: str = "",
        ages: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        네이버 데이터랩 통합검색어 트렌드 조회
        """
        payload: dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
        }
        if device:
            payload["device"] = device
        if gender:
            payload["gender"] = gender
        if ages:
            payload["ages"] = ages

        url = NCP_TREND_URL if self.is_ncp else "https://openapi.naver.com/v1/datalab/search"
        headers = self._get_headers(is_json=True)
        response = self.session.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=self.timeout,
        )
        return self._handle_response(response)
