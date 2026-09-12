import pandas as pd
import streamlit as st


def render_metrics_cards(
    df_items: pd.DataFrame,
    df_summary: pd.DataFrame,
    df_trend: pd.DataFrame,
    keywords: list[str],
):
    """
    상단 주요 KPI 메트릭 카드 렌더링 (Toss/Linear 스타일 프리미엄 카드 디자인)
    """
    col1, col2, col3, col4 = st.columns(4)

    total_fetched = len(df_items) if not df_items.empty else 0

    top_buzz_kw = "-"
    top_buzz_val_str = "0건"
    if not df_summary.empty:
        buzz_by_kw = df_summary.groupby("keyword")["total_count"].sum()
        top_buzz_kw = buzz_by_kw.idxmax()
        top_buzz_val = buzz_by_kw.max()
        top_buzz_val_str = f"포털 총 {top_buzz_val:,}건"

    top_trend_kw = "-"
    top_trend_val_str = "0.0 pt"
    if not df_trend.empty:
        avg_trend = df_trend.groupby("keyword")["ratio"].mean()
        top_trend_kw = avg_trend.idxmax()
        top_trend_val = avg_trend.max()
        top_trend_val_str = f"평균 지수 {top_trend_val:.1f} pt"

    card_template = """
    <div class="kpi-card {theme}">
        <div class="kpi-top-row">
            <span class="kpi-icon-pill">{icon}</span>
            <span class="kpi-title">{title}</span>
        </div>
        <div class="kpi-main-val">{value}</div>
        <div class="kpi-sub-badge">{subtext}</div>
    </div>
    """

    with col1:
        st.markdown(
            card_template.format(
                theme="kpi-emerald",
                icon="🎯",
                title="비교 검색어 수",
                value=f"{len(keywords)} <span class='kpi-unit'>개</span>",
                subtext="🟢 실시간 다중 비교",
            ),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            card_template.format(
                theme="kpi-blue",
                icon="📥",
                title="총 수집 데이터",
                value=f"{total_fetched:,} <span class='kpi-unit'>건</span>",
                subtext="📊 8대 검색 채널 전수",
            ),
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            card_template.format(
                theme="kpi-violet",
                icon="🔥",
                title="최다 버즈 검색어",
                value=f"<span class='kpi-text-val'>{top_buzz_kw}</span>",
                subtext=f"📢 {top_buzz_val_str}",
            ),
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            card_template.format(
                theme="kpi-amber",
                icon="📈",
                title="데이터랩 관심도 1위",
                value=f"<span class='kpi-text-val'>{top_trend_kw}</span>",
                subtext=f"⚡ {top_trend_val_str}",
            ),
            unsafe_allow_html=True,
        )
