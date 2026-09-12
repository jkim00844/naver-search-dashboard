import io
import os
from datetime import datetime
from typing import Optional, Union

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _resolve_korean_font() -> tuple[str, Optional[str]]:
    """macOS 및 시스템의 한국어 TTF 폰트 경로 탐색 및 ReportLab 등록"""
    candidates = [
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/Library/Fonts/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/NanumGothic.ttf",
        "/Library/Fonts/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
        "/usr/share/fonts/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    selected_path = None
    for p in candidates:
        if os.path.exists(p):
            selected_path = p
            break

    if not selected_path:
        for f in fm.fontManager.ttflist:
            if any(k in f.name.lower() for k in ["applegothic", "nanum", "malgun", "gothic"]):
                if f.fname.endswith(".ttf"):
                    selected_path = f.fname
                    break

    font_name = "KoreanFont"
    if selected_path:
        try:
            pdfmetrics.registerFont(TTFont(font_name, selected_path))
            return font_name, selected_path
        except Exception:
            pass

    return "Helvetica", None


class NumberedCanvas:
    """PDF 하단에 페이지 번호 및 저작권 헤더를 기록하는 캔버스 헬퍼"""

    def __init__(self, *args, **kwargs):
        pass


class PdfReportGenerator:
    """
    네이버 검색 및 트렌드 분석 종합 결과를
    비즈니스 보고서(Executive PDF Report) 규격으로 생성하는 서비스
    """

    def __init__(self):
        self.font_name, self.font_path = _resolve_korean_font()
        if self.font_path:
            if "AppleGothic" in self.font_path:
                plt.rcParams["font.family"] = "AppleGothic"
            elif "Nanum" in self.font_path:
                plt.rcParams["font.family"] = "NanumGothic"
            else:
                plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["axes.unicode_minus"] = False

    def generate_report(
        self,
        df_summary: pd.DataFrame,
        df_trend: Optional[pd.DataFrame] = None,
        keywords: Optional[list[str]] = None,
        selected_channels: Optional[list[str]] = None,
        stats: Optional[dict] = None,
    ) -> bytes:
        """
        종합 분석 데이터를 바탕으로 A4 PDF 바이너리 바이트 생성
        """
        keywords = keywords or []
        selected_channels = selected_channels or []
        stats = stats or {}

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        fn = self.font_name

        # 타이포그래피 스타일 정의
        title_style = ParagraphStyle(
            "DocTitle",
            fontName=fn,
            fontSize=20,
            leading=25,
            textColor=colors.HexColor("#0F172A"),
            fontweight="bold",
            spaceAfter=3,
        )
        sub_style = ParagraphStyle(
            "DocSub",
            fontName=fn,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=12,
        )
        sec_title_style = ParagraphStyle(
            "SecTitle",
            fontName=fn,
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0F172A"),
            fontweight="bold",
            spaceBefore=14,
            spaceAfter=8,
        )
        body_style = ParagraphStyle(
            "DocBody",
            fontName=fn,
            fontSize=8.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        table_cell = ParagraphStyle(
            "TableCell",
            fontName=fn,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1E293B"),
        )
        table_cell_center = ParagraphStyle(
            "TableCellCenter",
            fontName=fn,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1E293B"),
            alignment=1,
        )
        table_cell_bold = ParagraphStyle(
            "TableCellBold",
            fontName=fn,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#0F172A"),
            fontweight="bold",
        )
        table_head = ParagraphStyle(
            "TableHead",
            fontName=fn,
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#FFFFFF"),
            alignment=1,
            fontweight="bold",
        )
        kpi_title = ParagraphStyle(
            "KPITitle",
            fontName=fn,
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#64748B"),
            alignment=1,
        )
        kpi_val = ParagraphStyle(
            "KPIVal",
            fontName=fn,
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#02B852"),
            alignment=1,
            fontweight="bold",
        )

        story = []

        # ==========================================
        # 1. 헤더 및 문서 메타 정보
        # ==========================================
        now_str = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
        kw_display = ", ".join(keywords) if keywords else "전체"

        story.append(Paragraph("📊 NAVER 멀티 채널 시장 분석 종합 리포트", title_style))
        story.append(
            Paragraph(
                f"<b>발행 일시:</b> {now_str} &nbsp;&nbsp;|&nbsp;&nbsp; <b>분석 대상:</b> [{kw_display}] &nbsp;&nbsp;|&nbsp;&nbsp; <b>출처:</b> NAVER Search API & DataLab",
                sub_style,
            )
        )
        story.append(
            HRFlowable(
                width="100%",
                thickness=1.5,
                color=colors.HexColor("#02B852"),
                spaceBefore=0,
                spaceAfter=12,
            )
        )

        # ==========================================
        # 2. 핵심 KPI 메트릭 카드 블록
        # ==========================================
        total_buzz = stats.get("total_buzz", 0)
        kw_count = stats.get("keyword_count", len(keywords))
        top_ch = stats.get("top_channel", "-")
        success_rate = stats.get("success_rate", 100.0)

        # 1만 단위 환산 텍스트
        if total_buzz >= 10000:
            buzz_text = f"{total_buzz / 10000:,.1f}만 건"
        else:
            buzz_text = f"{total_buzz:,.0f}건"

        kpi_data = [
            [
                Paragraph("🎯 분석 키워드 수", kpi_title),
                Paragraph("📥 총 포털 버즈량", kpi_title),
                Paragraph("🔥 1위 점유 채널", kpi_title),
                Paragraph("📈 수집 성공률", kpi_title),
            ],
            [
                Paragraph(f"{kw_count}개", kpi_val),
                Paragraph(buzz_text, kpi_val),
                Paragraph(str(top_ch), kpi_val),
                Paragraph(f"{success_rate:.1f}%", kpi_val),
            ],
        ]

        t_kpi = Table(kpi_data, colWidths=[130, 130, 130, 133])
        t_kpi.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
        )
        story.append(t_kpi)
        story.append(Spacer(1, 14))

        # ==========================================
        # 3. 채널별 점유율 현황 및 통계 테이블
        # ==========================================
        story.append(Paragraph("1. 채널별 버즈량 및 점유율 순위 현황", sec_title_style))

        if not df_summary.empty:
            df_ch = df_summary.groupby("channel_name", as_index=False)["total_count"].sum()
            df_ch = df_ch[df_ch["total_count"] > 0].sort_values(by="total_count", ascending=False).reset_index(drop=True)
            sum_val = df_ch["total_count"].sum() if not df_ch.empty else 1
            df_ch["share_pct"] = (df_ch["total_count"] / sum_val * 100).round(1)

            # 표 헤더
            table_rows = [
                [
                    Paragraph("순위", table_head),
                    Paragraph("검색 채널명", table_head),
                    Paragraph("총 문서 수(버즈량)", table_head),
                    Paragraph("점유율(%)", table_head),
                    Paragraph("채널 특성 및 비중 요약", table_head),
                ]
            ]

            for rank, r in enumerate(df_ch.itertuples(), start=1):
                pct_str = f"{r.share_pct:.1f}%"
                cnt_str = f"{r.total_count:,.0f}건"
                if r.total_count >= 10000:
                    cnt_str += f" ({r.total_count / 10000:,.1f}만)"

                desc = "핵심 점유 채널" if rank == 1 else ("주요 유통 채널" if rank <= 3 else "보조 참고 채널")

                table_rows.append(
                    [
                        Paragraph(str(rank), table_cell_center),
                        Paragraph(f"<b>{r.channel_name}</b>", table_cell),
                        Paragraph(cnt_str, table_cell_center),
                        Paragraph(f"<b>{pct_str}</b>", table_cell_center),
                        Paragraph(desc, table_cell),
                    ]
                )

            t_ch = Table(table_rows, colWidths=[40, 110, 140, 90, 143])
            t_ch.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
                    ]
                )
            )
            story.append(t_ch)
            story.append(Spacer(1, 12))

            # 채널 점유율 수평 바 차트 생성 및 삽입
            chart_img = self._create_channel_bar_chart(df_ch)
            if chart_img:
                story.append(chart_img)
                story.append(Spacer(1, 14))

        # ==========================================
        # 4. 검색어 × 채널 버즈량 교차 피벗 분석
        # ==========================================
        story.append(Paragraph("2. 검색어 × 채널별 버즈량 요약 매트릭스", sec_title_style))

        if not df_summary.empty:
            df_pivot = df_summary.pivot_table(
                index="channel_name",
                columns="keyword",
                values="total_count",
                aggfunc="sum",
                fill_value=0,
            )
            df_pivot["합계"] = df_pivot.sum(axis=1)
            df_pivot = df_pivot.sort_values(by="합계", ascending=False)

            p_cols = ["채널명"] + [str(c) for c in df_pivot.columns]
            p_head = [Paragraph(f"<b>{c}</b>", table_head) for c in p_cols]
            p_rows = [p_head]

            col_w = 523 / max(len(p_cols), 1)
            col_widths = [max(col_w, 80)] + [col_w] * (len(p_cols) - 1)

            for idx, r in df_pivot.iterrows():
                row_cells = [Paragraph(f"<b>{idx}</b>", table_cell)]
                for val in r:
                    row_cells.append(Paragraph(f"{val:,.0f}", table_cell_center))
                p_rows.append(row_cells)

            t_pivot = Table(p_rows, colWidths=col_widths)
            t_pivot.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("TOPPADDING", (0, 0), (-1, -1), 4.5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFFFFF"), colors.HexColor("#F8FAFC")]),
                    ]
                )
            )
            story.append(t_pivot)
            story.append(Spacer(1, 14))

        # ==========================================
        # 5. 검색 트렌드 추이 요약 (데이터랩 데이터가 있는 경우)
        # ==========================================
        if df_trend is not None and not df_trend.empty:
            story.append(Paragraph("3. NAVER 데이터랩 시계열 트렌드 추이", sec_title_style))
            trend_chart_img = self._create_trend_line_chart(df_trend)
            if trend_chart_img:
                story.append(trend_chart_img)
                story.append(Spacer(1, 14))

        # ==========================================
        # 6. 데이터 기반 핵심 분석 인사이트 & 제언
        # ==========================================
        story.append(Paragraph("4. 데이터 종합 인사이트 및 전략적 제언", sec_title_style))

        insights_text = self._generate_insights_narrative(df_summary, df_trend, keywords)
        t_insight = Table(
            [[Paragraph(insights_text, body_style)]],
            colWidths=[523],
        )
        t_insight.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ]
            )
        )
        story.append(t_insight)

        # 문서 빌드
        doc.build(story)
        return buf.getvalue()

    def _create_channel_bar_chart(self, df_ch: pd.DataFrame) -> Optional[Image]:
        """채널별 버즈량 수평 막대 차트 이미지 생성"""
        try:
            plot_df = df_ch.head(8).sort_values(by="total_count", ascending=True)

            fig, ax = plt.subplots(figsize=(7.2, 2.8), dpi=180)
            bars = ax.barh(
                plot_df["channel_name"],
                plot_df["total_count"],
                color="#02B852",
                height=0.6,
                edgecolor="none",
            )

            # 최고값 하이라이트
            if len(bars) > 0:
                bars[-1].set_color("#059669")

            # 데이터 라벨 (천/만 단위)
            max_val = plot_df["total_count"].max() if not plot_df.empty else 1
            for bar in bars:
                w = bar.get_width()
                label = f" {w:,.0f}건 ({w / df_ch['total_count'].sum() * 100:.1f}%)"
                ax.text(w + max_val * 0.01, bar.get_y() + bar.get_height() / 2, label, va="center", fontsize=7.5, color="#334155")

            ax.set_xlim(0, max_val * 1.35)
            ax.set_title("채널별 문서 버즈량 비교 (Top Channels)", fontsize=9.5, fontweight="bold", pad=8, color="#0F172A")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#CBD5E1")
            ax.spines["bottom"].set_color("#CBD5E1")
            ax.tick_params(axis="both", labelsize=8, colors="#475569")
            ax.xaxis.grid(True, linestyle="--", alpha=0.4, color="#E2E8F0")

            fig.tight_layout()

            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", bbox_inches="tight", transparent=False, facecolor="#FFFFFF")
            plt.close(fig)
            img_buf.seek(0)

            return Image(img_buf, width=520, height=200)
        except Exception:
            return None

    def _create_trend_line_chart(self, df_trend: pd.DataFrame) -> Optional[Image]:
        """데이터랩 검색 트렌드 시계열 라인 차트 생성"""
        try:
            fig, ax = plt.subplots(figsize=(7.2, 2.5), dpi=180)
            palette = ["#02B852", "#2563EB", "#7C3AED", "#D97706", "#EC4899"]

            keywords = df_trend["keyword"].unique()
            for idx, kw in enumerate(keywords):
                kw_df = df_trend[df_trend["keyword"] == kw].sort_values("period")
                color = palette[idx % len(palette)]
                ax.plot(
                    kw_df["period"],
                    kw_df["ratio"],
                    label=kw,
                    color=color,
                    linewidth=1.8,
                    marker="o",
                    markersize=3,
                )

            ax.set_title("기간별 상대 관심도(트렌드 지수) 시계열 추이", fontsize=9.5, fontweight="bold", pad=8, color="#0F172A")
            ax.set_ylabel("상대 검색 지수 (0~100)", fontsize=7.5, color="#64748B")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_color("#CBD5E1")
            ax.spines["bottom"].set_color("#CBD5E1")
            ax.tick_params(axis="both", labelsize=7, colors="#475569")
            ax.grid(True, linestyle="--", alpha=0.4, color="#E2E8F0")

            # X축 눈금 간격 정리
            if len(df_trend) > 10:
                ax.xaxis.set_major_locator(plt.MaxNLocator(8))
            plt.xticks(rotation=20)
            ax.legend(frameon=True, fontsize=7.5, loc="upper right")

            fig.tight_layout()

            img_buf = io.BytesIO()
            fig.savefig(img_buf, format="png", bbox_inches="tight", transparent=False, facecolor="#FFFFFF")
            plt.close(fig)
            img_buf.seek(0)

            return Image(img_buf, width=520, height=180)
        except Exception:
            return None

    def _generate_insights_narrative(
        self,
        df_summary: pd.DataFrame,
        df_trend: Optional[pd.DataFrame],
        keywords: list[str],
    ) -> str:
        """데이터를 기반으로 실무 비즈니스 인사이트 텍스트 자동 도출"""
        paragraphs = []

        if not df_summary.empty:
            df_ch = df_summary.groupby("channel_name", as_index=False)["total_count"].sum()
            df_ch = df_ch.sort_values(by="total_count", ascending=False).reset_index(drop=True)
            top_ch = df_ch.iloc[0]["channel_name"]
            top_cnt = df_ch.iloc[0]["total_count"]
            total_sum = df_ch["total_count"].sum()
            top_pct = (top_cnt / total_sum * 100) if total_sum > 0 else 0

            paragraphs.append(
                f"• <b>채널 집중도 분석:</b> 수집된 총 {total_sum:,.0f}건의 포털 문서 중 <b>'{top_ch}'</b> 채널이 "
                f"약 <b>{top_pct:.1f}%</b>({top_cnt:,.0f}건)로 압도적인 1위 점유율을 기록하고 있습니다. "
                f"이는 타겟 유저들이 해당 주제에 대해 가장 많이 정보를 탐색하고 소비하는 핵심 접점이 '{top_ch}'임을 시사합니다."
            )

            # 2위 채널 비교
            if len(df_ch) > 1:
                sec_ch = df_ch.iloc[1]["channel_name"]
                sec_pct = (df_ch.iloc[1]["total_count"] / total_sum * 100) if total_sum > 0 else 0
                paragraphs.append(
                    f"• <b>서브 채널 기회 요인:</b> 2위 채널인 <b>'{sec_ch}'</b>({sec_pct:.1f}%) 역시 유의미한 볼륨을 확보하고 있어, "
                    f"메인 채널인 '{top_ch}'과 연계한 크로스 채널 바이럴 마케팅 전략이 효과적입니다."
                )

        if df_trend is not None and not df_trend.empty:
            # 트렌드 평균 최고 키워드
            avg_trend = df_trend.groupby("keyword")["ratio"].mean().sort_values(ascending=False)
            top_kw = avg_trend.index[0]
            top_kw_score = avg_trend.iloc[0]
            paragraphs.append(
                f"• <b>검색 관심도(트렌드) 분석:</b> 분석 기간 동안 <b>'{top_kw}'</b> 검색어가 평균 관심도 지수 "
                f"<b>{top_kw_score:.1f}점</b>을 기록하여 가장 지속적인 유저 검색 수요를 유지한 것으로 나타났습니다."
            )

        paragraphs.append(
            "• <b>실행 제언:</b> 버즈량이 집중된 상위 채널에 대한 SEO 최적화 및 고품질 콘텐츠 배포를 우선순위로 두고, "
            "상대적으로 경쟁 강도가 낮은 롱테일 채널을 통한 틈새 키워드 선점 전략을 병행할 것을 권장합니다."
        )

        return "<br/><br/>".join(paragraphs)
