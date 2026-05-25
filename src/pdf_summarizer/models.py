from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class SourceType(Enum):
    URL = "url"
    PDF = "pdf"


class FetchStatus(Enum):
    SUCCESS = "success"
    FAILED_403 = "failed_403"
    FAILED_500 = "failed_500"
    FAILED_ROBOTS = "failed_robots"
    FAILED_BINARY = "failed_binary"
    FAILED_TIMEOUT = "failed_timeout"
    FAILED_OTHER = "failed_other"


class SummaryStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Item:
    id: str
    source_type: SourceType
    source: str
    fetch_status: FetchStatus | None = None
    raw_text: str | None = None
    truncated: bool = False
    summary_status: SummaryStatus | None = None
    title: str | None = None
    summary: str | None = None
    tags: list[str] = field(default_factory=list)
    output_path: Path | None = None
    error_message: str | None = None
