"""
fetcher.py — async content fetcher for URLs and PDFs.

Public API:
    fetch_all(items: list[Item]) -> list[Item]
"""
from __future__ import annotations

import asyncio
import io
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
import pdfplumber
import trafilatura

from .config import TEXT_CHAR_LIMIT
from .models import FetchStatus, Item, SourceType

TIMEOUT_SEC = 30
USER_AGENT = "Mozilla/5.0 (compatible; MyMDSummerizer/0.1)"
BINARY_CONTENT_TYPES = (
    "image/",
    "audio/",
    "video/",
    "application/octet-stream",
    "application/zip",
    "application/x-tar",
)


# ── Public entry point ─────────────────────────────────────────────────────────

def fetch_all(items: list[Item]) -> list[Item]:
    """Synchronous wrapper around the async fetch pipeline."""
    return asyncio.run(_fetch_all_async(items))


async def _fetch_all_async(items: list[Item]) -> list[Item]:
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(TIMEOUT_SEC),
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        tasks = [_fetch_one(client, item) for item in items]
        return list(await asyncio.gather(*tasks))


# ── Per-item dispatch ──────────────────────────────────────────────────────────

async def _fetch_one(client: httpx.AsyncClient, item: Item) -> Item:
    try:
        if item.source_type == SourceType.PDF:
            return await _fetch_pdf(item)
        return await _fetch_url(client, item)
    except Exception as exc:
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = f"Unexpected error: {exc}"
        return item


# ── URL fetching ───────────────────────────────────────────────────────────────

async def _fetch_url(client: httpx.AsyncClient, item: Item) -> Item:
    url = item.source
    loop = asyncio.get_event_loop()

    # robots.txt check runs in executor because RobotFileParser uses blocking urllib
    try:
        allowed = await loop.run_in_executor(None, _check_robots, url)
    except Exception:
        allowed = True

    if not allowed:
        item.fetch_status = FetchStatus.FAILED_ROBOTS
        item.error_message = f"robots.txt disallows: {url}"
        return item

    if url.lower().endswith(".pdf"):
        return await _fetch_url_pdf(client, item)

    try:
        response = await client.get(url)
    except httpx.TimeoutException:
        item.fetch_status = FetchStatus.FAILED_TIMEOUT
        item.error_message = "Request timed out after 30 seconds"
        return item
    except httpx.RequestError as exc:
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = str(exc)
        return item

    if response.status_code == 403:
        item.fetch_status = FetchStatus.FAILED_403
        item.error_message = "HTTP 403 Forbidden"
        return item
    if response.status_code >= 500:
        item.fetch_status = FetchStatus.FAILED_500
        item.error_message = f"HTTP {response.status_code}"
        return item
    if response.status_code >= 400:
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = f"HTTP {response.status_code}"
        return item

    content_type = response.headers.get("content-type", "").lower()

    if "application/pdf" in content_type or "application/x-pdf" in content_type:
        return _extract_pdf_bytes(response.content, item)

    if any(content_type.startswith(b) for b in BINARY_CONTENT_TYPES):
        item.fetch_status = FetchStatus.FAILED_BINARY
        item.error_message = f"Binary content-type: {content_type}"
        return item

    html = response.text
    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )
    if not extracted:
        extracted = re.sub(r"<[^>]+>", " ", html).strip()

    if not extracted:
        item.fetch_status = FetchStatus.FAILED_BINARY
        item.error_message = "Could not extract text from HTML"
        return item

    return _apply_char_limit(item, extracted, FetchStatus.SUCCESS)


async def _fetch_url_pdf(client: httpx.AsyncClient, item: Item) -> Item:
    try:
        response = await client.get(item.source)
    except httpx.TimeoutException:
        item.fetch_status = FetchStatus.FAILED_TIMEOUT
        item.error_message = "Request timed out after 30 seconds"
        return item
    except httpx.RequestError as exc:
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = str(exc)
        return item

    if response.status_code == 403:
        item.fetch_status = FetchStatus.FAILED_403
        item.error_message = "HTTP 403 Forbidden"
        return item
    if response.status_code >= 500:
        item.fetch_status = FetchStatus.FAILED_500
        item.error_message = f"HTTP {response.status_code}"
        return item
    if response.status_code >= 400:
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = f"HTTP {response.status_code}"
        return item

    return _extract_pdf_bytes(response.content, item)


# ── PDF fetching ───────────────────────────────────────────────────────────────

async def _fetch_pdf(item: Item) -> Item:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _read_local_pdf, item)


def _read_local_pdf(item: Item) -> Item:
    path = Path(item.source)
    if not path.exists():
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = f"File not found: {item.source}"
        return item
    try:
        with open(path, "rb") as f:
            return _extract_pdf_bytes(f.read(), item)
    except Exception as exc:
        item.fetch_status = FetchStatus.FAILED_OTHER
        item.error_message = f"Could not read PDF: {exc}"
        return item


def _extract_pdf_bytes(data: bytes, item: Item) -> Item:
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages_text = [page.extract_text() or "" for page in pdf.pages]
        text = "\n\n".join(pages_text).strip()
    except Exception as exc:
        item.fetch_status = FetchStatus.FAILED_BINARY
        item.error_message = f"PDF extraction failed: {exc}"
        return item

    if not text:
        item.fetch_status = FetchStatus.FAILED_BINARY
        item.error_message = "PDF yielded no extractable text"
        return item

    return _apply_char_limit(item, text, FetchStatus.SUCCESS)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _apply_char_limit(item: Item, text: str, status: FetchStatus) -> Item:
    if len(text) > TEXT_CHAR_LIMIT:
        item.raw_text = text[:TEXT_CHAR_LIMIT]
        item.truncated = True
    else:
        item.raw_text = text
        item.truncated = False
    item.fetch_status = status
    return item


def _check_robots(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        return True
    return rp.can_fetch(USER_AGENT, url)
