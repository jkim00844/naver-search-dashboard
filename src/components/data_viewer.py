import pandas as pd
import streamlit as st
from src.api.endpoints import SEARCH_CHANNELS


def render_data_viewer(df_items: pd.DataFrame):
    """
    수집된 상세 검색 결과 탐색 및 채널별 카드/테이블 뷰어, CSV 다운로드
    """
    if df_items.empty:
        st.info("조회된 검색 결과가 없습니다.")
        return

    st.markdown("### 🗂️ 수집 원문 데이터 탐색 및 다운로드")

    # 상단 필터 & 다운로드 행
    filter_col1, filter_col2, dl_col = st.columns([2, 2, 2])
    with filter_col1:
        unique_kws = list(df_items["keyword"].unique())
        selected_kw = st.selectbox("검색어 필터", options=["전체"] + unique_kws, index=0)
    with filter_col2:
        available_channels = [ch for ch in SEARCH_CHANNELS if ch in df_items["channel_key"].unique()]
        selected_channel = st.selectbox(
            "채널 필터",
            options=["전체"] + available_channels,
            format_func=lambda x: "전체 채널" if x == "전체" else f"{SEARCH_CHANNELS[x]['icon']} {SEARCH_CHANNELS[x]['name']}",
            index=0,
        )
    with dl_col:
        # CSV 다운로드
        csv_data = df_items.drop(columns=["raw_data"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="📥 전체 데이터 CSV 다운로드",
            data=csv_data,
            file_name="naver_market_insight_data.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 필터링 적용
    filtered_df = df_items.copy()
    if selected_kw != "전체":
        filtered_df = filtered_df[filtered_df["keyword"] == selected_kw]
    if selected_channel != "전체":
        filtered_df = filtered_df[filtered_df["channel_key"] == selected_channel]

    st.caption(f"총 **{len(filtered_df):,}** 건의 검색 결과가 표시됩니다.")

    # 탭별 채널별 뷰어
    channel_keys_in_filtered = filtered_df["channel_key"].unique()
    if len(channel_keys_in_filtered) == 0:
        st.write("해당 조건에 부합하는 데이터가 없습니다.")
        return

    tabs = st.tabs([f"{SEARCH_CHANNELS.get(k, {}).get('icon', '📌')} {SEARCH_CHANNELS.get(k, {}).get('name', k)} ({len(filtered_df[filtered_df['channel_key'] == k])})" for k in channel_keys_in_filtered])

    for tab, ch_key in zip(tabs, channel_keys_in_filtered):
        with tab:
            ch_data = filtered_df[filtered_df["channel_key"] == ch_key]

            # 이미지 채널 특화 레이아웃
            if ch_key == "image":
                img_cols = st.columns(4)
                for idx, (_, row) in enumerate(ch_data.iterrows()):
                    col = img_cols[idx % 4]
                    with col:
                        thumb = row.get("thumbnail") or row.get("link")
                        if thumb:
                            st.image(thumb, use_container_width=True)
                        st.markdown(f"**[{row.get('keyword')}]** {row.get('title')[:35]}...")
                        if row.get("link"):
                            st.markdown(f"[🔗 원본 링크]({row.get('link')})")
                        st.markdown("---")

            # 지역(플레이스) 특화 레이아웃
            elif ch_key == "local":
                for _, row in ch_data.iterrows():
                    with st.container():
                        st.markdown(f"#### 📍 {row.get('title')}")
                        st.markdown(f"**분류**: `{row.get('category', '정보 없음')}` | **검색어**: `{row.get('keyword')}`")
                        road_addr = row.get("roadAddress")
                        addr = row.get("address")
                        if road_addr:
                            st.markdown(f"🛣️ **도로명**: {road_addr}")
                        if addr:
                            st.markdown(f"🏠 **지번**: {addr}")
                        if row.get("link"):
                            st.markdown(f"[👉 지도/상세정보 보기]({row.get('link')})")
                        st.markdown("---")

            # 텍스트 기반 일반 채널 (뉴스, 블로그, 카페, 지식iN, 웹문서, 백과사전)
            else:
                for _, row in ch_data.iterrows():
                    with st.container():
                        st.markdown(f"##### 📌 {row.get('title')}")
                        meta_info = []
                        if row.get("keyword"):
                            meta_info.append(f"🔍 **검색어**: `{row['keyword']}`")
                        if row.get("pub_date"):
                            meta_info.append(f"📅 **일시**: {row['pub_date']}")
                        if row.get("bloggername"):
                            meta_info.append(f"✍️ **작성자**: {row['bloggername']}")
                        elif row.get("cafename"):
                            meta_info.append(f"☕ **카페**: {row['cafename']}")

                        if meta_info:
                            st.caption(" | ".join(meta_info))

                        if row.get("description"):
                            st.markdown(f"> {row.get('description')}")

                        if row.get("link"):
                            st.markdown(f"[🔗 원문 바로가기]({row.get('link')})")
                        st.markdown("---")
