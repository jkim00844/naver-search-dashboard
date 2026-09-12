import os
import platform
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from wordcloud import WordCloud


def get_korean_font_path() -> str:
    """
    OS별 한글 폰트 경로 자동 탐색 (Mac, Linux, Windows)
    """
    bundled_font = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "NanumGothic.ttf")
    if os.path.exists(bundled_font):
        return bundled_font

    system = platform.system()
    candidates = []
    if system == "Darwin":  # Mac
        candidates = [
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        ]
    elif system == "Windows":
        candidates = [
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/gulim.ttc",
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return ""


def render_wordcloud(df_top: pd.DataFrame, title: str = "워드클라우드"):
    """
    단어 빈도 데이터프레임으로부터 라이트 모드 최적화 워드클라우드 생성 및 렌더링
    """
    if df_top.empty:
        st.info("워드클라우드를 생성할 단어 데이터가 없습니다.")
        return

    word_freq = dict(zip(df_top["단어"], df_top["출현빈도"]))
    font_path = get_korean_font_path()

    wc_params = {
        "width": 800,
        "height": 450,
        "background_color": "white",
        "colormap": "tab10",
        "max_words": 150,
        "random_state": 42,
    }
    if font_path:
        wc_params["font_path"] = font_path

    try:
        wc = WordCloud(**wc_params).generate_from_frequencies(word_freq)

        fig, ax = plt.subplots(figsize=(10, 5.5), facecolor="white")
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        plt.tight_layout(pad=0)
        st.pyplot(fig)
        plt.close(fig)
    except Exception as e:
        st.warning(f"워드클라우드 생성 중 오류 발생: {e}")
