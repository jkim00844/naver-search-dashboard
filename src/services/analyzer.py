from collections import Counter
import logging
from typing import Optional
import pandas as pd

from src.utils.text_cleaner import clean_html_tags, extract_keywords_simple

logger = logging.getLogger(__name__)

# Kiwi 형태소 분석기 지연 로딩
_kiwi_instance = None


def get_kiwi():
    global _kiwi_instance
    if _kiwi_instance is None:
        try:
            from kiwipiepy import Kiwi
            _kiwi_instance = Kiwi()
            logger.info("Kiwi morphological analyzer loaded successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize Kiwi: {e}. Fallback to regex.")
            _kiwi_instance = False
    return _kiwi_instance


DEFAULT_STOPWORDS = {
    "네이버", "검색", "관련", "통해", "대한", "위한", "있는", "있습니다", "하는",
    "경우", "이후", "따라", "모두", "이번", "가장", "위해", "다양한", "이용",
    "제공", "확인", "사용", "정보", "방법", "추천", "소개", "후기", "기반",
    "더", "등", "및", "수", "것", "그", "이", "저", "또", "때", "중", "뿐"
}


class DataAnalyzer:
    """
    수집된 네이버 검색 및 트렌드 데이터에 대한 통계 집계, 형태소 및 텍스트 EDA 서비스
    """

    @staticmethod
    def summarize_channel_buzz(df_summary: pd.DataFrame) -> pd.DataFrame:
        """
        검색어 및 채널별 총 버즈량(total_count) 피벗 및 요약 테이블 생성
        """
        if df_summary.empty:
            return pd.DataFrame()

        pivot_total = df_summary.pivot_table(
            index="keyword",
            columns="channel_name",
            values="total_count",
            aggfunc="sum",
            fill_value=0,
        )
        pivot_total["전체 버즈량"] = pivot_total.sum(axis=1)
        return pivot_total.sort_values(by="전체 버즈량", ascending=False)

    @staticmethod
    def extract_top_nouns(
        texts: list[str],
        top_n: int = 30,
        min_len: int = 2,
        custom_stopwords: Optional[set[str]] = None,
    ) -> pd.DataFrame:
        """
        텍스트 목록에서 Kiwi 형태소 분석기를 이용해 일반명사(NNG), 고유명사(NNP), 영문/알파벳(SL) 추출 및 빈도 계산
        """
        stopwords = set(DEFAULT_STOPWORDS)
        if custom_stopwords:
            stopwords.update(custom_stopwords)

        counter = Counter()
        kiwi = get_kiwi()

        if kiwi:
            # Kiwi 형태소 분석
            for text in texts:
                cleaned = clean_html_tags(text)
                if not cleaned:
                    continue
                try:
                    tokens = kiwi.tokenize(cleaned)
                    for t in tokens:
                        # NNG(일반명사), NNP(고유명사), SL(외래어/알파벳)
                        if t.tag in ("NNG", "NNP", "SL") and len(t.form) >= min_len:
                            form = t.form.strip()
                            if form.lower() not in stopwords and form not in stopwords:
                                counter[form] += 1
                except Exception:
                    # 토큰화 오류 발생 시 폴백
                    for word in extract_keywords_simple(cleaned, min_len=min_len):
                        if word.lower() not in stopwords:
                            counter[word] += 1
        else:
            # 단순 정규식 분리 폴백
            for text in texts:
                cleaned = clean_html_tags(text)
                for word in extract_keywords_simple(cleaned, min_len=min_len):
                    if word.lower() not in stopwords:
                        counter[word] += 1

        top_list = counter.most_common(top_n)
        df_top = pd.DataFrame(top_list, columns=["단어", "출현빈도"])
        return df_top

    @staticmethod
    def analyze_trend_statistics(df_trend: pd.DataFrame) -> pd.DataFrame:
        """
        데이터랩 트렌드 시계열 지표 분석 (평균 지수, 최대 지수, 최대 도달일, 표준편차)
        """
        if df_trend.empty:
            return pd.DataFrame()

        records = []
        for kw, group in df_trend.groupby("keyword"):
            avg_ratio = group["ratio"].mean()
            max_ratio = group["ratio"].max()
            min_ratio = group["ratio"].min()
            std_ratio = group["ratio"].std()

            # 최대값 발생일
            max_row = group.loc[group["ratio"].idxmax()]
            max_date = max_row["period"].strftime("%Y-%m-%d")

            # 최근 지수 (마지막 날짜)
            latest_row = group.sort_values(by="period").iloc[-1]
            latest_ratio = latest_row["ratio"]

            records.append({
                "검색어": kw,
                "평균 검색 지수": round(avg_ratio, 2),
                "최고 지수": round(max_ratio, 2),
                "최고치 발생일": max_date,
                "최근 지수": round(latest_ratio, 2),
                "최저 지수": round(min_ratio, 2),
                "지수 변동성(표준편차)": round(std_ratio, 2) if not pd.isna(std_ratio) else 0.0,
            })

        df_stats = pd.DataFrame(records)
        return df_stats.sort_values(by="평균 검색 지수", ascending=False)

    @staticmethod
    def calculate_descriptive_stats(
        df: pd.DataFrame,
        numeric_cols: list[str],
        group_col: Optional[str] = "keyword",
    ) -> pd.DataFrame:
        """
        수치형 컬럼들의 기술통계 요약표 계산 (Count, Mean, Std, Min, 25%, Median, 75%, Max, Skewness)
        """
        if df.empty:
            return pd.DataFrame()

        valid_cols = [c for c in numeric_cols if c in df.columns]
        if not valid_cols:
            return pd.DataFrame()

        rows = []
        if group_col and group_col in df.columns:
            for grp_val, sub_df in df.groupby(group_col):
                for col in valid_cols:
                    s = pd.to_numeric(sub_df[col], errors="coerce").dropna()
                    if s.empty:
                        continue
                    rows.append({
                        "구분": str(grp_val),
                        "분석 지표": col,
                        "표본수(N)": int(s.count()),
                        "평균(Mean)": round(float(s.mean()), 2),
                        "표준편차(Std)": round(float(s.std()), 2) if s.count() > 1 else 0.0,
                        "최솟값(Min)": round(float(s.min()), 2),
                        "제1사분위(Q1)": round(float(s.quantile(0.25)), 2),
                        "중앙값(Median)": round(float(s.median()), 2),
                        "제3사분위(Q3)": round(float(s.quantile(0.75)), 2),
                        "최댓값(Max)": round(float(s.max()), 2),
                        "왜도(Skewness)": round(float(s.skew()), 2) if s.count() > 2 else 0.0,
                    })
        else:
            for col in valid_cols:
                s = pd.to_numeric(df[col], errors="coerce").dropna()
                if s.empty:
                    continue
                rows.append({
                    "구분": "전체",
                    "분석 지표": col,
                    "표본수(N)": int(s.count()),
                    "평균(Mean)": round(float(s.mean()), 2),
                    "표준편차(Std)": round(float(s.std()), 2) if s.count() > 1 else 0.0,
                    "최솟값(Min)": round(float(s.min()), 2),
                    "제1사분위(Q1)": round(float(s.quantile(0.25)), 2),
                    "중앙값(Median)": round(float(s.median()), 2),
                    "제3사분위(Q3)": round(float(s.quantile(0.75)), 2),
                    "최댓값(Max)": round(float(s.max()), 2),
                    "왜도(Skewness)": round(float(s.skew()), 2) if s.count() > 2 else 0.0,
                })

        return pd.DataFrame(rows)

    @staticmethod
    def create_crosstab(
        df: pd.DataFrame,
        index_col: str,
        column_col: str,
        normalize: bool = False,
    ) -> pd.DataFrame:
        """
        범주형 변수 간의 교차표(Cross-tabulation) 생성 (행/열 합계 포함)
        """
        if df.empty or index_col not in df.columns or column_col not in df.columns:
            return pd.DataFrame()

        clean_df = df.dropna(subset=[index_col, column_col])
        if clean_df.empty:
            return pd.DataFrame()

        try:
            if normalize:
                ct = pd.crosstab(
                    clean_df[index_col],
                    clean_df[column_col],
                    normalize="index",
                    margins=True,
                    margins_name="전체 비율",
                ) * 100
                ct = ct.round(2)
            else:
                ct = pd.crosstab(
                    clean_df[index_col],
                    clean_df[column_col],
                    margins=True,
                    margins_name="합계",
                )
            return ct
        except Exception:
            return pd.DataFrame()

    @staticmethod
    def create_frequency_distribution(
        df: pd.DataFrame,
        col: str,
        bins: Optional[list[float]] = None,
        labels: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        수치형 데이터의 도수분포표 생성 (구간, 도수, 상대도수(%), 누적도수, 누적상대도수(%))
        """
        if df.empty or col not in df.columns:
            return pd.DataFrame()

        series = pd.to_numeric(df[col], errors="coerce").dropna()
        if series.empty:
            return pd.DataFrame()

        if bins is None:
            min_val = float(series.min())
            max_val = float(series.max())
            if min_val == max_val:
                bins = [min_val - 1, min_val + 1]
                cuts = pd.cut(series, bins=bins, include_lowest=True)
            else:
                cuts = pd.cut(series, bins=5, include_lowest=True)
        else:
            cuts = pd.cut(series, bins=bins, labels=labels, include_lowest=True)

        counts = cuts.value_counts(sort=False)

        total_n = len(series)
        freq_df = pd.DataFrame({
            "구간": [f"{iv.left:.0f} ~ {iv.right:.0f}" if hasattr(iv, "left") else str(iv) for iv in counts.index],
            "도수(빈도)": counts.values,
        })
        freq_df["상대도수(%)"] = (freq_df["도수(빈도)"] / total_n * 100).round(2)
        freq_df["누적도수"] = freq_df["도수(빈도)"].cumsum()
        freq_df["누적상대도수(%)"] = freq_df["상대도수(%)"].cumsum().round(2)

        return freq_df

    @staticmethod
    def summarize_top_entities(
        df: pd.DataFrame,
        entity_col: str,
        top_n: int = 15,
        length_col: str = "desc_len",
    ) -> pd.DataFrame:
        """
        상위 출처/작성자/도메인별 종합 랭킹 및 기술 지표 요약표
        """
        if df.empty or entity_col not in df.columns:
            return pd.DataFrame()

        sub_df = df[df[entity_col].notna()]
        sub_df = sub_df[sub_df[entity_col].astype(str).str.strip() != ""]
        if sub_df.empty:
            return pd.DataFrame()

        records = []
        total_items = len(sub_df)
        top_items = sub_df[entity_col].value_counts().head(top_n)

        for rank, (name, count) in enumerate(top_items.items(), 1):
            entity_data = sub_df[sub_df[entity_col] == name]
            kws = list(entity_data["keyword"].unique())
            avg_len = entity_data[length_col].mean() if length_col in entity_data.columns else 0.0

            records.append({
                "순위": rank,
                "출처/작성자": name,
                "게시물 수": count,
                "점유 비중(%)": round(count / total_items * 100, 2),
                "평균 본문 글자수": round(avg_len, 1),
                "다룬 검색어 수": len(kws),
                "관련 검색어": ", ".join(kws[:3]),
            })

        return pd.DataFrame(records)

    @staticmethod
    def build_cooccurrence_network(
        texts: list[str],
        top_nodes: int = 25,
        top_edges: int = 40,
        min_cooc: int = 2,
        custom_stopwords: Optional[set[str]] = None,
    ) -> tuple[dict, pd.DataFrame]:
        """
        문서 목록에서 명사 동시 출현(Co-occurrence) 네트워크 데이터 및 엣지 랭킹표 생성
        :return: (네트워크 시각화 데이터 딕셔너리, 상위 동시출현 단어쌍 DataFrame)
        """
        import itertools
        import networkx as nx

        stopwords = set(DEFAULT_STOPWORDS)
        if custom_stopwords:
            stopwords.update(custom_stopwords)

        kiwi = get_kiwi()
        doc_tokens = []
        word_freq = Counter()

        for text in texts:
            cleaned = clean_html_tags(text)
            if not cleaned:
                continue
            nouns = []
            if kiwi:
                try:
                    tokens = kiwi.tokenize(cleaned)
                    for t in tokens:
                        if t.tag in ("NNG", "NNP", "SL") and len(t.form) >= 2:
                            form = t.form.strip()
                            if form.lower() not in stopwords and form not in stopwords:
                                nouns.append(form)
                except Exception:
                    nouns = [w for w in extract_keywords_simple(cleaned, min_len=2) if w.lower() not in stopwords]
            else:
                nouns = [w for w in extract_keywords_simple(cleaned, min_len=2) if w.lower() not in stopwords]

            unique_nouns = list(dict.fromkeys(nouns))
            if len(unique_nouns) >= 2:
                doc_tokens.append(unique_nouns)
                for w in unique_nouns:
                    word_freq[w] += 1

        if not doc_tokens:
            return {}, pd.DataFrame()

        # 상위 노드 선정
        top_words = set([w for w, _ in word_freq.most_common(top_nodes)])

        # 동시 출현 단어쌍 카운트
        edge_counter = Counter()
        for doc in doc_tokens:
            filtered = [w for w in doc if w in top_words]
            if len(filtered) >= 2:
                for w1, w2 in itertools.combinations(sorted(filtered), 2):
                    edge_counter[(w1, w2)] += 1

        if not edge_counter:
            return {}, pd.DataFrame()

        # 상위 엣지 선정
        most_common_edges = [
            (pair, count) for pair, count in edge_counter.most_common(top_edges) if count >= min_cooc
        ]
        if not most_common_edges:
            most_common_edges = edge_counter.most_common(top_edges)

        # NetworkX 그래프 구축
        G = nx.Graph()
        for (w1, w2), weight in most_common_edges:
            G.add_edge(w1, w2, weight=weight)

        # 고립 노드 방지: 엣지에 참여한 노드들만
        active_nodes = list(G.nodes())
        if not active_nodes:
            return {}, pd.DataFrame()

        # Spring Layout 2D 좌표 계산
        try:
            pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)
        except Exception:
            pos = nx.circular_layout(G)

        # 엣지 랭킹 데이터프레임
        edge_records = []
        for rank, ((w1, w2), count) in enumerate(most_common_edges, 1):
            edge_records.append({
                "순위": rank,
                "단어 1": w1,
                "단어 2": w2,
                "동시 출현 빈도": count,
                "단어 1 총 빈도": word_freq[w1],
                "단어 2 총 빈도": word_freq[w2],
            })
        df_edges = pd.DataFrame(edge_records)

        network_data = {
            "G": G,
            "pos": pos,
            "word_freq": word_freq,
            "edges": most_common_edges,
        }

        return network_data, df_edges

