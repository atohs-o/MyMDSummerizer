"""
renderer.py — Generate Obsidian-formatted Markdown files.

Public API:
    render_note(item, output_dir, model_key) -> Path
    render_failed(items, output_dir) -> Path
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from slugify import slugify

from .models import FetchStatus, Item, SummaryStatus


# ── Public API ─────────────────────────────────────────────────────────────────

def render_note(item: Item, output_dir: Path, model_key: str) -> Path:
    """Write a success note as Obsidian-formatted Markdown; return its Path."""
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = slugify(item.title or item.id, allow_unicode=True) or item.id
    path = output_dir / f"{slug}.md"

    tags_yaml = "\n".join(f"  - {t}" for t in item.tags)
    today = date.today().isoformat()

    content = f"""\
---
title: "{_escape_yaml(item.title or "")}"
tags:
{tags_yaml}
source: "{_escape_yaml(item.source)}"
fetched_at: "{today}"
model: "{model_key}"
truncated: {str(item.truncated).lower()}
---

# {item.title}

## 出典
{item.source}

## 要約
{item.summary}
"""

    path.write_text(content, encoding="utf-8")
    item.output_path = path
    return path


def render_failed(items: list[Item], output_dir: Path) -> Path:
    """Write a failure summary Markdown table; return its Path."""
    failed_path = output_dir.parent / "failed.md"
    failed_path.parent.mkdir(parents=True, exist_ok=True)

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fetch_failed = [i for i in items if i.fetch_status != FetchStatus.SUCCESS]
    summary_failed = [
        i for i in items
        if i.fetch_status == FetchStatus.SUCCESS and i.summary_status == SummaryStatus.FAILED
    ]

    lines = [f"# 処理失敗リスト\n", f"生成日時: {now}\n"]

    lines.append("## fetch失敗\n")
    if fetch_failed:
        lines.append("| URL / ファイル | ステータス | 理由 |")
        lines.append("|---|---|---|")
        for item in fetch_failed:
            status = item.fetch_status.value if item.fetch_status else "-"
            reason = (item.error_message or "-").replace("|", "｜")
            lines.append(f"| {item.source} | {status} | {reason} |")
    else:
        lines.append("なし")

    lines.append("\n## 要約失敗\n")
    if summary_failed:
        lines.append("| URL / ファイル | ステータス | 理由 |")
        lines.append("|---|---|---|")
        for item in summary_failed:
            reason = (item.error_message or "-").replace("|", "｜")
            lines.append(f"| {item.source} | failed | {reason} |")
    else:
        lines.append("なし")

    failed_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return failed_path


# ── Helper ─────────────────────────────────────────────────────────────────────

def _escape_yaml(s: str) -> str:
    return s.replace('"', '\\"')
