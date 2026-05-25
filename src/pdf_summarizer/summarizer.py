"""
summarizer.py — LLM summarization (Anthropic Batch API / Google Generative AI).

Public API:
    summarize_all(items, model_key, batch=True) -> list[Item]
    summarize_one(item, model_key) -> Item
"""
from __future__ import annotations

from .config import ANTHROPIC_API_KEY, GOOGLE_API_KEY, MODELS, PROMPTS_DIR
from .models import Item, SummaryStatus


def summarize_all(
    items: list[Item],
    model_key: str = "gemini-flash",
    batch: bool = True,
) -> list[Item]:
    # TODO: implement
    # - Filter items where fetch_status == SUCCESS
    # - Load prompt from PROMPTS_DIR / "summarize.txt"
    # - If provider == "anthropic" and batch=True: use Anthropic Batch API
    #   POST /v1/messages/batches → poll every BATCH_POLL_INTERVAL_SEC → GET results
    # - If provider == "google": use google-genai SDK (non-batch)
    # - Parse JSON response; set title, tags, summary, summary_status on Item
    # - On parse error: retry once, then set summary_status = FAILED
    raise NotImplementedError


def summarize_one(item: Item, model_key: str = "gemini-flash") -> Item:
    # TODO: implement
    # - Single synchronous LLM call (no batch)
    # - Same JSON parse + retry logic as summarize_all
    raise NotImplementedError
