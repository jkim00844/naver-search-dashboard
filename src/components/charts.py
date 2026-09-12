import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# 세련되고 가독성 높은 모던 라이트 컬러 팔레트 (Linear/Toss 테마)
LIGHT_PALETTE = [
    "#02B852",  # Vivid Emerald Green (네이버 포인트)
    "#3B82F6",  # Modern Blue
    "#8B5CF6",  # Bright Violet
    "#F43F5E",  # Vivid Rose
    "#F59E0B",  # Warm Amber
    "#06B6D4",  # Electric Cyan
    "#EC4899",  # Vivid Pink
    "#6366F1",  # Rich Indigo
]

LIGHT_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(248,250,252,0.5)",
    font=dict(color="#1E293B", family="Pretendard, -apple-system, sans-serif", size=12),
    xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", zerolinecolor="#E2E8F0"),
    yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", zerolinecolor="#E2E8F0"),
)


def plot_datalab_trend(df_trend: pd.DataFrame) -> go.Figure:
    """
    데이터랩 트렌드 시계열 라인 차트 (라이트 모드 전용)
    """
    if df_trend.empty:
        fig = go.Figure()
        fig.update_layout(title="트렌드 데이터가 없습니다.", **LIGHT_LAYOUT)
        return fig

    fig = px.line(
        df_trend,
        x="period",
        y="ratio",
        color="keyword",
        markers=True,
        title="<b>📊 검색어별 상대적 관심도(트렌드) 시계열 추이</b>",
        labels={"period": "일자 / 기간", "ratio": "검색 지수 (최대 100 기준 상대값)", "keyword": "검색어"},
        color_discrete_sequence=LIGHT_PALETTE,
    )

    fig.update_layout(
        **LIGHT_LAYOUT,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_traces(line=dict(width=3))
    return fig


def plot_channel_comparison(df_summary: pd.DataFrame) -> go.Figure:
    """
    검색어 및 채널별 총 버즈량(total_count) 비교 그룹 막대 차트
    """
    if df_summary.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    fig = px.bar(
        df_summary,
        x="channel_name",
        y="total_count",
        color="keyword",
        barmode="group",
        title="<b>📢 채널별 버즈량 (포털 내 총 문서 수) 비교</b>",
        labels={"channel_name": "채널", "total_count": "총 문서 수", "keyword": "검색어"},
        color_discrete_sequence=LIGHT_PALETTE,
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1),
    )
    return fig


CHANNEL_UI_META = {
    "웹문서": {"icon": "🌐", "color": "#0284C7", "gradient": "linear-gradient(90deg, #0284C7, #38BDF8)"},
    "블로그": {"icon": "📝", "color": "#03C75A", "gradient": "linear-gradient(90deg, #03C75A, #34D399)"},
    "카페글": {"icon": "☕", "color": "#EA580C", "gradient": "linear-gradient(90deg, #EA580C, #FB923C)"},
    "뉴스": {"icon": "📰", "color": "#2563EB", "gradient": "linear-gradient(90deg, #2563EB, #60A5FA)"},
    "지식iN": {"icon": "💡", "color": "#D97706", "gradient": "linear-gradient(90deg, #D97706, #FBBF24)"},
    "이미지": {"icon": "🖼️", "color": "#7C3AED", "gradient": "linear-gradient(90deg, #7C3AED, #A78BFA)"},
    "지역(플레이스)": {"icon": "📍", "color": "#DC2626", "gradient": "linear-gradient(90deg, #DC2626, #F87171)"},
    "백과사전": {"icon": "📚", "color": "#0D9488", "gradient": "linear-gradient(90deg, #0D9488, #2DD4BF)"},
}


def render_channel_share_toss_card(df_summary: pd.DataFrame, selected_kw: str = "전체") -> str:
    """
    토스/핀테크 스타일의 채널별 점유율 프로그레스 리스트 카드 HTML 생성
    """
    if df_summary.empty:
        return "<div style='padding: 20px; text-align: center; color: #94A3B8;'>수집된 채널 요약 데이터가 없습니다.</div>"

    if selected_kw == "전체":
        data = df_summary.groupby("channel_name", as_index=False)["total_count"].sum()
        title = "전체 검색어 채널 점유율"
    else:
        data = df_summary[df_summary["keyword"] == selected_kw]
        title = f"[{selected_kw}] 채널 점유율"

    data = data[data["total_count"] > 0].copy()
    if data.empty:
        return "<div style='padding: 20px; text-align: center; color: #94A3B8;'>표시할 채널 데이터가 없습니다.</div>"

    total_sum = data["total_count"].sum()
    data["share_pct"] = (data["total_count"] / total_sum * 100).round(1)
    data = data.sort_values(by="total_count", ascending=False).reset_index(drop=True)

    items_html = []
    for rank, row in enumerate(data.itertuples(), start=1):
        ch_name = row.channel_name
        meta = CHANNEL_UI_META.get(ch_name, {"icon": "📌", "color": "#475569", "gradient": "linear-gradient(90deg, #475569, #94A3B8)"})
        icon = meta["icon"]
        color = meta["color"]
        gradient = meta["gradient"]
        count_str = f"{row.total_count:,.0f}건"
        pct_str = f"{row.share_pct:.1f}%"
        if row.total_count >= 10000:
            man_val = row.total_count / 10000
            count_badge = f"{count_str} ({man_val:,.1f}만)"
        else:
            count_badge = count_str

        rank_cls = f"toss-rank-badge rank-{rank}" if rank <= 3 else "toss-rank-badge"

        items_html.append(f"""
        <div class="toss-share-item">
            <div class="toss-item-top">
                <div class="toss-item-left">
                    <span class="{rank_cls}">{rank}</span>
                    <span class="toss-ch-icon">{icon}</span>
                    <span class="toss-ch-name">{ch_name}</span>
                </div>
                <div class="toss-item-right">
                    <span class="toss-count-text">{count_badge}</span>
                    <span class="toss-pct-badge" style="background: {color}18; color: {color}; border: 1px solid {color}35;">{pct_str}</span>
                </div>
            </div>
            <div class="toss-progress-track">
                <div class="toss-progress-bar" style="width: {row.share_pct}%; background: {gradient};"></div>
            </div>
        </div>
        """)

    full_html = f"""
    <div class="toss-share-card">
        <div class="toss-share-header">
            <div class="toss-header-left">
                <span class="toss-header-title">📊 {title}</span>
                <span class="toss-header-sub">실시간 채널별 문서 점유 비율</span>
            </div>
            <div class="toss-header-right">
                <span class="toss-total-pill">총합 {total_sum:,.0f}건</span>
            </div>
        </div>
        <div class="toss-share-list">
            {"".join(items_html)}
        </div>
    </div>
    """
    return full_html


def plot_channel_share_treemap(df_summary: pd.DataFrame, selected_kw: str = "전체") -> go.Figure:
    """
    채널별 버즈량 점유율 트리맵 차트 (모던 화이트 스타일)
    """
    if df_summary.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    if selected_kw == "전체":
        data = df_summary.groupby("channel_name", as_index=False)["total_count"].sum()
        title_text = "<b>🗺️ 전체 검색어 채널 점유율 (트리맵)</b>"
    else:
        data = df_summary[df_summary["keyword"] == selected_kw]
        title_text = f"<b>🗺️ [{selected_kw}] 채널 점유율 (트리맵)</b>"

    data = data[data["total_count"] > 0].copy()
    if data.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    colors = [CHANNEL_UI_META.get(c, {}).get("color", "#02B852") for c in data["channel_name"]]

    fig = go.Figure(
        go.Treemap(
            labels=data["channel_name"],
            parents=[""] * len(data),
            values=data["total_count"],
            textinfo="label+value+percent root",
            marker=dict(
                colors=colors,
                line=dict(width=2, color="#FFFFFF"),
                pad=dict(t=4, b=4, l=4, r=4),
            ),
            hovertemplate="<b>%{label}</b><br>문서 수: %{value:,}건<extra></extra>",
        )
    )
    layout_args = {**LIGHT_LAYOUT, "paper_bgcolor": "#FFFFFF"}
    fig.update_layout(
        title=title_text,
        margin=dict(l=10, r=10, t=50, b=10),
        **layout_args,
    )
    return fig


def plot_channel_share_horizontal_bar(df_summary: pd.DataFrame, selected_kw: str = "전체") -> go.Figure:
    """
    채널별 버즈량 점유율 수평 바 차트 (토스/스트라이프 모던 스타일)
    """
    if df_summary.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    if selected_kw == "전체":
        data = df_summary.groupby("channel_name", as_index=False)["total_count"].sum()
        title_text = "<b>📊 전체 검색어 채널 점유율</b>"
    else:
        data = df_summary[df_summary["keyword"] == selected_kw]
        title_text = f"<b>📊 [{selected_kw}] 채널 점유율</b>"

    data = data[data["total_count"] > 0].sort_values(by="total_count", ascending=True).reset_index(drop=True)
    total_val = data["total_count"].sum()
    data["pct"] = (data["total_count"] / total_val * 100).round(1)
    data["label_text"] = data.apply(lambda r: f"{r['total_count']:,}건 ({r['pct']}%)", axis=1)

    colors = [CHANNEL_UI_META.get(c, {}).get("color", "#3B82F6") for c in data["channel_name"]]

    fig = go.Figure(
        go.Bar(
            x=data["total_count"],
            y=data["channel_name"],
            orientation="h",
            text=data["label_text"],
            textposition="auto",
            marker=dict(
                color=colors,
                line=dict(width=0),
            ),
            hovertemplate="<b>%{y}</b><br>문서 수: %{x:,}건<extra></extra>",
        )
    )

    fig.update_layout(
        title=title_text,
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=30, t=50, b=20),
    )
    fig.update_xaxes(title="총 문서 수 (건)", gridcolor="#F1F5F9", showline=False)
    fig.update_yaxes(title="", showgrid=False)
    return fig


def plot_top_keywords_bar(df_top: pd.DataFrame, title: str = "Top 키워드 빈도") -> go.Figure:
    """
    형태소 추출 단어 빈도수 수평 막대 차트
    """
    if df_top.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    df_sorted = df_top.head(20).sort_values(by="출현빈도", ascending=True)

    fig = px.bar(
        df_sorted,
        x="출현빈도",
        y="단어",
        orientation="h",
        title=f"<b>🔤 {title} Top 20</b>",
        color="출현빈도",
        color_continuous_scale="Tealgrn",
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False,
    )
    return fig


def plot_top_ranking_bar(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    color_col: str = None,
    orientation: str = "h",
    top_n: int = 15,
) -> go.Figure:
    """
    상위 랭킹 막대 차트 (가로 또는 세로)
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    sub_df = df.head(top_n)
    if orientation == "h":
        sub_df = sub_df.sort_values(by=x_col, ascending=True)

    fig = px.bar(
        sub_df,
        x=x_col,
        y=y_col,
        orientation=orientation,
        color=color_col or x_col if orientation == "h" else y_col,
        color_continuous_scale="Tealgrn" if (not color_col and pd.api.types.is_numeric_dtype(sub_df[x_col if orientation == "h" else y_col])) else None,
        color_discrete_sequence=LIGHT_PALETTE if (color_col and not pd.api.types.is_numeric_dtype(sub_df[color_col])) else None,
        title=f"<b>{title}</b>",
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_showscale=False,
    )
    return fig


def plot_time_series_line(
    df: pd.DataFrame,
    date_col: str,
    val_col: str,
    group_col: str = "keyword",
    title: str = "시계열 추이",
) -> go.Figure:
    """
    일자/시간별 시계열 라인 차트
    """
    if df.empty or date_col not in df.columns or val_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    clean_df = df.dropna(subset=[date_col, val_col]).sort_values(by=date_col)
    if clean_df.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    has_group = group_col in clean_df.columns and clean_df[group_col].nunique() > 1
    fig = px.line(
        clean_df,
        x=date_col,
        y=val_col,
        color=group_col if has_group else None,
        markers=True,
        title=f"<b>{title}</b>",
        color_discrete_sequence=LIGHT_PALETTE,
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
    )
    fig.update_traces(line=dict(width=2.5))
    return fig


def plot_distribution_box(
    df: pd.DataFrame,
    y_col: str,
    x_col: str = "keyword",
    title: str = "텍스트 길이 분포 (Box Plot)",
    y_label: str = "글자수",
) -> go.Figure:
    """
    수치형 데이터 분포 박스플롯 (사분위수, 중앙값, 이상치)
    """
    if df.empty or y_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    clean_df = df.dropna(subset=[y_col])
    if clean_df.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    has_x = x_col in clean_df.columns
    fig = px.box(
        clean_df,
        x=x_col if has_x else None,
        y=y_col,
        color=x_col if has_x else None,
        points="all",
        title=f"<b>{title}</b>",
        labels={y_col: y_label, x_col: "검색어"},
        color_discrete_sequence=LIGHT_PALETTE,
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=False,
    )
    return fig


def plot_distribution_histogram(
    df: pd.DataFrame,
    x_col: str,
    group_col: str = "keyword",
    title: str = "도수분포 히스토그램",
    nbins: int = 25,
) -> go.Figure:
    """
    수치형 데이터 도수분포 히스토그램
    """
    if df.empty or x_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    clean_df = df.dropna(subset=[x_col])
    has_group = group_col in clean_df.columns and clean_df[group_col].nunique() > 1

    fig = px.histogram(
        clean_df,
        x=x_col,
        color=group_col if has_group else None,
        barmode="overlay" if has_group else "relative",
        opacity=0.75,
        nbins=nbins,
        title=f"<b>{title}</b>",
        color_discrete_sequence=LIGHT_PALETTE,
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def plot_scatter_correlation(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: str = "keyword",
    title: str = "상관관계 산점도",
    x_label: str = None,
    y_label: str = None,
    hover_name: str = "title",
) -> go.Figure:
    """
    변수 간 상관관계 산점도
    """
    if df.empty or x_col not in df.columns or y_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    clean_df = df.dropna(subset=[x_col, y_col])
    has_group = group_col in clean_df.columns and clean_df[group_col].nunique() > 1
    has_hover = hover_name in clean_df.columns

    fig = px.scatter(
        clean_df,
        x=x_col,
        y=y_col,
        color=group_col if has_group else None,
        hover_name=hover_name if has_hover else None,
        title=f"<b>{title}</b>",
        labels={x_col: x_label or x_col, y_col: y_label or y_col},
        color_discrete_sequence=LIGHT_PALETTE,
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def plot_heatmap_matrix(
    df_matrix: pd.DataFrame,
    title: str = "교차 빈도 히트맵",
    x_label: str = "",
    y_label: str = "",
) -> go.Figure:
    """
    교차표/피봇테이블 2차원 히트맵 시각화
    """
    if df_matrix.empty:
        fig = go.Figure()
        fig.update_layout(**LIGHT_LAYOUT)
        return fig

    plot_df = df_matrix.copy()
    if "합계" in plot_df.index:
        plot_df = plot_df.drop(index="합계")
    if "합계" in plot_df.columns:
        plot_df = plot_df.drop(columns="합계")

    fig = px.imshow(
        plot_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Tealgrn",
        title=f"<b>{title}</b>",
        labels=dict(x=x_label, y=y_label, color="건수"),
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def plot_weekday_hour_heatmap(
    df_news: pd.DataFrame,
    title: str = "📰 뉴스 보도 골든타임 (요일 × 시간대 히트맵)",
) -> go.Figure:
    """
    뉴스 요일(월~일) x 시간대(0~23시) 2차원 골든타임 보도 집중도 히트맵
    """
    if df_news.empty or "pub_weekday" not in df_news.columns or "pub_hour" not in df_news.columns:
        fig = go.Figure()
        fig.update_layout(title="요일/시간대 데이터가 없습니다.", **LIGHT_LAYOUT)
        return fig

    sub_df = df_news.dropna(subset=["pub_weekday", "pub_hour"]).copy()
    if sub_df.empty:
        fig = go.Figure()
        fig.update_layout(title="요일/시간대 데이터가 없습니다.", **LIGHT_LAYOUT)
        return fig

    weekday_order = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    sub_df["pub_hour_str"] = sub_df["pub_hour"].apply(lambda h: f"{int(h):02d}시")
    hour_order = [f"{h:02d}시" for h in range(24)]

    # 2D Crosstab
    matrix = pd.crosstab(sub_df["pub_weekday"], sub_df["pub_hour_str"])
    matrix = matrix.reindex(index=weekday_order, columns=hour_order, fill_value=0)

    fig = px.imshow(
        matrix,
        labels=dict(x="보도 시간대", y="요일", color="기사 수"),
        x=hour_order,
        y=weekday_order,
        color_continuous_scale="Mint",
        aspect="auto",
        title=f"<b>{title}</b>",
        text_auto=True,
    )
    fig.update_layout(
        **LIGHT_LAYOUT,
        margin=dict(l=20, r=20, t=50, b=20),
        coloraxis_colorbar=dict(title="기사 수"),
    )
    return fig


def plot_cooccurrence_network(
    network_data: dict,
    title: str = "🕸️ 연관어 동시 출현(Co-occurrence) 네트워크 맵",
) -> go.Figure:
    """
    Plotly 기반 형태소 연관어 동시 출현 네트워크 그래프
    """
    if not network_data or "G" not in network_data or "pos" not in network_data:
        fig = go.Figure()
        fig.update_layout(title="네트워크 데이터가 없습니다.", **LIGHT_LAYOUT)
        return fig

    G = network_data["G"]
    pos = network_data["pos"]
    word_freq = network_data["word_freq"]

    # 1. 엣지 좌표 생성
    edge_x = []
    edge_y = []
    edge_weights = []
    for edge in G.edges(data=True):
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_weights.append(edge[2].get("weight", 1))

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1.5, color="rgba(148, 163, 184, 0.6)"),
        hoverinfo="none",
        mode="lines",
    )

    # 2. 노드 좌표 및 속성 생성
    node_x = []
    node_y = []
    node_text = []
    node_hover = []
    node_size = []
    node_color = []

    max_freq = max(word_freq.values()) if word_freq else 1
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)

        freq = word_freq.get(node, 1)
        degree = G.degree(node)
        node_hover.append(f"<b>{node}</b><br>출현 빈도: {freq:,}회<br>연결된 연관어: {degree}개")

        # 노드 크기 스케일링 (16 ~ 42)
        size = 16 + (freq / max_freq) * 26
        node_size.append(size)
        node_color.append(degree)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            showscale=True,
            colorscale="Tealgrn",
            color=node_color,
            size=node_size,
            colorbar=dict(
                thickness=12,
                title=dict(text="연결 중심성(Degree)", side="right"),
                xanchor="left",
            ),
            line=dict(width=2, color="#FFFFFF"),
        ),
        textfont=dict(size=12, color="#0F172A", family="sans-serif"),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(text=f"<b>{title}</b>", font=dict(size=16)),
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(248,250,252,0.6)",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=20, r=20, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    return fig


