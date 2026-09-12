from datetime import date, timedelta
from typing import Any
import streamlit as st

from src.api.endpoints import SEARCH_CHANNELS
from src.utils.config import get_naver_credentials, is_valid_credentials


def render_sidebar() -> dict[str, Any]:
    """
    사이드바 UI 렌더링 (헤더 및 API 연동 배너 삭제, 순수 입력 컨트롤부터 시작)
    """
    client_id, client_secret = get_naver_credentials()

    st.sidebar.markdown(
        """
        <div style="padding: 4px 0 14px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 18px;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.2rem;">⚙️</span>
                <span style="font-size: 1.02rem; font-weight: 800; color: #0F172A; letter-spacing: -0.02em;">분석 조건 설정</span>
            </div>
            <div style="font-size: 0.8rem; color: #64748B; margin-top: 4px;">다중 검색어 및 수집 채널 지정</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. 검색어 입력
    raw_keywords = st.sidebar.text_area(
        "🔎 검색어 입력 (쉼표 , 구분)",
        value="생성형AI, 챗GPT, 딥시크",
        help="쉼표(,)로 구분하여 여러 검색어의 시장 반응과 트렌드를 비교 분석할 수 있습니다.",
        height=80,
    )

    # 3. 기간 설정
    st.sidebar.markdown("##### 📅 분석 기간 설정")
    today = date.today()
    default_start = today - timedelta(days=90)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_date = st.date_input(
            "시작일",
            value=default_start,
            max_value=today - timedelta(days=1),
            help="데이터랩 트렌드 분석 시작 날짜",
        )
    with col2:
        end_date = st.date_input(
            "종료일",
            value=today,
            max_value=today,
            help="데이터랩 트렌드 분석 종료 날짜",
        )

    time_unit = st.sidebar.selectbox(
        "트렌드 시간 단위",
        options=["date", "week", "month"],
        index=0,
        format_func=lambda x: {"date": "일간 (date)", "week": "주간 (week)", "month": "월간 (month)"}[x],
        help="트렌드 시계열 집계 단위",
    )

    # 4. 수집 옵션 상세 설정
    with st.sidebar.expander("🛠️ 수집 옵션 상세 설정", expanded=False):
        all_channel_keys = list(SEARCH_CHANNELS.keys())
        selected_channels = st.multiselect(
            "수집 대상 채널",
            options=all_channel_keys,
            default=all_channel_keys,
            format_func=lambda k: f"{SEARCH_CHANNELS[k]['icon']} {SEARCH_CHANNELS[k]['name']}",
        )

        display_count = st.slider(
            "채널별 수집 건수 (display)",
            min_value=10,
            max_value=100,
            value=100,
            step=10,
            help="네이버 검색 API 1회 호출당 최대 100건",
        )

        sort_option = st.selectbox(
            "검색 정렬 방식",
            options=["sim", "date"],
            index=0,
            format_func=lambda x: "정확도순 (sim)" if x == "sim" else "최신순 (date)",
        )

    st.sidebar.markdown("---")

    # 5. 실행 버튼
    run_btn = st.sidebar.button(
        "🚀 마켓 인사이트 분석 시작",
        type="primary",
        use_container_width=True,
    )

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "raw_keywords": raw_keywords,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "time_unit": time_unit,
        "selected_channels": selected_channels,
        "display_count": display_count,
        "sort_option": sort_option,
        "run_btn": run_btn,
    }
