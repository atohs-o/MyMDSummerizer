from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION: str = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gemini-flash")
DEFAULT_OUTPUT_DIR: Path = Path(os.getenv("DEFAULT_OUTPUT_DIR", "output/notes"))
TEXT_CHAR_LIMIT: int = int(os.getenv("TEXT_CHAR_LIMIT", "30000"))
BATCH_POLL_INTERVAL_SEC: int = int(os.getenv("BATCH_POLL_INTERVAL_SEC", "60"))

MODELS: dict[str, dict[str, str]] = {
    "gemini-2.5-flash": {"provider": "google", "model_id": "gemini-2.5-flash"},
    "gemini-2.5-flash-lite": {"provider": "google", "model_id": "gemini-2.5-flash-lite"},
    "claude-sonnet": {"provider": "anthropic", "model_id": "claude-sonnet-4-6"},
    "claude-haiku": {"provider": "anthropic", "model_id": "claude-haiku-4-5-20251001"},
}

# src/pdf_summarizer/ の3階層上 = リポジトリルート
PROMPTS_DIR: Path = Path(__file__).parent.parent.parent / "prompts"
