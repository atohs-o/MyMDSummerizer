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

st.markdown("**URL リスト**")
text = st.text_area(
    "URLを1行1件で貼り付け",
    height=150,
    placeholder="https://example.com/paper1.pdf\nhttps://example.com/paper2",
    label_visibility="collapsed",
)
uploaded_txt = st.file_uploader("urls.txt をアップロード", type=["txt"])
if uploaded_txt:
    text = uploaded_txt.read().decode("utf-8")
raw_urls = [u.strip() for u in (text or "").splitlines() if u.strip()]

st.markdown("**PDF ファイル**")
uploaded_pdfs = st.file_uploader("PDFファイル（複数可）", type=["pdf"], accept_multiple_files=True)
pdf_items: list[Item] = []
for f in uploaded_pdfs or []:
    tmp_path = Path(f"/tmp/_batch_{f.name}")
    tmp_path.write_bytes(f.read())
    pdf_items.append(
        Item(
            id=slugify(tmp_path.stem, allow_unicode=True) or tmp_path.stem,
            source_type=SourceType.PDF,
            source=str(tmp_path),
        )
    )

model_key = st.selectbox("モデル", list(MODELS.keys()), index=list(MODELS.keys()).index(DEFAULT_MODEL))
output_dir = Path(st.text_input("出力先ディレクトリ", value=str(DEFAULT_OUTPUT_DIR)))

total = len(raw_urls) + len(pdf_items)
run = st.button(f"▶ 実行（{total}件）" if total else "▶ 実行", type="primary", disabled=total == 0)

# ── セッションステート初期化 ───────────────────────────────────────────────────

if "batch_items" not in st.session_state:
    st.session_state["batch_items"] = []
if "batch_done" not in st.session_state:
    st.session_state["batch_done"] = False

# ── 実行ロジック ───────────────────────────────────────────────────────────────

if run:
    st.session_state["batch_done"] = False

    url_items = [
        Item(
            id=slugify(u.split("/")[-1].split("?")[0], allow_unicode=True) or f"item-{i}",
            source_type=SourceType.URL,
            source=u,
        )
        for i, u in enumerate(raw_urls)
    ]
    items = url_items + pdf_items
    n = len(items)

    # ① fetch
    st.markdown("**① fetch中...**")
    fetch_bar = st.progress(0, text=f"0 / {n} 件")
    fetch_label = st.empty()

    fetched = fetch_all(items)

    fetch_ok = sum(1 for i in fetched if i.fetch_status == FetchStatus.SUCCESS)
    fetch_ng = n - fetch_ok
    fetch_bar.progress(1.0, text=f"{n} / {n} 件")
    fetch_label.markdown(f"✅ fetch完了: **{fetch_ok}件**取得 / {fetch_ng}件失敗")

    # ② 要約
    st.markdown("**② 要約中...**")
    sum_bar = st.progress(0, text=f"0 / {fetch_ok} 件")
    sum_label = st.empty()

    def _on_progress(current: int, total: int, source: str) -> None:
        sum_bar.progress(current / total, text=f"{current} / {total} 件")
        sum_label.caption(f"処理中: {source[:80]}")

    results = summarize_all(fetched, model_key=model_key, on_progress=_on_progress)
    sum_label.empty()
    sum_bar.progress(1.0, text=f"{fetch_ok} / {fetch_ok} 件")
    st.markdown("✅ 要約完了")

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
            st.markdown("**タグ:** " + " / ".join(f"`{t}`" for t in item.tags))
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
        save_bar = st.progress(0, text="保存中...")
        save_label = st.empty()
        saved = []
        try:
            for i, item in enumerate(success):
                save_label.caption(f"{i + 1} / {len(success)} 件  —  {item.title or item.source}")
                p = render_note(item, output_dir, model_key)
                saved.append(p)
                save_bar.progress((i + 1) / len(success), text="保存中...")
            if failed_all:
                render_failed(items, output_dir)
            save_bar.empty()
            save_label.empty()
            st.success(f"✅ {len(saved)}件を {output_dir} に保存しました。")
        except Exception as e:
            st.error(f"保存中にエラーが発生しました: {e}")
