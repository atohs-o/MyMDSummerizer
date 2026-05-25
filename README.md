# MyMDSummerizer

URLリストおよびPDFファイルをGemini（Vertex AI）で要約し、Obsidian向けMarkdownファイルとして出力するツール。

---

## 機能

- **URLバッチ処理** — URLを複数貼り付けて一括要約
- **PDF対応** — ローカルPDFまたはURLから取得したPDFのテキスト抽出・要約
- **URL + PDF 混在** — 両者を同時にまとめて処理可能
- **単件テスト** — 1件ずつ結果を確認しながら試せるページ
- **Obsidian出力** — YAMLフロントマター付きMarkdownを指定ディレクトリに保存
- **失敗レポート** — fetch・要約に失敗したアイテムをテーブル形式で `failed.md` に記録

---

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -e .
```

### 2. Vertex AI の準備

1. [Google Cloud Console](https://console.cloud.google.com) で **Vertex AI API** を有効化
2. サービスアカウントを作成し、`roles/aiplatform.user` ロールを付与
3. サービスアカウントのJSONキーをダウンロードして保存（例: `~/.config/gcp-keys/your-project-sa.json`）

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集：

```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

DEFAULT_MODEL=gemini-2.5-flash
DEFAULT_OUTPUT_DIR=/path/to/your/obsidian/vault
TEXT_CHAR_LIMIT=100000
BATCH_POLL_INTERVAL_SEC=60
```

---

## 起動

```bash
streamlit run app.py
```

ブラウザで http://localhost:8501 が開きます。

---

## 使い方

### 📦 Batch処理ページ

1. URLを1行1件で貼り付け（または `urls.txt` をアップロード）
2. PDFファイルを複数アップロード（URLと同時指定可）
3. モデルと出力先を確認して「▶ 実行」
4. 完了後、「⬇ output/ に書き出す」でMarkdownファイルを保存

### 🔍 単件テストページ

1. URLまたはPDFを1件指定して「▶ 実行」
2. fetch結果・LLM出力・Markdownプレビューを順に確認
3. 問題なければ「⬇ このファイルを保存」

---

## 出力フォーマット

```markdown
---
title: "論文タイトル"
tags:
  - タグ1
  - タグ2
source: "https://example.com/paper"
fetched_at: "2026-05-25"
model: "gemini-2.5-flash"
truncated: false
---

# 論文タイトル

## 出典
https://example.com/paper

## 要約
要約本文...
```

---

## ディレクトリ構成

```
MyMDSummerizer/
├── app.py                     # Streamlit エントリーポイント
├── pages/
│   ├── 1_batch.py             # バッチ処理ページ
│   └── 2_single.py            # 単件テストページ
├── src/pdf_summarizer/
│   ├── config.py              # 設定・環境変数
│   ├── fetcher.py             # URL fetch / PDF読み込み
│   ├── summarizer.py          # Gemini API呼び出し
│   ├── renderer.py            # Markdown生成
│   └── models.py              # データクラス
├── prompts/
│   └── summarize.txt          # 要約プロンプト（Few-shot例入り）
├── input/                     # URLリスト・PDFの置き場
├── output/
│   ├── notes/                 # 生成されたMarkdownファイル
│   └── failed.md              # 失敗レポート
├── .env.example
└── pyproject.toml
```

---

## 対応モデル

| キー | モデル |
|---|---|
| `gemini-2.5-flash` | Gemini 2.5 Flash（デフォルト） |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite |
| `claude-sonnet` | Claude Sonnet 4.6（要Anthropic APIキー） |
| `claude-haiku` | Claude Haiku 4.5（要Anthropic APIキー） |
