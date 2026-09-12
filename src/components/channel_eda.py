import pandas as pd
import streamlit as st
import plotly.express as px

from src.services.analyzer import DataAnalyzer
from src.components.charts import (
    plot_top_ranking_bar,
    plot_time_series_line,
    plot_distribution_box,
    plot_distribution_histogram,
    plot_scatter_correlation,
    plot_heatmap_matrix,
    plot_weekday_hour_heatmap,
    LIGHT_PALETTE,
    LIGHT_LAYOUT,
)


def render_channel_eda_tab(df_items: pd.DataFrame, channel_key: str, channel_name: str, channel_icon: str, keywords: list[str]):
    """
    각 검색 API 채널별(뉴스, 블로그, 카페, 웹문서, 백과사전, 지식iN 등) 5개 이상 그래프 + 5개 이상 통계표 심층 EDA 뷰어
    """
    if df_items.empty:
        st.info(f"수집된 {channel_name} 데이터가 없습니다.")
        return

    df_ch = df_items[df_items["channel_key"] == channel_key].copy()
    if df_ch.empty:
        st.info(f"선택하신 조건에 해당하는 {channel_name} 데이터가 없습니다.")
        return

    st.markdown(
        f"""
        <div style="margin-bottom: 1.25rem;">
            <h3 style="font-size: 1.4rem; font-weight: 800; color: #0F172A; margin: 0 0 4px 0;">{channel_icon} {channel_name} API 심층 탐색적 데이터 분석 (EDA)</h3>
            <p style="font-size: 0.88rem; color: #64748B; margin: 0;">수집된 총 {len(df_ch):,}건의 콘텐츠를 다각도로 분석한 통계표와 시각화 대시보드입니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. 상단 KPI 메트릭 요약 (모던 프리미엄 카드)
    total_docs = len(df_ch)
    avg_desc_len = df_ch["desc_len"].mean() if "desc_len" in df_ch.columns else 0.0
    
    # 채널별 대표 출처/분류 엔티티 컬럼 결정 (피봇 및 교차표에서 keyword 컬럼과의 중복 충돌 방지)
    if channel_key == "news":
        source_col = "domain"
        source_label = "언론사/도메인"
    elif channel_key == "blog":
        source_col = "bloggername" if "bloggername" in df_ch.columns and df_ch["bloggername"].notna().any() else "domain"
        source_label = "블로거/작성자"
    elif channel_key == "cafearticle":
        source_col = "cafename" if "cafename" in df_ch.columns and df_ch["cafename"].notna().any() else "domain"
        source_label = "커뮤니티 카페"
    elif channel_key == "webkr":
        source_col = "domain"
        source_label = "웹 도메인"
    elif channel_key == "encyc":
        source_col = "has_thumbnail" if "has_thumbnail" in df_ch.columns and df_ch["has_thumbnail"].nunique() > 1 else "keyword_in_title"
        source_label = "썸네일 유무" if source_col == "has_thumbnail" else "제목 키워드 일치여부"
    elif channel_key == "local":
        source_col = "category" if "category" in df_ch.columns and df_ch["category"].notna().any() else "domain"
        source_label = "업종 카테고리"
    elif channel_key == "image":
        source_col = "domain" if "domain" in df_ch.columns and df_ch["domain"].notna().any() else "keyword_in_title"
        source_label = "이미지 출처 도메인"
    else:
        source_col = "domain" if ("domain" in df_ch.columns and df_ch["domain"].notna().any()) else "keyword_in_title"
        source_label = "출처 도메인"

    # 만약 source_col이 여전히 keyword와 같으면 keyword_in_title로 변경
    if source_col == "keyword":
        source_col = "keyword_in_title"
        source_label = "제목 키워드 일치여부"

    unique_sources = df_ch[source_col].nunique() if source_col in df_ch.columns else 0
    kw_match_rate = (df_ch["keyword_in_title"].mean() * 100) if "keyword_in_title" in df_ch.columns else 0.0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="kpi-card kpi-emerald">
                <div class="kpi-top-row"><span class="kpi-icon-pill">📄</span><span class="kpi-title">총 수집 문서</span></div>
                <div class="kpi-main-val">{total_docs:,}<span class="kpi-unit">건</span></div>
                <div class="kpi-sub-badge">📌 {channel_name} 채널</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="kpi-card kpi-blue">
                <div class="kpi-top-row"><span class="kpi-icon-pill">📝</span><span class="kpi-title">평균 본문 글자수</span></div>
                <div class="kpi-main-val">{avg_desc_len:.1f}<span class="kpi-unit">자</span></div>
                <div class="kpi-sub-badge">📏 텍스트 분량 평균</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="kpi-card kpi-violet">
                <div class="kpi-top-row"><span class="kpi-icon-pill">🌐</span><span class="kpi-title">고유 {source_label}</span></div>
                <div class="kpi-main-val">{unique_sources:,}<span class="kpi-unit">개</span></div>
                <div class="kpi-sub-badge">🏷️ 출처 다양성</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="kpi-card kpi-amber">
                <div class="kpi-top-row"><span class="kpi-icon-pill">🎯</span><span class="kpi-title">키워드 직접포함율</span></div>
                <div class="kpi-main-val">{kw_match_rate:.1f}<span class="kpi-unit">%</span></div>
                <div class="kpi-sub-badge">🔍 제목 직접 일치</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ==========================================
    # 📈 [섹션 1] 시각화 분석 (그래프 5개 이상, 파이차트 배제)
    # ==========================================
    st.markdown(f"#### 📈 {channel_name} 시각화 분석")
    st.caption("※ 파이차트를 배제하고 직관적인 막대 차트, 시계열 라인, 박스플롯, 히스토그램, 산점도, 히트맵으로 시각화했습니다.")

    # Graph Row 1
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.markdown(f"##### 1. 상위 {source_label} 분포 랭킹")
        if source_col in df_ch.columns and df_ch[source_col].notna().any():
            top_counts = df_ch[source_col].value_counts().head(15).reset_index()
            top_counts.columns = [source_label, "문서 수"]
            fig1 = plot_top_ranking_bar(
                top_counts,
                x_col="문서 수",
                y_col=source_label,
                title=f"Top 15 {source_label} 점유 현황",
                orientation="h",
            )
            st.plotly_chart(fig1, use_container_width=True, key=f"{channel_key}_chart_ranking")
        else:
            st.info("출처 정보를 표시할 수 없습니다.")

    with g_col2:
        st.markdown("##### 2. 검색어별 기사/게시글 수집 건수 비교")
        kw_counts = df_ch["keyword"].value_counts().reset_index()
        kw_counts.columns = ["검색어", "수집 건수"]
        fig2 = plot_top_ranking_bar(
            kw_counts,
            x_col="수집 건수",
            y_col="검색어",
            title="검색어별 수집 문서 수",
            orientation="h",
            color_col="검색어",
        )
        st.plotly_chart(fig2, use_container_width=True, key=f"{channel_key}_chart_kw_counts")

    # Graph Row 2
    g_col3, g_col4 = st.columns(2)

    with g_col3:
        st.markdown("##### 3. 검색어별 텍스트 글자수 분포 (Box Plot)")
        target_len_col = "desc_len" if "desc_len" in df_ch.columns else "total_len"
        fig3 = plot_distribution_box(
            df_ch,
            y_col=target_len_col,
            x_col="keyword",
            title=f"검색어별 본문 길이(사분위수/중앙값/이상치)",
            y_label="글자수 (Characters)",
        )
        st.plotly_chart(fig3, use_container_width=True, key=f"{channel_key}_chart_box")

    with g_col4:
        st.markdown("##### 4. 텍스트 분량 도수분포 (Histogram)")
        fig4 = plot_distribution_histogram(
            df_ch,
            x_col=target_len_col,
            group_col="keyword",
            title=f"{channel_name} 본문 글자수 도수분포 히스토그램",
            nbins=25,
        )
        st.plotly_chart(fig4, use_container_width=True, key=f"{channel_key}_chart_hist")

    # Graph Row 3
    g_col5, g_col6 = st.columns(2)

    with g_col5:
        st.markdown("##### 5. 제목 글자수 vs 본문 글자수 상관관계 (Scatter Plot)")
        if "title_len" in df_ch.columns and "desc_len" in df_ch.columns:
            fig5 = plot_scatter_correlation(
                df_ch,
                x_col="title_len",
                y_col="desc_len",
                group_col="keyword",
                title="제목 길이 vs 본문 길이 상관 산점도",
                x_label="제목 글자수",
                y_label="본문 글자수",
            )
            st.plotly_chart(fig5, use_container_width=True, key=f"{channel_key}_chart_scatter")
        else:
            st.info("텍스트 길이 데이터가 충분하지 않습니다.")

    with g_col6:
        # 채널 특성에 따른 6번째 차트
        if channel_key == "news" and "pub_hour" in df_ch.columns and df_ch["pub_hour"].notna().any():
            st.markdown("##### 6. ⏰ 언론 보도 골든타임 (요일 × 시간대 히트맵)")
            fig6 = plot_weekday_hour_heatmap(df_ch, title="뉴스 보도 집중 시간대 (요일 × 시간대)")
            st.plotly_chart(fig6, use_container_width=True, key=f"{channel_key}_chart_golden_heatmap")
        elif "pub_weekday" in df_ch.columns and df_ch["pub_weekday"].notna().any():
            st.markdown("##### 6. 요일별(월~일) 게시/보도 분포 (Bar Chart)")
            weekday_order = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
            w_counts = df_ch["pub_weekday"].value_counts().reindex(weekday_order).fillna(0).reset_index()
            w_counts.columns = ["요일", "문서 수"]
            fig6 = px.bar(
                w_counts,
                x="요일",
                y="문서 수",
                title="<b>요일별 콘텐츠 집중도</b>",
                color="문서 수",
                color_continuous_scale="Tealgrn",
            )
            fig6.update_layout(**LIGHT_LAYOUT, margin=dict(l=20, r=20, t=50, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig6, use_container_width=True, key=f"{channel_key}_chart_weekday")
        elif "pub_date_str" in df_ch.columns and df_ch["pub_date_str"].notna().any():
            st.markdown("##### 6. 일자별 콘텐츠 발행 추이 (Time Series)")
            daily_trend = df_ch.groupby(["pub_date_str", "keyword"]).size().reset_index(name="문서 수")
            fig6 = plot_time_series_line(
                daily_trend,
                date_col="pub_date_str",
                val_col="문서 수",
                group_col="keyword",
                title="일자별 발행 추이",
            )
            st.plotly_chart(fig6, use_container_width=True, key=f"{channel_key}_chart_timeseries")
        elif "url_depth" in df_ch.columns:
            st.markdown("##### 6. URL 경로 깊이(Depth) 분포")
            depth_counts = df_ch["url_depth"].value_counts().sort_index().reset_index()
            depth_counts.columns = ["URL Depth", "문서 수"]
            fig6 = px.bar(
                depth_counts,
                x="URL Depth",
                y="문서 수",
                title="<b>웹페이지 URL 경로 깊이 분포</b>",
                color="문서 수",
                color_continuous_scale="Tealgrn",
            )
            fig6.update_layout(**LIGHT_LAYOUT, margin=dict(l=20, r=20, t=50, b=20), coloraxis_showscale=False)
            st.plotly_chart(fig6, use_container_width=True, key=f"{channel_key}_chart_urldepth")
        else:
            st.markdown("##### 6. 검색어 x 제목 키워드 포함여부 교차 히트맵")
            ct_heat = pd.crosstab(df_ch["keyword"], df_ch["keyword_in_title"])
            fig6 = plot_heatmap_matrix(ct_heat, title="검색어별 제목 내 키워드 포함 히트맵", x_label="제목 포함 여부", y_label="검색어")
            st.plotly_chart(fig6, use_container_width=True, key=f"{channel_key}_chart_heatmap")

    st.markdown("---")

    # ==========================================
    # 📋 [섹션 2] 통계 계산 표 (표 5개 이상)
    # ==========================================
    st.markdown(f"### 📋 {channel_name} 고급 통계 분석표 (Tables - 5종 이상)")
    st.caption("기술통계량, 교차표(Cross-tab), 피봇테이블, 도수분포표, 출처 랭킹표 등 다양한 통계 계산 결과를 제공합니다.")

    # Table 1: 기술통계 요약표
    st.markdown("##### 1. 텍스트 지표 기술통계 요약표 (Descriptive Statistics)")
    st.caption("평균(Mean), 표준편차(Std), 최솟값, 제1사분위(Q1), 중앙값(Median), 제3사분위(Q3), 최댓값, 왜도(Skewness)")
    stat_cols = [c for c in ["desc_len", "title_len", "desc_words", "title_words"] if c in df_ch.columns]
    df_desc_stats = DataAnalyzer.calculate_descriptive_stats(df_ch, numeric_cols=stat_cols, group_col="keyword")
    st.dataframe(df_desc_stats, use_container_width=True)

    # Table 2: 검색어 x 주요 출처/도메인 피봇테이블
    st.markdown(f"##### 2. 검색어 x 주요 {source_label} 피봇테이블 (Pivot Table)")
    st.caption(f"각 검색어별 상위 10대 {source_label}의 문서 발행 건수 및 합계 집계")
    pivot_idx = source_col if source_col != "keyword" else "keyword_in_title"
    top_10_entities = df_ch[pivot_idx].value_counts().head(10).index
    df_pivot_data = df_ch[df_ch[pivot_idx].isin(top_10_entities)].copy()
    if not df_pivot_data.empty:
        df_pivot_data[pivot_idx] = df_pivot_data[pivot_idx].astype(str)
        pivot_table = pd.pivot_table(
            df_pivot_data,
            index=pivot_idx,
            columns="keyword",
            values="title",
            aggfunc="count",
            fill_value=0,
            margins=True,
            margins_name="합계",
        )
        st.dataframe(pivot_table, use_container_width=True)
    else:
        st.info("피봇테이블을 생성할 출처 데이터가 부족합니다.")

    # Table 3: 교차표 (Cross-tabulation)
    st.markdown("##### 3. 범주형 변수 교차표 (Cross-tabulation)")
    col_t3_1, col_t3_2 = st.columns(2)
    with col_t3_1:
        st.markdown("**[교차표 A] 검색어 x 제목 키워드 포함 빈도**")
        ct_kw = DataAnalyzer.create_crosstab(df_ch, index_col="keyword", column_col="keyword_in_title")
        ct_kw.columns = ["미포함" if c is False else "포함" if c is True else str(c) for c in ct_kw.columns]
        st.dataframe(ct_kw, use_container_width=True)
    with col_t3_2:
        st.markdown("**[교차표 B] 검색어 x 제목 키워드 포함 비율 (%)**")
        ct_pct = DataAnalyzer.create_crosstab(df_ch, index_col="keyword", column_col="keyword_in_title", normalize=True)
        ct_pct.columns = ["미포함(%)" if c is False else "포함(%)" if c is True else str(c) for c in ct_pct.columns]
        st.dataframe(ct_pct.style.format("{:.1f}%"), use_container_width=True)

    # Table 4: 본문 글자수 도수분포표
    st.markdown("##### 4. 텍스트 분량 구간별 도수분포표 (Frequency Distribution Table)")
    st.caption("구간별 빈도, 상대도수(비율), 누적빈도, 누적상대도수(%)")
    df_freq = DataAnalyzer.create_frequency_distribution(df_ch, col=target_len_col)
    st.dataframe(df_freq, use_container_width=True)

    # Table 5: 상위 출처/작성자 종합 랭킹표
    st.markdown(f"##### 5. 상위 {source_label} 종합 랭킹 및 활동 분석표")
    st.caption(f"문서 발행 건수 순위, 전체 비중(%), 평균 본문 글자수 및 다룬 검색어 목록")
    df_top_sources = DataAnalyzer.summarize_top_entities(df_ch, entity_col=source_col, top_n=15, length_col=target_len_col)
    st.dataframe(df_top_sources, use_container_width=True)
