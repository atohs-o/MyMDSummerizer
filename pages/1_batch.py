"""
pages/1_batch.py — バッチ処理ページ。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from slugify import slugify

from pdf_summarizer.config import DEFAULT_MODEL, DEFAULT_OUTPUT_DIR, MODELS
from pdf_summarizer.fetcher import fetch_all
from pdf_summarizer.models import FetchStatus, Item, SourceType, SummaryStatus
from pdf_summarizer.renderer import render_failed, render_note
from pdf_summarizer.summarizer import summarize_all

st.set_page_config(page_title="Batch処理", page_icon="📦")
st.title("📦 Batch処理")

# ── 入力 UI ───────────────────────────────────────────────────────────────────

input_mode = st.radio("入力方法", ["URLリスト", "PDFアップロード"], horizontal=True)

raw_urls: list[str] = []
pdf_items: list[Item] = []

if input_mode == "URLリスト":
    text = st.text_area(
        "URLを1行1件で貼り付け（または urls.txt をアップロード）",
        height=180,
        placeholder="https://example.com/paper1.pdf\nhttps://example.com/paper2",
    )
    uploaded_txt = st.file_uploader("urls.txt をアップロード", type=["txt"])
    if uploaded_txt:
        text = uploaded_txt.read().decode("utf-8")
    raw_urls = [u.strip() for u in (text or "").splitlines() if u.strip()]
else:
    uploaded_pdfs = st.file_uploader("PDFファイル（複数可）", type=["pdf"], accept_multiple_files=True)
    for f in uploaded_pdfs or []:
        tmp_path = Path(f"/tmp/_batch_{f.name}")
        tmp_path.write_bytes(f.read())
        pdf_items.append(
            Item(
                id=slugify(tmp_path.stem, allow_unicode=False) or tmp_path.stem,
                source_type=SourceType.PDF,
                source=str(tmp_path),
            )
        )

model_key = st.selectbox("モデル", list(MODELS.keys()), index=list(MODELS.keys()).index(DEFAULT_MODEL))
output_dir = Path(st.text_input("出力先ディレクトリ", value=str(DEFAULT_OUTPUT_DIR)))

all_ready = bool(raw_urls or pdf_items)
run = st.button("▶ 実行", type="primary", disabled=not all_ready)

# ── セッションステート初期化 ───────────────────────────────────────────────────

if "batch_items" not in st.session_state:
    st.session_state["batch_items"] = []
if "batch_done" not in st.session_state:
    st.session_state["batch_done"] = False

# ── 実行ロジック ───────────────────────────────────────────────────────────────

if run:
    st.session_state["batch_done"] = False

    if input_mode == "URLリスト":
        items = [
            Item(
                id=slugify(u.split("/")[-1].split("?")[0], allow_unicode=False) or f"item-{i}",
                source_type=SourceType.URL,
                source=u,
            )
            for i, u in enumerate(raw_urls)
        ]
    else:
        items = pdf_items

    progress = st.progress(0, text="fetch 中...")
    with st.spinner("fetch 中..."):
        fetched = fetch_all(items)
    progress.progress(50, text="LLM 処理中...")

    with st.spinner("LLM 処理中..."):
        results = summarize_all(fetched, model_key=model_key)
    progress.progress(100, text="完了")

    st.session_state["batch_items"] = results
    st.session_state["batch_done"] = True

# ── 結果表示 ──────────────────────────────────────────────────────────────────

items: list[Item] = st.session_state.get("batch_items", [])
done: bool = st.session_state.get("batch_done", False)

if not items:
    st.stop()

success = [i for i in items if i.summary_status == SummaryStatus.SUCCESS]
fetch_failed = [i for i in items if i.fetch_status != FetchStatus.SUCCESS]
summary_failed = [
    i for i in items
    if i.fetch_status == FetchStatus.SUCCESS and i.summary_status != SummaryStatus.SUCCESS
]

st.markdown(
    f"**完了: {len(success)}件成功 / {len(fetch_failed)}件fetch失敗 / {len(summary_failed)}件要約失敗**"
)

if success:
    st.markdown("### 成功")
    for item in success:
        with st.expander(f"📄 {item.title or item.source}"):
            st.markdown(f"**タグ:** " + " / ".join(f"`{t}`" for t in item.tags))
            st.write(item.summary)

failed_all = fetch_failed + summary_failed
if failed_all:
    st.markdown("### 失敗リスト")
    rows = []
    for item in failed_all:
        status = item.fetch_status.value if item.fetch_status else "-"
        rows.append({"URL / ファイル": item.source, "ステータス": status, "理由": item.error_message or "-"})
    st.table(rows)

# ── 書き出しボタン ─────────────────────────────────────────────────────────────

if done and success:
    if st.button("⬇ output/ に書き出す"):
        saved = []
        for item in success:
            p = render_note(item, output_dir, model_key)
            saved.append(p)
        if failed_all:
            render_failed(items, output_dir)
        st.success(f"{len(saved)}件を `{output_dir}` に保存しました。")
