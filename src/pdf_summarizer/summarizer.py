"""
summarizer.py — LLM summarization via Google Gemini.

Public API:
    summarize_all(items, model_key="gemini-flash") -> list[Item]
    summarize_one(item, model_key="gemini-flash") -> Item
"""
from __future__ import annotations

import json
import re

from google import genai
from google.genai import types as genai_types

from .config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT, MODELS, PROMPTS_DIR
from .models import FetchStatus, Item, SummaryStatus


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_prompt() -> str:
    return (PROMPTS_DIR / "summarize.txt").read_text(encoding="utf-8")


def _make_client() -> genai.Client:
    return genai.Client(
        vertexai=True,
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION,
    )


def _call_gemini(
    client: genai.Client,
    model_id: str,
    text: str,
    prompt_template: str,
) -> str:
    prompt = prompt_template.replace("{text}", text)
    response = client.models.generate_content(
        model=model_id,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return response.text


def _parse_json(raw: str) -> dict:
    """Parse JSON, stripping markdown code fences if present."""
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    return json.loads(cleaned)


def _summarize_item(
    client: genai.Client,
    model_id: str,
    prompt_template: str,
    item: Item,
) -> Item:
    """Call Gemini and parse result; retry once on any failure."""
    last_error: str = ""
    for attempt in range(2):
        try:
            raw = _call_gemini(client, model_id, item.raw_text, prompt_template)
            data = _parse_json(raw)
            item.title = data.get("title", "")
            item.tags = data.get("tags", [])
            item.summary = data.get("summary", "")
            item.summary_status = SummaryStatus.SUCCESS
            return item
        except Exception as exc:
            last_error = str(exc)[:300]

    item.summary_status = SummaryStatus.FAILED
    item.error_message = last_error
    return item


# ── Public API ─────────────────────────────────────────────────────────────────

def summarize_one(item: Item, model_key: str = "gemini-flash") -> Item:
    """Immediate single-item summarization (for 単件テストページ)."""
    if item.fetch_status != FetchStatus.SUCCESS or not item.raw_text:
        item.summary_status = SummaryStatus.SKIPPED
        return item

    model_id = MODELS[model_key]["model_id"]
    prompt_template = _load_prompt()
    client = _make_client()

    return _summarize_item(client, model_id, prompt_template, item)


def summarize_all(
    items: list[Item],
    model_key: str = "gemini-flash",
    batch: bool = True,  # reserved for future Gemini batch API; currently sequential
) -> list[Item]:
    """Summarize all items sequentially (for バッチ処理ページ)."""
    model_id = MODELS[model_key]["model_id"]
    prompt_template = _load_prompt()
    client = _make_client()

    results: list[Item] = []
    for item in items:
        if item.fetch_status != FetchStatus.SUCCESS or not item.raw_text:
            item.summary_status = SummaryStatus.SKIPPED
            results.append(item)
            continue
        results.append(_summarize_item(client, model_id, prompt_template, item))

    return results
