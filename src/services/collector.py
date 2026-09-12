import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional
import pandas as pd

import email.utils
import urllib.parse
from datetime import datetime

WEEKDAY_KR = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]


def _parse_item_datetime(pub_date_str: str) -> tuple[Optional[datetime], Optional[str], Optional[int], Optional[str]]:
    """발행일 문자열 파싱 (RFC 822 또는 YYYYMMDD 또는 ISO) -> (datetime, date_str, hour, weekday_kr)"""
    if not pub_date_str or not isinstance(pub_date_str, str):
        return None, None, None, None
    s = pub_date_str.strip()
    dt = None
    # 1. RFC 822 뉴스 형식 (e.g. "Thu, 10 Sep 2026 18:20:00 +0900")
    try:
        dt = email.utils.parsedate_to_datetime(s)
    except Exception:
        pass

    # 2. YYYYMMDD 블로그 형식 (e.g. "20260910")
    if dt is None and len(s) == 8 and s.isdigit():
        try:
            dt = datetime.strptime(s, "%Y%m%d")
        except Exception:
            pass

    # 3. pd.to_datetime 일반 형식 시도
    if dt is None:
        try:
            parsed = pd.to_datetime(s)
            if not pd.isna(parsed):
                dt = parsed.to_pydatetime()
        except Exception:
            pass

    if dt is not None:
        try:
            date_str = dt.strftime("%Y-%m-%d")
            hour = dt.hour
            weekday = WEEKDAY_KR[dt.weekday()]
            return dt, date_str, hour, weekday
        except Exception:
            pass

    return None, None, None, None


def _extract_domain_and_depth(url: str) -> tuple[str, str, int]:
    """URL에서 (순수 도메인, TLD, URL 깊이) 추출"""
    if not url or not isinstance(url, str):
        return "", "", 0
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.strip("/")
        depth = len([p for p in path.split("/") if p]) if path else 0
        tld = netloc.split(".")[-1] if "." in netloc else ""
        return netloc, tld, depth
    except Exception:
        return "", "", 0


from src.api.client import NaverApiClient, NaverApiError
from src.api.endpoints import SEARCH_CHANNELS
from src.utils.text_cleaner import clean_html_tags

logger = logging.getLogger(__name__)


class DataCollector:
    """
    다중 키워드 및 8개 채널의 네이버 검색 데이터와 데이터랩 트렌드를 병렬 수집하는 서비스
    """

    def __init__(self, api_client: NaverApiClient):
        self.client = api_client

    def parse_keywords(self, raw_input: str) -> list[str]:
        """쉼표 또는 줄바꿈으로 구분된 키워드 문자열 파싱 (중복 제거 및 공백 트림)"""
        if not raw_input:
            return []
        items = [k.strip() for k in raw_input.replace("\n", ",").split(",") if k.strip()]
        # 순서 유지 중복 제거
        seen = set()
        unique = []
        for item in items:
            if item not in seen:
                seen.add(item)
                unique.append(item)
        return unique

    def _fetch_single_channel(
        self,
        keyword: str,
        channel_key: str,
        display: int = 100,
        sort: str = "sim",
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """단일 키워드와 단일 채널에 대한 검색 실행 및 결과 정규화 (Rate limit 방어 재시도 포함)"""
        import time

        last_error = None
        for attempt in range(max_retries):
            try:
                res = self.client.search(
                    channel=channel_key,
                    query=keyword,
                    display=display,
                    start=1,
                    sort=sort,
                )
                items = res.get("items", [])
                total = res.get("total", 0)

                records = []
                for it in items:
                    title = clean_html_tags(it.get("title", ""))
                    description = clean_html_tags(
                        it.get("description", "")
                        or it.get("snippet", "")
                        or it.get("bloggername", "")
                        or it.get("cafename", "")
                    )
                    link = it.get("link", "")
                    pub_date = (
                        it.get("pubDate", "")
                        or it.get("postdate", "")
                        or it.get("thumbnail", "")
                    )

                    originallink = it.get("originallink", "")
                    effective_url = originallink if (channel_key == "news" and originallink) else link
                    domain, tld, depth = _extract_domain_and_depth(effective_url)
                    dt_obj, date_str, hour, weekday = _parse_item_datetime(pub_date)

                    title_len = len(title)
                    desc_len = len(description)
                    title_words = len(title.split())
                    desc_words = len(description.split())
                    kw_in_title = keyword.lower() in title.lower()

                    extra_info = {
                        "domain": domain,
                        "tld": tld,
                        "url_depth": depth,
                        "pub_date_str": date_str,
                        "pub_hour": hour,
                        "pub_weekday": weekday,
                        "title_len": title_len,
                        "desc_len": desc_len,
                        "total_len": title_len + desc_len,
                        "title_words": title_words,
                        "desc_words": desc_words,
                        "keyword_in_title": kw_in_title,
                    }

                    if channel_key == "image":
                        thumb = it.get("thumbnail", "")
                        extra_info["thumbnail"] = thumb
                        extra_info["sizeheight"] = it.get("sizeheight", "")
                        extra_info["sizewidth"] = it.get("sizewidth", "")
                        extra_info["has_thumbnail"] = bool(thumb)
                    elif channel_key == "local":
                        extra_info["address"] = clean_html_tags(it.get("address", ""))
                        extra_info["roadAddress"] = clean_html_tags(it.get("roadAddress", ""))
                        extra_info["category"] = it.get("category", "")
                        extra_info["has_thumbnail"] = False
                    elif channel_key == "blog":
                        extra_info["bloggername"] = it.get("bloggername", "")
                        extra_info["bloggerlink"] = it.get("bloggerlink", "")
                        extra_info["has_thumbnail"] = False
                    elif channel_key == "cafearticle":
                        extra_info["cafename"] = it.get("cafename", "")
                        extra_info["cafeurl"] = it.get("cafeurl", "")
                        extra_info["has_thumbnail"] = False
                    elif channel_key == "news":
                        extra_info["originallink"] = originallink
                        extra_info["has_thumbnail"] = False
                    elif channel_key == "encyc":
                        thumb = it.get("thumbnail", "")
                        extra_info["thumbnail"] = thumb
                        extra_info["has_thumbnail"] = bool(thumb)
                    else:
                        extra_info["has_thumbnail"] = bool(it.get("thumbnail", ""))

                    records.append({
                        "keyword": keyword,
                        "channel_key": channel_key,
                        "channel_name": SEARCH_CHANNELS[channel_key]["name"],
                        "title": title,
                        "description": description,
                        "link": link,
                        "pub_date": pub_date,
                        "raw_data": it,
                        **extra_info,
                    })

                return {
                    "keyword": keyword,
                    "channel_key": channel_key,
                    "channel_name": SEARCH_CHANNELS[channel_key]["name"],
                    "total_count": total,
                    "items_count": len(records),
                    "records": records,
                    "error": None,
                }
            except Exception as e:
                last_error = e
                # 속도 제한(Rate limit) 발생 시 잠시 대기 후 재시도
                if "429" in str(e) or "Rate limit" in str(e):
                    time.sleep(0.3 * (attempt + 1))
                    continue
                break

        logger.warning(f"Error fetching {keyword} - {channel_key}: {last_error}")
        return {
            "keyword": keyword,
            "channel_key": channel_key,
            "channel_name": SEARCH_CHANNELS.get(channel_key, {}).get("name", channel_key),
            "total_count": 0,
            "items_count": 0,
            "records": [],
            "error": str(last_error),
        }

    def collect_search_data(
        self,
        keywords: list[str],
        channels: Optional[list[str]] = None,
        display: int = 100,
        sort: str = "sim",
        max_workers: int = 4,
    ) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
        """
        다중 키워드 x 선택된 채널 일괄 병렬 수집
        :return: (상세 아이템 DataFrame, 채널별 총계 요약 DataFrame, 에러 목록)
        """
        if channels is None:
            channels = list(SEARCH_CHANNELS.keys())

        all_records = []
        summary_rows = []
        errors = []

        tasks = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for kw in keywords:
                for ch in channels:
                    tasks.append(
                        executor.submit(
                            self._fetch_single_channel,
                            keyword=kw,
                            channel_key=ch,
                            display=display,
                            sort=sort,
                        )
                    )

            for future in as_completed(tasks):
                res = future.result()
                if res["error"]:
                    errors.append(f"[{res['keyword']} - {res['channel_name']}] {res['error']}")
                summary_rows.append({
                    "keyword": res["keyword"],
                    "channel_key": res["channel_key"],
                    "channel_name": res["channel_name"],
                    "total_count": res["total_count"],
                    "fetched_count": res["items_count"],
                })
                all_records.extend(res["records"])

        df_items = pd.DataFrame(all_records)
        df_summary = pd.DataFrame(summary_rows)

        if not df_summary.empty:
            df_summary = df_summary.sort_values(by=["keyword", "channel_name"])

        return df_items, df_summary, errors

    def collect_datalab_trend(
        self,
        keywords: list[str],
        start_date: str,
        end_date: str,
        time_unit: str = "date",
    ) -> tuple[pd.DataFrame, Optional[str]]:
        """
        네이버 데이터랩 트렌드 API 호출 및 시계열 DataFrame 변환
        :return: (트렌드 DataFrame [period, keyword, ratio], 에러 메시지)
        """
        # 최대 5개 키워드 그룹 제한 (네이버 데이터랩 사양)
        target_kws = keywords[:5]
        keyword_groups = [{"groupName": kw, "keywords": [kw]} for kw in target_kws]

        try:
            raw_res = self.client.get_datalab_trend(
                keyword_groups=keyword_groups,
                start_date=start_date,
                end_date=end_date,
                time_unit=time_unit,
            )

            results = raw_res.get("results", [])
            trend_records = []
            for group in results:
                title = group.get("title", "")
                data_list = group.get("data", [])
                for d in data_list:
                    trend_records.append({
                        "period": pd.to_datetime(d.get("period")),
                        "keyword": title,
                        "ratio": float(d.get("ratio", 0.0)),
                    })

            df_trend = pd.DataFrame(trend_records)
            if not df_trend.empty:
                df_trend = df_trend.sort_values(by=["period", "keyword"])

            return df_trend, None
        except Exception as e:
            return pd.DataFrame(), str(e)
