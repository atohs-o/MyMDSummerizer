"""
pages/2_single.py — Single item test page.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st

from pdf_summarizer.config import DEFAULT_MODEL, MODELS
from pdf_summarizer.fetcher import fetch_all
from pdf_summarizer.models import Item, SourceType

st.set_page_config(page_title="単件テスト", page_icon="🔍")
st.title("🔍 単件テスト")

# TODO: implement single-item UI
# Flow:
# 1. Radio: "URL" or "PDFファイル"
# 2. URL input (st.text_input) or PDF upload (st.file_uploader)
# 3. Model selector + Batch API toggle (default OFF for single test)
# 4. "実行" button → fetch_all([item]) → summarize_one(item)
# 5. Expander "① Fetch結果": status badge, char count, truncated flag, text preview
# 6. Expander "② LLM出力": title, tags chips, summary text
# 7. Expander "③ Markdownプレビュー": st.code(rendered markdown)
# 8. "保存" button → render_note() → show output path

st.info("実装予定: 単件テストUI")
