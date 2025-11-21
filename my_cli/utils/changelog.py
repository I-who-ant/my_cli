"""
Changelog 解析工具 ⭐ Stage 30

解析 Keep a Changelog 格式的 CHANGELOG.md 文件。

对应源码：kimi-cli-fork/src/kimi_cli/utils/changelog.py
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple


class ReleaseEntry(NamedTuple):
    description: str
    entries: list[str]


def parse_changelog(md_text: str) -> dict[str, ReleaseEntry]:
    """Parse a subset of Keep a Changelog-style markdown into a map:
    version -> (description, entries)
    """
    lines = md_text.splitlines()
    result: dict[str, ReleaseEntry] = {}

    current_ver: str | None = None
    collecting_desc = False
    desc_lines: list[str] = []
    bullet_lines: list[str] = []
    seen_content_after_header = False

    def commit():
        nonlocal current_ver, desc_lines, bullet_lines, result
        if current_ver is None:
            return
        description = "\n".join([line.strip() for line in desc_lines]).strip()
        norm_entries = [
            line.strip()[2:].strip() for line in bullet_lines if line.strip().startswith("- ")
        ]
        result[current_ver] = ReleaseEntry(description=description, entries=norm_entries)

    for raw in lines:
        line = raw.rstrip()
        if line.startswith("## ["):
            commit()
            end = line.find("]")
            ver = line[4:end] if end != -1 else line[3:].strip()
            current_ver = ver.strip()
            desc_lines = []
            bullet_lines = []
            collecting_desc = True
            seen_content_after_header = False
            continue

        if current_ver is None:
            continue

        if not line.strip():
            if collecting_desc and seen_content_after_header:
                collecting_desc = False
            continue

        seen_content_after_header = True

        if line.lstrip().startswith("### "):
            collecting_desc = False
            continue

        if line.lstrip().startswith("- "):
            collecting_desc = False
            bullet_lines.append(line.strip())
            continue

        if collecting_desc:
            desc_lines.append(line.strip())

    commit()
    return result


def format_release_notes(changelog: dict[str, ReleaseEntry], include_lib_changes: bool) -> str:
    """格式化发布说明"""
    parts: list[str] = []
    for ver, entry in changelog.items():
        s = f"[bold]{ver}[/bold]"
        if entry.description:
            s += f": {entry.description}"
        if entry.entries:
            for it in entry.entries:
                if it.lower().startswith("lib:") and not include_lib_changes:
                    continue
                s += "\n[markdown.item.bullet]• [/]" + it
        parts.append(s + "\n")
    return "\n".join(parts).strip()


# 尝试加载 CHANGELOG（如果存在）
_changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
if _changelog_path.exists():
    CHANGELOG = parse_changelog(_changelog_path.read_text(encoding="utf-8"))
else:
    CHANGELOG: dict[str, ReleaseEntry] = {}


__all__ = ["ReleaseEntry", "parse_changelog", "format_release_notes", "CHANGELOG"]
