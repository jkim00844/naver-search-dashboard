import pandas as pd
import streamlit as st
from src.api.endpoints import SEARCH_CHANNELS


def render_data_viewer(df_items: pd.DataFrame):
    """
    수집된 상세 검색 결과 다차원 탐색, 조합 정렬(최근업로드/인기도/텍스트분량),
    결과 내 실시간 텍스트 재검색 및 CSV 다운로드 뷰어
    """
    if df_items.empty:
        st.info("조회된 검색 결과가 없습니다.")
        return

    st.markdown("### 🗂️ 채널별 원문 탐색기 (다차원 정렬 & 조합 검색)")

    # 네이버 정렬 알고리즘 및 조합 검색 안내 배너
    st.info(
        "💡 **조합 검색 가이드**: 네이버 검색 API는 개별 문서의 단순 조회수 수치 대신, "
        "사용자 클릭·조회·관심도 가중치가 종합 반영된 **'포털 추천/인기도순(sim)'**을 제공합니다. "
        "아래 정렬 및 필터를 조합하여 **'최근 업로드순(최신 발행일)'**, **'포털 인기도순(랭킹)'**, "
        "**'제목 키워드 일치순'** 및 **'결과 내 본문 검색'**으로 원하는 결과를 정밀하게 선별할 수 있습니다."
    )

    # 원본 랭킹 부여 (네이버 수집 순서 = 인기도/정확도 순위)
    df_work = df_items.copy()
    if "api_rank" not in df_work.columns:
        df_work["api_rank"] = df_work.groupby(["keyword", "channel_key"]).cumcount() + 1

    # 상단 1행: 검색어, 채널, 정렬 기준, 표시 건수
    col1, col2, col3, col4 = st.columns([1.5, 1.5, 2, 1])

    with col1:
        unique_kws = list(df_work["keyword"].unique())
        selected_kw = st.selectbox("🎯 검색어 필터", options=["전체"] + unique_kws, index=0, key="dv_filter_kw")

    with col2:
        available_channels = [ch for ch in SEARCH_CHANNELS if ch in df_work["channel_key"].unique()]
        selected_channel = st.selectbox(
            "📁 채널 필터",
            options=["전체"] + available_channels,
            format_func=lambda x: "전체 채널" if x == "전체" else f"{SEARCH_CHANNELS[x]['icon']} {SEARCH_CHANNELS[x]['name']}",
            index=0,
            key="dv_filter_ch",
        )

    with col3:
        sort_mode = st.selectbox(
            "⚡ 정렬 기준 조합",
            options=[
                "⏱️ 최근 업로드순 (발행일 최신순)",
                "🎯 포털 추천/인기도순 (네이버 랭킹순)",
                "🔍 제목 키워드 일치 우선순",
                "📝 본문 정보량 많은 순 (상세 분석순)",
                "⏳ 과거 업로드순 (오래된 순)",
            ],
            index=0,
            key="dv_sort_mode",
        )

    with col4:
        display_limit = st.selectbox("표시 건수", options=[20, 50, 100, "전체"], index=1, key="dv_limit")

    # 상단 2행: 결과 내 텍스트 검색창 + CSV 다운로드 버튼
    col_search, col_dl = st.columns([3, 1.5])

    with col_search:
        text_query = st.text_input(
            "🔍 결과 내 본문·제목·작성자 재검색",
            placeholder="단어 입력 시 실시간으로 일치하는 문서만 필터링합니다...",
            key="dv_text_search",
        ).strip().lower()

    # 1. 기본 필터링 적용 (검색어, 채널)
    filtered_df = df_work.copy()
    if selected_kw != "전체":
        filtered_df = filtered_df[filtered_df["keyword"] == selected_kw]
    if selected_channel != "전체":
        filtered_df = filtered_df[filtered_df["channel_key"] == selected_channel]

    # 2. 결과 내 텍스트 검색 필터링
    if text_query:
        mask = (
            filtered_df["title"].fillna("").str.lower().str.contains(text_query)
            | filtered_df["description"].fillna("").str.lower().str.contains(text_query)
            | filtered_df.get("bloggername", pd.Series("", index=filtered_df.index)).fillna("").str.lower().str.contains(text_query)
            | filtered_df.get("cafename", pd.Series("", index=filtered_df.index)).fillna("").str.lower().str.contains(text_query)
            | filtered_df.get("domain", pd.Series("", index=filtered_df.index)).fillna("").str.lower().str.contains(text_query)
        )
        filtered_df = filtered_df[mask]

    # 3. 정렬 적용
    if "최근 업로드순" in sort_mode:
        # pub_date_str 내림차순, 없는 경우 빈 문자열로 정렬
        if "pub_date_str" in filtered_df.columns:
            filtered_df["_sort_date"] = filtered_df["pub_date_str"].fillna("")
            filtered_df = filtered_df.sort_values(by=["_sort_date", "api_rank"], ascending=[False, True])
            filtered_df = filtered_df.drop(columns=["_sort_date"])
    elif "포털 추천/인기도순" in sort_mode:
        filtered_df = filtered_df.sort_values(by="api_rank", ascending=True)
    elif "제목 키워드 일치" in sort_mode:
        if "keyword_in_title" in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=["keyword_in_title", "api_rank"], ascending=[False, True])
    elif "본문 정보량" in sort_mode:
        if "total_len" in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by="total_len", ascending=False)
    elif "과거 업로드순" in sort_mode:
        if "pub_date_str" in filtered_df.columns:
            filtered_df["_sort_date"] = filtered_df["pub_date_str"].fillna("9999-99-99")
            filtered_df = filtered_df.sort_values(by=["_sort_date", "api_rank"], ascending=[True, True])
            filtered_df = filtered_df.drop(columns=["_sort_date"])

    # CSV 다운로드 버튼 배치
    with col_dl:
        csv_data = filtered_df.drop(columns=["raw_data"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 현재 필터 데이터 CSV 다운로드",
            data=csv_data,
            file_name=f"naver_filtered_search_{selected_kw}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 필터 결과 안내 캡션
    total_found = len(filtered_df)
    active_filters = []
    if selected_kw != "전체":
        active_filters.append(f"검색어: `{selected_kw}`")
    if selected_channel != "전체":
        active_filters.append(f"채널: `{SEARCH_CHANNELS[selected_channel]['name']}`")
    if text_query:
        active_filters.append(f"검색어 포함: `{text_query}`")
    active_filters.append(f"정렬: `{sort_mode.split()[1]}`")

    filter_desc = " · ".join(active_filters)
    st.caption(f"📊 조건 부합 결과: **{total_found:,}건** ({filter_desc})")

    if total_found == 0:
        st.warning("⚠️ 선택하신 검색 및 정렬 조건에 일치하는 문서가 없습니다. 검색어나 필터를 조정해 보세요.")
        return

    # 채널 탭별 표시
    channel_keys_in_filtered = [k for k in SEARCH_CHANNELS if k in filtered_df["channel_key"].unique()]
    if not channel_keys_in_filtered:
        channel_keys_in_filtered = list(filtered_df["channel_key"].unique())

    tab_labels = [
        f"{SEARCH_CHANNELS.get(k, {}).get('icon', '📌')} {SEARCH_CHANNELS.get(k, {}).get('name', k)} ({len(filtered_df[filtered_df['channel_key'] == k]):,}건)"
        for k in channel_keys_in_filtered
    ]
    tabs = st.tabs(tab_labels)

    for tab, ch_key in zip(tabs, channel_keys_in_filtered):
        with tab:
            ch_data = filtered_df[filtered_df["channel_key"] == ch_key]
            if display_limit != "전체":
                ch_data = ch_data.head(int(display_limit))

            # 이미지 채널 레이아웃
            if ch_key == "image":
                img_cols = st.columns(4)
                for idx, (_, row) in enumerate(ch_data.iterrows()):
                    col = img_cols[idx % 4]
                    with col:
                        thumb = row.get("thumbnail") or row.get("link")
                        if thumb:
                            st.image(thumb, use_container_width=True)
                        rank_num = row.get("api_rank", idx + 1)
                        st.markdown(f"**#{rank_num} [{row.get('keyword')}]** {row.get('title')[:35]}...")
                        if row.get("sizeheight") and row.get("sizewidth"):
                            st.caption(f"📐 해상도: {row.get('sizewidth')}×{row.get('sizeheight')} px")
                        if row.get("link"):
                            st.markdown(f"[🔗 원본 링크]({row.get('link')})")
                        st.markdown("---")

            # 지역(플레이스) 레이아웃
            elif ch_key == "local":
                for idx, (_, row) in enumerate(ch_data.iterrows(), start=1):
                    rank_num = row.get("api_rank", idx)
                    with st.container():
                        st.markdown(f"#### 📍 #{rank_num}. {row.get('title')}")
                        badges = [
                            f"🔍 검색어: `{row.get('keyword')}`",
                            f"🏷️ 분류: `{row.get('category', '정보 없음')}`",
                        ]
                        if row.get("telephone"):
                            badges.append(f"📞 전화: `{row.get('telephone')}`")
                        st.caption(" | ".join(badges))

                        road_addr = row.get("roadAddress")
                        addr = row.get("address")
                        if road_addr:
                            st.markdown(f"🛣️ **도로명**: {road_addr}")
                        if addr:
                            st.markdown(f"🏠 **지번**: {addr}")
                        if row.get("link"):
                            st.markdown(f"[👉 지도 및 상세정보 보기]({row.get('link')})")
                        st.markdown("---")

            # 텍스트 기반 일반 채널 (뉴스, 블로그, 카페, 지식iN, 웹문서, 백과사전)
            else:
                for idx, (_, row) in enumerate(ch_data.iterrows(), start=1):
                    rank_num = row.get("api_rank", idx)
                    rank_badge = f"🥇 {rank_num}위" if rank_num == 1 else (f"🥈 {rank_num}위" if rank_num == 2 else (f"🥉 {rank_num}위" if rank_num == 3 else f"#{rank_num}"))

                    with st.container():
                        st.markdown(f"##### {rank_badge} {row.get('title')}")

                        # 메타데이터 뱃지 행
                        meta_badges = []
                        if row.get("keyword"):
                            meta_badges.append(f"🔍 `{row['keyword']}`")

                        # 업로드 일시 표시
                        date_display = row.get("pub_date_str")
                        if date_display:
                            weekday_str = f" ({row.get('pub_weekday')})" if row.get("pub_weekday") else ""
                            hour_str = f" {row.get('pub_hour')}시" if pd.notna(row.get("pub_hour")) else ""
                            meta_badges.append(f"📅 **발행:** {date_display}{hour_str}{weekday_str}")
                        elif row.get("pub_date"):
                            meta_badges.append(f"📅 **발행:** {str(row['pub_date'])[:16]}")

                        # 출처 / 작성자 / 언론사
                        if row.get("bloggername"):
                            meta_badges.append(f"✍️ **블로거:** {row['bloggername']}")
                        elif row.get("cafename"):
                            meta_badges.append(f"☕ **카페:** {row['cafename']}")
                        elif row.get("domain"):
                            meta_badges.append(f"🌐 **출처:** {row['domain']}")

                        # 분량 / 키워드 일치
                        if row.get("total_len"):
                            meta_badges.append(f"📏 **본문:** {row['total_len']:,}자")
                        if row.get("keyword_in_title"):
                            meta_badges.append("🎯 **제목 키워드 일치**")

                        if meta_badges:
                            st.caption(" &nbsp;|&nbsp; ".join(meta_badges))

                        # 본문 요약문
                        if row.get("description"):
                            st.markdown(f"> {row.get('description')}")

                        if row.get("link"):
                            st.markdown(f"[🔗 원문 기사/포스트 바로가기]({row.get('link')})")
                        st.markdown("---")
