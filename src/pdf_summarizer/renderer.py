"""
renderer.py — Generate Obsidian-formatted Markdown files.

Public API:
    render_note(item, output_dir, model_key) -> Path
    render_failed(items, output_dir) -> Path
"""
from __future__ import annotations

from pathlib import Path

from .models import Item


def render_note(item: Item, output_dir: Path, model_key: str) -> Path:
    # TODO: implement
    # - YAML frontmatter: title, tags, source, date, model
    # - Body: item.summary
    # - Filename: slugify(item.title) + ".md" via python-slugify
    # - Write to output_dir / filename
    # - Set item.output_path and return Path
    raise NotImplementedError


def render_failed(items: list[Item], output_dir: Path) -> Path:
    # TODO: implement
    # - Markdown table: | source | fetch_status | summary_status | error_message |
    # - Write to output_dir.parent / "failed.md"
    # - Return Path
    raise NotImplementedError
