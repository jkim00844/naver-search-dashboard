# 📈 네이버 마켓 인사이트 & 검색 EDA 대시보드

네이버 오픈API(검색 8개 채널) 및 데이터랩(통합검색어 트렌드)을 연동하여, 다중 검색어의 시장 반응과 트렌드를 비교·분석하는 Streamlit EDA 대시보드입니다.

---

## 🌟 주요 기능

1. **다중 검색어 비교 분석**
   - 쉼표(`,`)로 구분된 다중 키워드 입력 지원 (예: `생성형AI, 챗GPT, 딥시크`)
   - 키워드별 시장 관심도 및 채널별 점유율을 종합 비교

2. **네이버 8대 채널 전수 수집 및 버즈량 EDA**
   - 📰 **뉴스**: 언론 보도 기사
   - 📝 **블로그**: 네이버 블로그 포스팅
   - ☕ **카페글**: 네이버 카페 게시글
   - 💡 **지식iN**: Q&A 질문 및 답변
   - 🌐 **웹문서**: 국내 웹문서 검색 결과
   - 🖼️ **이미지**: 관련 이미지 및 썸네일 갤러리
   - 📍 **지역(플레이스)**: 매장/장소 위치, 도로명/지번 주소
   - 📚 **백과사전**: 네이버 백과사전 정의 및 표제어

3. **데이터랩 검색어 트렌드 시계열 분석**
   - 지정한 기간(일간/주간/월간) 동안의 상대적 검색 지수(최고 100 기준) 시계열 추이
   - 평균 지수, 최고치 달성일, 최근 지수, 표준편차(변동성) 통계 제공

4. **형태소(Kiwi) 기반 키워드 & 연관어 텍스트 마이닝**
   - Java 설치가 불필요한 초고속 한국어 형태소 분석기(`kiwipiepy`) 내장
   - 본문 텍스트 명사 추출 기반 **워드클라우드** 및 **Top 30 연관어 바 차트**
   - 사용자 지정 불용어(Stopwords) 동적 추가 기능

5. **원문 탐색기 & CSV 다운로드**
   - 수집된 세부 콘텐츠 카드 뷰어 및 원문 링크 연결
   - 수집된 원시 데이터 UTF-8-SIG CSV 다운로드 제공

---

## 📁 프로젝트 구조

파일 종류별/역할별로 모듈화되어 관리됩니다:

```text
naver-search-dashboard/
├── .env.example               # 환경변수 예시 파일
├── .env                      # 네이버 API 키 보관 파일 (git 제외)
├── pyproject.toml            # uv 프로젝트 설정 및 의존성 명세
├── README.md                 # 프로젝트 안내서
├── app.py                    # Streamlit 대시보드 메인 앱
└── src/
    ├── api/                  # 네이버 API 통신 모듈
    │   ├── __init__.py
    │   ├── client.py         # 네이버 검색 & 데이터랩 API 호출 클라이언트
    │   └── endpoints.py      # 엔드포인트 URL 및 8개 채널 메타데이터
    ├── services/             # 비즈니스 로직 및 분석 엔진
    │   ├── __init__.py
    │   ├── collector.py      # 멀티스레드 기반 병렬 데이터 수집기
    │   └── analyzer.py       # 채널 피벗 통계, Kiwi 형태소 분석, 트렌드 집계
    ├── components/           # Streamlit UI 컴포넌트
    │   ├── __init__.py
    │   ├── sidebar.py        # 키워드/기간/API키 설정 패널
    │   ├── metrics_cards.py  # 상단 KPI 지표 카드
    │   ├── charts.py         # Plotly 기반 시계열/도넛/바 차트
    │   ├── wordcloud_view.py # 한글 워드클라우드 시각화
    │   └── data_viewer.py    # 채널별 원문 카드 뷰어 및 CSV 다운로드
    └── utils/                # 유틸리티
        ├── __init__.py
        ├── config.py         # .env 로드 및 API 인증정보 유효성 검사
        └── text_cleaner.py   # 네이버 검색 특수문자 및 태그 정제기
```

---

## 🚀 빠른 시작 가이드 (Quick Start)

### 1. 사전 요구사항
- Python 3.9 이상
- [uv](https://github.com/astral-sh/uv) 패키지 매니저

### 2. 가상환경 및 패키지 설치
`uv`를 통해 의존성을 자동으로 동기화합니다:
```bash
uv sync
```

### 3. 네이버 API 키 발급 및 설정
1. [네이버 개발자센터](https://developers.naver.com/apps/#/register)에서 애플리케이션 등록
2. 사용 API 항목에서 **'검색'** 및 **'데이터랩 (검색어트렌드)'** 권한 추가
3. 프로젝트 루트의 `.env` 파일에 발급받은 키를 입력합니다:
```env
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here
```
*(또는 대시보드 실행 후 좌측 사이드바에서 직접 입력할 수도 있습니다.)*

### 4. 대시보드 서버 실행
```bash
uv run streamlit run app.py
```
실행 후 브라우저에서 `http://localhost:8501`로 접속하시면 대시보드를 바로 사용할 수 있습니다.
