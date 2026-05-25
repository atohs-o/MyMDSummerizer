"""
app.py — Streamlit entry point.

Run with: uv run streamlit run app.py
"""
import streamlit as st

st.set_page_config(
    page_title="MyMDSummerizer",
    page_icon="📝",
    layout="wide",
)

st.title("MyMDSummerizer")
st.markdown(
    "URLリストまたはPDFをLLMで要約し、Obsidian向けMarkdownファイルとして出力します。"
)
st.info("左のサイドバーからページを選択してください。")
