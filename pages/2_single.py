"""
pages/2_single.py — 単件動作確認ページ。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st

from pdf_summarizer.config import DEFAULT_MODEL, DEFAULT_OUTPUT_DIR, MODELS
from pdf_summarizer.fetcher import fetch_all
from pdf_summarizer.models import FetchStatus, Item, SourceType, SummaryStatus
from pdf_summarizer.renderer import render_note
from pdf_summarizer.summarizer import summarize_one

st.set_page_config(page_title="単件テスト", page_icon="🔍")
st.title("🔍 単件テスト")

# ── 入力 UI ───────────────────────────────────────────────────────────────────

input_type = st.radio("入力タイプ", ["URL", "PDFアップロード"], horizontal=True)

url_input: str = ""
pdf_bytes: bytes | None = None

if input_type == "URL":
    url_input = st.text_input("URL", placeholder="https://example.com/paper.pdf")
else:
    uploaded = st.file_uploader("PDFファイル", type=["pdf"])
    if uploaded:
        pdf_bytes = uploaded.read()

model_key = st.selectbox("モデル", list(MODELS.keys()), index=list(MODELS.keys()).index(DEFAULT_MODEL))

run = st.button("▶ 実行", type="primary", disabled=not (url_input or pdf_bytes))

# ── 実行ロジック ───────────────────────────────────────────────────────────────

if run:
    st.session_state.pop("single_item", None)

    if input_type == "URL":
        item = Item(id="single", source_type=SourceType.URL, source=url_input)
    else:
        tmp_path = Path("/tmp/_upload.pdf")
        tmp_path.write_bytes(pdf_bytes)
        item = Item(id="single", source_type=SourceType.PDF, source=str(tmp_path))

    with st.spinner("fetch 中..."):
        [item] = fetch_all([item])

    with st.spinner("LLM 処理中..."):
        item = summarize_one(item, model_key=model_key)

    st.session_state["single_item"] = item

# ── 結果表示 ──────────────────────────────────────────────────────────────────

item: Item | None = st.session_state.get("single_item")

if item is None:
    st.stop()

# ① fetch 結果
fetch_ok = item.fetch_status == FetchStatus.SUCCESS
status_icon = "✅" if fetch_ok else "❌"

with st.expander(f"① fetch結果 — {status_icon} {item.fetch_status.value if item.fetch_status else '-'}", expanded=True):
    if fetch_ok:
        col1, col2 = st.columns(2)
        col1.metric("取得文字数", f"{len(item.raw_text or ''):,} 文字")
        col2.metric("切り詰め", "あり" if item.truncated else "なし")
        with st.expander("全文を表示"):
            st.text(item.raw_text)
    else:
        st.error(item.error_message or "fetch 失敗")

if not fetch_ok:
    st.stop()

# ② LLM 出力
summary_ok = item.summary_status == SummaryStatus.SUCCESS
s_icon = "✅" if summary_ok else "❌"

with st.expander(f"② LLM出力 — {s_icon} {item.summary_status.value if item.summary_status else '-'}", expanded=True):
    if summary_ok:
        st.markdown(f"**タイトル:** {item.title}")
        st.markdown("**タグ:** " + " / ".join(f"`{t}`" for t in item.tags))
        st.markdown("**要約:**")
        st.write(item.summary)
    else:
        st.error(item.error_message or "要約失敗")

if not summary_ok:
    st.stop()

# ③ Markdown プレビュー
from datetime import date

tags_yaml = "\n".join(f"  - {t}" for t in item.tags)
preview_md = f"""\
---
title: "{item.title}"
tags:
{tags_yaml}
source: "{item.source}"
fetched_at: "{date.today().isoformat()}"
model: "{model_key}"
truncated: {str(item.truncated).lower()}
---

# {item.title}

## 出典
{item.source}

## 要約
{item.summary}
"""

with st.expander("③ 生成されるMarkdownプレビュー", expanded=True):
    st.code(preview_md, language="markdown")

# ④ 保存ボタン
if st.button("⬇ このファイルを保存"):
    output_dir = DEFAULT_OUTPUT_DIR
    saved_path = render_note(item, output_dir, model_key)
    st.success(f"保存しました: `{saved_path}`")
