# MyMDSummerizer

URLリストおよびPDFファイルをLLM（Google Gemini / Claude）で要約し、Obsidian向けMarkdownファイルとして出力するStreamlitアプリ。

---

## 機能

- **URLバッチ処理** — URLを複数貼り付けて一括取得・要約
- **PDF対応** — ローカルPDFまたはURLから取得したPDFのテキスト抽出・要約
- **URL + PDF 混在** — 両者を同じバッチで同時処理
- **単件テスト** — 1件ずつfetch結果・LLM出力・Markdownプレビューを確認しながら試せるページ
- **Obsidian出力** — YAMLフロントマター付きMarkdownを指定ディレクトリに保存
- **失敗レポート** — fetch・要約に失敗したアイテムを `failed.md` に記録

---

## セットアップ

### 1. 依存ライブラリのインストール

```bash
pip install -e .
```

Python 3.9 以上が必要です。

### 2. Vertex AI の準備

1. [Google Cloud Console](https://console.cloud.google.com) で **Vertex AI API** を有効化
2. 認証方法はいずれか一方：
   - **ADC（推奨）**: `gcloud auth application-default login` を実行（`.env` に `GOOGLE_APPLICATION_CREDENTIALS` 不要）
   - **サービスアカウントJSON**: サービスアカウントを作成し `roles/aiplatform.user` を付与 → JSONキーをダウンロードしてパスを `.env` に記載

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` を編集：

```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# サービスアカウントJSONを使う場合のみ設定（ADCなら不要）
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

DEFAULT_MODEL=gemini-2.5-flash
DEFAULT_OUTPUT_DIR=/path/to/your/obsidian/vault
TEXT_CHAR_LIMIT=100000

# Claudeモデルを使う場合のみ設定
# ANTHROPIC_API_KEY=sk-ant-...
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
3. モデルと出力先ディレクトリを確認して「▶ 実行」
4. フェーズ表示：
   - **① fetch中** — 全件並列取得、完了後に取得件数を表示
   - **② 要約中** — 1件ごとにプログレスバーと処理中ソースを更新
5. 完了後、「⬇ output/ に書き出す」で全成功件のMarkdownを保存
   - 保存完了後、結果件数と保存先をページ上部に表示

### 🔍 単件テストページ

1. URLまたはPDFを1件指定して「▶ 実行」
2. fetch結果・LLM出力（タイトル/タグ/要約）・Markdownプレビューを順に確認
3. 問題なければ「⬇ このファイルを保存」

---

## 要約フォーマット

要約は日本語で約1000字、見出し・箇条書きを使わない段落形式で出力されます。
内容は以下の4点で構成：

1. **論証の骨格** — 筆者の主張とその根拠
2. **見落とされがちな論点** — 表面化しにくい問題や実証データ
3. **処方箋の論理** — 結論・提案の導かれ方
4. **参照軸** — 引用・参照されている思想家・概念

---

## 出力ファイルフォーマット

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

ファイル名はタイトルをスラッグ化したもの（日本語はそのまま保持）。

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
│   ├── fetcher.py             # URL fetch / PDF読み込み（非同期並列）
│   ├── summarizer.py          # LLM API呼び出し（Gemini / Claude）
│   ├── renderer.py            # Markdown生成・ファイル書き出し
│   └── models.py              # データクラス（Item, FetchStatus, SummaryStatus）
├── prompts/
│   └── summarize.txt          # 要約プロンプト（Few-shot例入り）
├── .env.example
└── pyproject.toml
```

---

## 対応モデル

| キー | モデル | 備考 |
|---|---|---|
| `gemini-2.5-flash` | Gemini 2.5 Flash | デフォルト |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite | 高速・低コスト |
| `claude-sonnet` | Claude Sonnet 4.6 | `ANTHROPIC_API_KEY` 必須 |
| `claude-haiku` | Claude Haiku 4.5 | `ANTHROPIC_API_KEY` 必須 |

GeminiはVertex AI経由（`GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION`）で利用します。
