from datetime import datetime
import textwrap

import streamlit as st
import pandas as pd

from src.api.client import NaverApiClient
from src.services.collector import DataCollector
from src.services.analyzer import DataAnalyzer
from src.services.report_generator import PdfReportGenerator
from src.utils.config import is_valid_credentials

from src.api.endpoints import SEARCH_CHANNELS
from src.components.sidebar import render_sidebar
from src.components.metrics_cards import render_metrics_cards
from src.components.charts import (
    plot_datalab_trend,
    plot_channel_comparison,
    plot_channel_share_treemap,
    plot_channel_share_horizontal_bar,
    plot_top_keywords_bar,
    plot_cooccurrence_network,
    render_channel_share_toss_card,
)
from src.components.wordcloud_view import render_wordcloud
from src.components.data_viewer import render_data_viewer
from src.components.channel_eda import render_channel_eda_tab


# 페이지 기본 설정
st.set_page_config(
    page_title="네이버 마켓 인사이트 & 검색 EDA 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 세련되고 가독성 높은 모던 UI 스타일링 (Pretendard 웹폰트 + Linear/Toss 디자인 시스템)
st.html(
    textwrap.dedent(
        """\
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <style>
    :root {
        --bg-main: #FFFFFF;
        --bg-subtle: #F8FAFC;
        --border: #E2E8F0;
        --border-hover: #CBD5E1;
        --text-strong: #0F172A;
        --text-body: #334155;
        --text-muted: #64748B;
        --accent: #02B852;
        --accent-hover: #029B45;
        --radius-lg: 14px;
        --radius-md: 10px;
        --radius-sm: 6px;
    }

    /* Pretendard 글로벌 폰트 및 베이스 타이포그래피 */
    html, body, p, div, input, button, select, textarea, label, h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"],
    [data-testid="stSidebarContent"],
    [data-testid="stHeader"] {
        font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, Roboto, "Helvetica Neue", "Segoe UI", sans-serif;
        letter-spacing: -0.022em;
    }

    /* Streamlit Material Icons 보호 (화살표, 토글, 액션 아이콘 텍스트 깨짐 방지) */
    [data-testid*="stIcon"],
    [data-testid="stIconMaterial"],
    [data-testid="stExpanderToggleIcon"],
    [class*="material-symbols"],
    [class*="material-icons"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-icons,
    [data-testid="stExpander"] summary span:first-child,
    [data-testid="stExpanderToggleIcon"] * {
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: "liga" !important;
        -webkit-font-smoothing: antialiased !important;
    }

    /* 메인 콘텐츠 여백 정리 (Streamlit 상단 헤더 겹침 완벽 방지) */
    .block-container {
        padding-top: 4.25rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1360px !important;
    }

    /* 히어로 헤더 배너 */
    .hero-container {
        margin-top: 0.5rem;
        margin-bottom: 2rem;
        padding-bottom: 1.25rem;
        border-bottom: 1px solid var(--border);
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 5px 14px;
        background: rgba(2, 184, 82, 0.08);
        border: 1px solid rgba(2, 184, 82, 0.25);
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        color: #029443;
        letter-spacing: 0.02em;
        margin-bottom: 0.75rem;
        line-height: 1.2;
    }
    .live-dot {
        width: 7px;
        height: 7px;
        background-color: #02B852;
        border-radius: 50%;
        box-shadow: 0 0 0 2px rgba(2, 184, 82, 0.2);
    }
    .hero-title {
        font-size: 2.15rem;
        font-weight: 800;
        color: var(--text-strong);
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.03em;
        line-height: 1.2;
    }
    .hero-title .accent-text {
        background: linear-gradient(135deg, #02B852 0%, #059669 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-desc {
        font-size: 0.98rem;
        color: var(--text-muted);
        margin: 0;
        line-height: 1.6;
        font-weight: 400;
    }

    /* 사이드바 스타일링 */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-subtle) !important;
        border-right: 1px solid var(--border) !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem !important;
    }

    /* 프리미엄 KPI 메트릭 카드 */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 6px 12px -2px rgba(0, 0, 0, 0.02);
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -3px rgba(0, 0, 0, 0.06), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
        border-color: var(--border-hover);
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    .kpi-card.kpi-emerald::before { background: linear-gradient(90deg, #02B852, #10B981); }
    .kpi-card.kpi-blue::before { background: linear-gradient(90deg, #2563EB, #3B82F6); }
    .kpi-card.kpi-violet::before { background: linear-gradient(90deg, #7C3AED, #8B5CF6); }
    .kpi-card.kpi-amber::before { background: linear-gradient(90deg, #D97706, #F59E0B); }

    .kpi-top-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }
    .kpi-icon-pill {
        font-size: 1rem;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm);
        background: #F1F5F9;
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-muted);
    }
    .kpi-main-val {
        font-size: 1.75rem;
        font-weight: 800;
        color: var(--text-strong);
        letter-spacing: -0.03em;
        line-height: 1.2;
        margin-bottom: 8px;
        font-feature-settings: "tnum";
    }
    .kpi-unit {
        font-size: 1rem;
        font-weight: 600;
        color: #94A3B8;
        margin-left: 2px;
    }
    .kpi-text-val {
        font-size: 1.35rem;
        font-weight: 800;
        color: var(--text-strong);
    }
    .kpi-sub-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.78rem;
        font-weight: 600;
        color: #475569;
        background: #F8FAFC;
        border: 1px solid var(--border);
        padding: 3px 8px;
        border-radius: var(--radius-sm);
    }

    /* 탭 헤더 스타일 (모던 캡슐형 세그먼트 탭) */
    div[data-baseweb="tab-list"] {
        background-color: #F1F5F9 !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        padding: 4px !important;
        gap: 3px !important;
        margin-bottom: 1.75rem !important;
        overflow-x: auto !important;
    }
    button[data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        border-radius: 7px !important;
        padding: 8px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 600 !important;
        color: var(--text-muted) !important;
        transition: all 0.15s ease !important;
        white-space: nowrap !important;
    }
    button[data-baseweb="tab"]:hover {
        color: var(--text-strong) !important;
        background: rgba(255, 255, 255, 0.6) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: var(--text-strong) !important;
        font-weight: 700 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {
        display: none !important;
    }

    /* 데이터프레임 및 카드 컨테이너 */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-md) !important;
        background: #FAFAFA !important;
    }

    /* 실행 버튼 (세련된 에메랄드 그라디언트) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #03C75A 0%, #02B852 100%) !important;
        border: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        border-radius: var(--radius-md) !important;
        padding: 10px 18px !important;
        box-shadow: 0 2px 4px rgba(3, 199, 90, 0.25), 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 14px rgba(3, 199, 90, 0.35) !important;
        background: linear-gradient(135deg, #02b350 0%, #029b45 100%) !important;
    }
    button[kind="primary"]:active {
        transform: translateY(0) !important;
    }

    /* 토스/스트라이프형 채널 점유율 프로그레스 카드 */
    .toss-share-card {
        background: #FFFFFF;
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03), 0 4px 12px rgba(0, 0, 0, 0.02);
        margin-top: 6px;
    }
    .toss-share-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 12px;
        margin-bottom: 12px;
        border-bottom: 1px solid #F1F5F9;
    }
    .toss-header-left {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .toss-header-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #0F172A;
    }
    .toss-header-sub {
        font-size: 0.76rem;
        color: #94A3B8;
    }
    .toss-total-pill {
        display: inline-flex;
        align-items: center;
        padding: 3px 10px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        color: #475569;
    }
    .toss-share-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .toss-share-item {
        display: flex;
        flex-direction: column;
        gap: 5px;
        padding: 4px 6px;
        border-radius: var(--radius-sm);
        transition: background 0.15s ease;
    }
    .toss-share-item:hover {
        background: #F8FAFC;
    }
    .toss-item-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .toss-item-left {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .toss-rank-badge {
        width: 19px;
        height: 19px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 6px;
        background: #F1F5F9;
        color: #64748B;
        font-size: 0.72rem;
        font-weight: 700;
    }
    .toss-rank-badge.rank-1 { background: #FEF3C7; color: #D97706; }
    .toss-rank-badge.rank-2 { background: #E2E8F0; color: #475569; }
    .toss-rank-badge.rank-3 { background: #FFEDD5; color: #C2410C; }
    .toss-ch-icon {
        font-size: 1.05rem;
    }
    .toss-ch-name {
        font-size: 0.90rem;
        font-weight: 600;
        color: #1E293B;
    }
    .toss-item-right {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .toss-count-text {
        font-size: 0.83rem;
        color: #64748B;
        font-weight: 500;
    }
    .toss-pct-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 48px;
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
    }
    .toss-progress-track {
        width: 100%;
        height: 6px;
        background: #F1F5F9;
        border-radius: 9999px;
        overflow: hidden;
    }
    .toss-progress-bar {
        height: 100%;
        border-radius: 9999px;
        transition: width 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* PDF 종합 보고서 다운로드 배너 */
    .report-download-banner {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: var(--radius-md);
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }
    .report-badge {
        display: inline-block;
        font-size: 0.70rem;
        font-weight: 800;
        color: var(--accent);
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .report-banner-title {
        font-size: 1.08rem;
        font-weight: 700;
        color: var(--text-strong);
        margin-bottom: 4px;
    }
    .report-banner-desc {
        font-size: 0.85rem;
        color: var(--text-muted);
        line-height: 1.5;
    }
    </style>
    """
    )
)


def main():
    # 1. 사이드바 컨트롤 렌더링
    params = render_sidebar()

    # 모던 히어로 타이틀 헤더
    st.markdown(
        """
        <div class="hero-container">
            <div class="hero-badge">
                <span class="live-dot"></span>
                <span>NAVER SEARCH & DATALAB INTELLIGENCE</span>
            </div>
            <h1 class="hero-title">네이버 마켓 인사이트 <span class="accent-text">& 검색 EDA</span></h1>
            <p class="hero-desc">포털 8대 검색 채널(뉴스·블로그·카페·웹·백과·지식iN·지역·이미지)과 데이터랩 트렌드를 비교 분석하는 마켓 인텔리전스 대시보드</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    client_id = params["client_id"]
    client_secret = params["client_secret"]

    # 세션 상태 초기화
    if "collected_data" not in st.session_state:
        st.session_state.collected_data = None

    # 분석 시작 버튼 클릭 이벤트
    if params["run_btn"]:
        if not is_valid_credentials(client_id, client_secret):
            st.error("❌ 유효한 네이버 API Client ID 및 Client Secret을 `.env`에 설정해 주세요.")
            return

        api_client = NaverApiClient(client_id=client_id, client_secret=client_secret)
        collector = DataCollector(api_client=api_client)

        keywords = collector.parse_keywords(params["raw_keywords"])
        if not keywords:
            st.warning("⚠️ 최소 1개 이상의 검색어를 입력해 주세요.")
            return

        if not params["selected_channels"]:
            st.warning("⚠️ 최소 1개 이상의 수집 채널을 선택해 주세요.")
            return

        with st.spinner("네이버 API로부터 데이터를 실시간 수집 및 분석 중입니다..."):
            # 1) 검색 결과 8채널 수집
            df_items, df_summary, errors = collector.collect_search_data(
                keywords=keywords,
                channels=params["selected_channels"],
                display=params["display_count"],
                sort=params["sort_option"],
            )

            # 2) 데이터랩 트렌드 수집
            df_trend, trend_err = collector.collect_datalab_trend(
                keywords=keywords,
                start_date=params["start_date"],
                end_date=params["end_date"],
                time_unit=params["time_unit"],
            )

            if trend_err:
                errors.append(f"[데이터랩 트렌드] {trend_err}")

            st.session_state.collected_data = {
                "keywords": keywords,
                "df_items": df_items,
                "df_summary": df_summary,
                "df_trend": df_trend,
                "errors": errors,
            }

            if errors:
                st.warning(f"수집 중 {len(errors)}건의 안내/경고가 발생했습니다:")
                for err in errors:
                    st.caption(f"- {err}")
            else:
                st.success(f"총 {len(keywords)}개 검색어에 대한 데이터 수집 및 분석이 성공적으로 완료되었습니다!")

    # 데이터가 아직 없는 경우 안내 화면 렌더링
    if st.session_state.collected_data is None:
        render_welcome_screen(has_creds=is_valid_credentials(client_id, client_secret))
        return

    # 저장된 데이터 로드
    data = st.session_state.collected_data
    keywords = data["keywords"]
    df_items = data["df_items"]
    df_summary = data["df_summary"]
    df_trend = data["df_trend"]

    # 사이드바 빠른 PDF 보고서 다운로드 버튼
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📥 보고서 내보내기")
        try:
            sb_gen = PdfReportGenerator()
            sb_stats = {
                "total_buzz": df_summary["total_count"].sum() if not df_summary.empty else 0,
                "keyword_count": len(keywords),
                "top_channel": df_summary.groupby("channel_name")["total_count"].sum().idxmax() if not df_summary.empty else "-",
                "success_rate": 100.0,
            }
            today_str = datetime.now().strftime("%Y%m%d")
            sb_pdf_bytes = sb_gen.generate_report(
                df_summary=df_summary,
                df_trend=df_trend,
                keywords=keywords,
                selected_channels=params.get("selected_channels", []),
                stats=sb_stats,
            )
            st.download_button(
                label="📄 PDF 종합 보고서 다운로드",
                data=sb_pdf_bytes,
                file_name=f"네이버_종합시장분석보고서_{today_str}.pdf",
                mime="application/pdf",
                key="sidebar_download_pdf",
                use_container_width=True,
            )
        except Exception:
            pass

    # 2. 최상단 KPI 메트릭 카드
    render_metrics_cards(df_items, df_summary, df_trend, keywords)

    # 3. 메인 분석 탭 구성 (검색 API별 심층 EDA 전용 탭 포함)
    tab_list = [
        "📊 종합 개요 (Overview)",
        "📈 트렌드 분석 (Datalab)",
        "📰 뉴스 심층 EDA",
        "📝 블로그 심층 EDA",
        "☕ 카페글 심층 EDA",
        "🌐 웹문서 심층 EDA",
        "📚 백과사전 심층 EDA",
        "💡 지식iN 심층 EDA",
        "📍 지역 & 🖼️ 이미지",
        "🔤 키워드 & 형태소 NLP",
        "🗂️ 채널별 원문 탐색기",
    ]
    tabs = st.tabs(tab_list)

    tab_overview = tabs[0]
    tab_trend = tabs[1]
    tab_news = tabs[2]
    tab_blog = tabs[3]
    tab_cafe = tabs[4]
    tab_web = tabs[5]
    tab_encyc = tabs[6]
    tab_kin = tabs[7]
    tab_local_img = tabs[8]
    tab_keywords = tabs[9]
    tab_raw = tabs[10]

    # [TAB 1] 종합 개요
    with tab_overview:
        # Executive PDF 종합 보고서 다운로드 영역
        st.markdown(
            """
            <div class="report-download-banner">
                <div class="report-badge">EXECUTIVE SUMMARY REPORT</div>
                <div class="report-banner-title">📄 네이버 마켓 인텔리전스 종합 분석 보고서 (PDF)</div>
                <div class="report-banner-desc">
                    핵심 KPI 지표 요약, 8개 채널 점유율 순위, 검색어×채널 교차 분석 매트릭스, 시계열 트렌드 차트 및 비즈니스 전략 제언이 포함된 정식 종합 보고서(A4 규격 PDF)를 다운로드합니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_rep_info, col_rep_btn = st.columns([3, 1])
        with col_rep_info:
            st.caption("📌 보고서 포함: 메타 정보 · 4대 핵심 KPI · 채널별 점유율 표 & 시각화 차트 · 교차 피벗 매트릭스 · 트렌드 추이 · 전략적 제언 요약")
        with col_rep_btn:
            try:
                report_gen = PdfReportGenerator()
                report_stats = {
                    "total_buzz": df_summary["total_count"].sum() if not df_summary.empty else 0,
                    "keyword_count": len(keywords),
                    "top_channel": df_summary.groupby("channel_name")["total_count"].sum().idxmax() if not df_summary.empty else "-",
                    "success_rate": 100.0,
                }
                today_str = datetime.now().strftime("%Y%m%d")
                pdf_bytes = report_gen.generate_report(
                    df_summary=df_summary,
                    df_trend=df_trend,
                    keywords=keywords,
                    selected_channels=params.get("selected_channels", []),
                    stats=report_stats,
                )
                st.download_button(
                    label="📥 PDF 종합 보고서 다운로드",
                    data=pdf_bytes,
                    file_name=f"네이버_종합시장분석보고서_{today_str}.pdf",
                    mime="application/pdf",
                    key="tab_overview_download_pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"보고서 생성 오류: {e}")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("### 📢 채널별 버즈량(총 문서 수) 비교")
        col_c1, col_c2 = st.columns([3, 2])
        with col_c1:
            fig_bar = plot_channel_comparison(df_summary)
            st.plotly_chart(fig_bar, use_container_width=True, key="overview_bar_chart")
        with col_c2:
            col_sel1, col_sel2 = st.columns([1, 1])
            with col_sel1:
                share_kw = st.selectbox("기준 검색어", options=["전체"] + keywords, key="overview_share_kw")
            with col_sel2:
                share_view = st.selectbox(
                    "시각화 모드",
                    options=["토스형 프로그레스", "가로 순위 막대", "모던 트리맵"],
                    index=0,
                    key="overview_share_view",
                )

            if share_view == "토스형 프로그레스":
                toss_html = render_channel_share_toss_card(df_summary, selected_kw=share_kw)
                st.html(toss_html)
            elif share_view == "가로 순위 막대":
                fig_bar = plot_channel_share_horizontal_bar(df_summary, selected_kw=share_kw)
                st.plotly_chart(fig_bar, use_container_width=True, key="overview_share_hbar")
            else:
                fig_tree = plot_channel_share_treemap(df_summary, selected_kw=share_kw)
                st.plotly_chart(fig_tree, use_container_width=True, key="overview_treemap_chart")

        st.markdown("### 📋 검색어 x 채널 버즈량 요약 피벗 테이블")
        df_pivot = DataAnalyzer.summarize_channel_buzz(df_summary)
        st.dataframe(
            df_pivot.style.format("{:,.0f}"),
            use_container_width=True,
        )

    # [TAB 2] 데이터랩 트렌드 분석
    with tab_trend:
        st.markdown("### 📈 기간별 상대 관심도(검색 지수) 시계열 추이")
        if not df_trend.empty:
            fig_trend = plot_datalab_trend(df_trend)
            st.plotly_chart(fig_trend, use_container_width=True, key="datalab_trend_chart")

            st.markdown("### 📊 트렌드 통계 지표 요약")
            df_trend_stats = DataAnalyzer.analyze_trend_statistics(df_trend)
            st.dataframe(df_trend_stats, use_container_width=True)
        else:
            st.info("데이터랩 트렌드 데이터가 없습니다. 사이드바에서 기간과 검색어를 확인 후 다시 실행해 주세요.")

    # [TAB 3] 📰 뉴스 심층 EDA
    with tab_news:
        render_channel_eda_tab(df_items, channel_key="news", channel_name="뉴스", channel_icon="📰", keywords=keywords)

    # [TAB 4] 📝 블로그 심층 EDA
    with tab_blog:
        render_channel_eda_tab(df_items, channel_key="blog", channel_name="블로그", channel_icon="📝", keywords=keywords)

    # [TAB 5] ☕ 카페글 심층 EDA
    with tab_cafe:
        render_channel_eda_tab(df_items, channel_key="cafearticle", channel_name="카페글", channel_icon="☕", keywords=keywords)

    # [TAB 6] 🌐 웹문서 심층 EDA
    with tab_web:
        render_channel_eda_tab(df_items, channel_key="webkr", channel_name="웹문서", channel_icon="🌐", keywords=keywords)

    # [TAB 7] 📚 백과사전 심층 EDA
    with tab_encyc:
        render_channel_eda_tab(df_items, channel_key="encyc", channel_name="백과사전", channel_icon="📚", keywords=keywords)

    # [TAB 8] 💡 지식iN 심층 EDA
    with tab_kin:
        render_channel_eda_tab(df_items, channel_key="kin", channel_name="지식iN", channel_icon="💡", keywords=keywords)

    # [TAB 9] 📍 지역 & 🖼️ 이미지 EDA
    with tab_local_img:
        sub_tab_local, sub_tab_img = st.tabs(["📍 지역(플레이스) EDA", "🖼️ 이미지 검색 EDA"])
        with sub_tab_local:
            render_channel_eda_tab(df_items, channel_key="local", channel_name="지역(플레이스)", channel_icon="📍", keywords=keywords)
        with sub_tab_img:
            render_channel_eda_tab(df_items, channel_key="image", channel_name="이미지", channel_icon="🖼️", keywords=keywords)

    # [TAB 3] 키워드 및 형태소 EDA 분석
    with tab_keywords:
        st.markdown("### 🔤 검색 결과 본문 형태소(명사) 빈도 및 워드클라우드")

        col_filter1, col_filter2 = st.columns([2, 3])
        with col_filter1:
            kw_for_nlp = st.selectbox("분석 대상 검색어", options=["전체"] + keywords, key="nlp_target_kw")
        with col_filter2:
            custom_sw_input = st.text_input(
                "추가 불용어 (쉼표 구분)",
                value="",
                placeholder="예: 무료, 사이트, 바로가기",
                help="워드클라우드 및 Top 키워드에서 제외할 단어를 추가할 수 있습니다.",
            )

        custom_stopwords = set([w.strip() for w in custom_sw_input.split(",") if w.strip()])

        # 텍스트 추출
        df_target_texts = df_items.copy() if not df_items.empty else pd.DataFrame(columns=["keyword", "title", "description"])
        if kw_for_nlp != "전체" and not df_target_texts.empty:
            df_target_texts = df_target_texts[df_target_texts["keyword"] == kw_for_nlp]

        if not df_target_texts.empty and "title" in df_target_texts.columns:
            combined_texts = (
                df_target_texts["title"].fillna("").tolist() +
                df_target_texts.get("description", pd.Series(dtype=str)).fillna("").tolist()
            )
        else:
            combined_texts = []

        with st.spinner("형태소 분석 및 연관어 빈도 추출 중..."):
            df_top_nouns = DataAnalyzer.extract_top_nouns(
                texts=combined_texts,
                top_n=30,
                min_len=2,
                custom_stopwords=custom_stopwords,
            )

        col_wc, col_chart = st.columns([1, 1])
        with col_wc:
            st.markdown(f"#### ☁️ [{kw_for_nlp}] 워드클라우드")
            render_wordcloud(df_top_nouns, title=f"{kw_for_nlp} 워드클라우드")
        with col_chart:
            fig_top_bar = plot_top_keywords_bar(df_top_nouns, title=f"[{kw_for_nlp}] 주요 연관어")
            st.plotly_chart(fig_top_bar, use_container_width=True, key="nlp_top_bar_chart")

        with st.expander("📄 Top 30 연관어 빈도 데이터프레임 확인"):
            st.dataframe(df_top_nouns, use_container_width=True)

        # 5. 연관어 동시 출현(Co-occurrence) 네트워크 분석
        st.markdown("---")
        st.markdown(f"#### 🕸️ [{kw_for_nlp}] 연관어 동시 출현(Co-occurrence) 네트워크 분석")
        st.caption("본문 내에서 함께 자주 등장하는 핵심 단어쌍 간의 의미적 연결망 및 중심성 구조를 시각화합니다.")

        with st.spinner("동시 출현 네트워크 및 연결망 구조 분석 중..."):
            network_data, df_edges = DataAnalyzer.build_cooccurrence_network(
                texts=combined_texts,
                top_nodes=25,
                top_edges=40,
                custom_stopwords=custom_stopwords,
            )

        if network_data and "G" in network_data:
            col_net, col_edge_tbl = st.columns([3, 2])
            with col_net:
                fig_net = plot_cooccurrence_network(
                    network_data,
                    title=f"[{kw_for_nlp}] 핵심 연관어 동시 출현 네트워크 맵",
                )
                st.plotly_chart(fig_net, use_container_width=True, key=f"nlp_network_{kw_for_nlp}")
            with col_edge_tbl:
                st.markdown("##### 🔗 상위 동시 출현 단어쌍 랭킹")
                st.caption("함께 가장 빈번하게 등장한 단어 조합 순위")
                st.dataframe(df_edges, use_container_width=True, height=450)
        else:
            st.info("동시 출현 네트워크를 형성하기에 유효한 텍스트 데이터가 부족합니다.")

    # [TAB 4] 채널별 원문 결과 탐색기
    with tab_raw:
        render_data_viewer(df_items)


def render_welcome_screen(has_creds: bool):
    """초기 안내 화면 렌더링 (모던 카드 온보딩 스타일)"""
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); height: 100%;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
                    <span style="font-size: 1.25rem;">✨</span>
                    <span style="font-size: 1.08rem; font-weight: 800; color: #0F172A;">주요 분석 기능 가이드</span>
                </div>
                <div style="font-size: 0.9rem; color: #475569; line-height: 1.8;">
                    <div>🎯 <b>다중 검색어 비교</b>: 쉼표(,) 구분으로 여러 키워드의 시장 반응 동시 비교</div>
                    <div>📡 <b>8대 검색 채널 EDA</b>: 뉴스, 블로그, 카페, 웹, 백과, 지식iN, 지역, 이미지</div>
                    <div>📈 <b>데이터랩 시계열</b>: 기간별 상대 검색량 지수 및 통계 변동성 집계</div>
                    <div>⏰ <b>뉴스 골든타임</b>: 요일 × 시간대(0~23시) 2차원 기사 송고 히트맵</div>
                    <div>🕸️ <b>연관어 네트워크</b>: Kiwi 형태소 기반 단어 동시 출현 관계망 및 워드클라우드</div>
                    <div>📥 <b>원문 및 CSV</b>: 채널별 상세 카드 뷰어 및 UTF-8-SIG CSV 다운로드</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        api_status_text = "🟢 네이버 API 연동 완료 (.env 키 정상 로드)" if has_creds else "⚠️ 네이버 API 키 설정 필요 (.env 확인)"
        api_status_color = "#029443" if has_creds else "#D97706"
        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px; padding: 22px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.03); height: 100%;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 14px;">
                    <span style="font-size: 1.25rem;">🔑</span>
                    <span style="font-size: 1.08rem; font-weight: 800; color: #0F172A;">API 연동 및 시작 안내</span>
                </div>
                <div style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 0.82rem; font-weight: 700; color: {api_status_color}; margin-bottom: 14px;">
                    {api_status_text}
                </div>
                <div style="font-size: 0.9rem; color: #475569; line-height: 1.7;">
                    <div>1. 좌측 사이드바에서 <b>비교할 검색어</b>를 쉼표로 입력하세요.</div>
                    <div>2. 분석 기간과 수집 채널을 확인하세요. (기본 8대 전 채널 선택)</div>
                    <div>3. <b>[🚀 마켓 인사이트 분석 시작]</b> 버튼을 누르면 실시간 수집 및 심층 분석이 시작됩니다.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
