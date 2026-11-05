"""CLI 전용 환경 로드. 저장소 루트 `.env`의 AWS 자격 증명을 읽는다.

서버(`server.py`)는 이 모듈을 import하지 않는다(design.md 8.5).
"""

from dotenv import load_dotenv

from quiz.db import REPO_ROOT


def load_cli_env() -> None:
    load_dotenv(REPO_ROOT / ".env", override=False)
