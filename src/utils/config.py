import os
from pathlib import Path
from dotenv import load_dotenv

# 루트 경로 탐색 및 .env 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)


def get_naver_credentials(
    override_client_id: str = "",
    override_client_secret: str = ""
) -> tuple[str, str]:
    """
    네이버 API Client ID와 Secret을 반환합니다.
    항상 최신 .env 파일 내용을 반영(override=True)합니다.
    우선순위: UI 직접 입력값 > 최신 .env/시스템 환경변수
    """
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)

    client_id = (override_client_id or os.getenv("NAVER_CLIENT_ID", "")).strip()
    client_secret = (override_client_secret or os.getenv("NAVER_CLIENT_SECRET", "")).strip()
    return client_id, client_secret


def is_valid_credentials(client_id: str, client_secret: str) -> bool:
    """API 키의 기본 유효성(공백 및 기본값 여부)을 점검합니다."""
    if not client_id or not client_secret:
        return False
    if "your_" in client_id.lower() or "your_" in client_secret.lower():
        return False
    return len(client_id) > 5 and len(client_secret) > 5
