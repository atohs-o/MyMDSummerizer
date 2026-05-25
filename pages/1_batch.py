"""
pages/1_batch.py — Batch processing page.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st

from pdf_summarizer.config import DEFAULT_MODEL, DEFAULT_OUTPUT_DIR, MODELS
from pdf_summarizer.fetcher import fetch_all
from pdf_summarizer.models import Item, SourceType

st.set_page_config(page_title="Batch処理", page_icon="📦")
st.title("📦 Batch処理")

# TODO: implement batch UI
# Flow:
# 1. URL paste area (st.text_area) or file upload (st.file_uploader, type=["pdf", "txt"])
# 2. Model selector (st.selectbox over MODELS.keys())
# 3. "実行" button → build list[Item] → fetch_all() → summarize_all(batch=True)
# 4. For Anthropic batch: poll with st.rerun() every BATCH_POLL_INTERVAL_SEC
# 5. Results: success accordion (title + summary preview) + failure table
# 6. "保存" button → render_note() for each success, render_failed() for failures

st.info("実装予定: バッチ処理UI")
