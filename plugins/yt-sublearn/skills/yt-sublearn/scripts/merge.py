# /// script
# requires-python = ">=3.11"
# ///
"""
Merge bilingual chunk outputs into one final file and prepare a smaller summary
source file for the main agent.

Usage:
  uv run merge.py <manifest_json_path>

Exit codes:
  0 — success; absolute path to final bilingual file printed to stdout
  2 — other error
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SUMMARY_MAX_ENTRIES = 120
SUMMARY_MAX_CHARS = 12000


TIMESTAMP_LINE_RE = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s?(.*)$")


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_required_files(paths: list[str]) -> list[str]:
    contents: list[str] = []
    missing: list[str] = []

    for p in paths:
        path = Path(p)
        if not path.exists():
            missing.append(str(path))
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            missing.append(f"{path} (empty)")
            continue
        contents.append(text)

    if missing:
        raise FileNotFoundError(
            "Missing or empty translated chunk files:\n" + "\n".join(missing)
        )
    return contents


def _build_summary_source(merged_text: str) -> str:
    blocks = re.split(r"\n{2,}", merged_text.strip())
    selected: list[str] = []
    total_chars = 0

    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2:
            continue

        en_match = TIMESTAMP_LINE_RE.match(lines[0])
        zh_match = TIMESTAMP_LINE_RE.match(lines[1])
        if not en_match or not zh_match:
            continue

        ts = en_match.group(1)
        en_text = en_match.group(2).strip()
        zh_text = zh_match.group(2).strip()
        compact = f"[{ts}] EN: {en_text}\n[{ts}] ZH: {zh_text}"

        projected = total_chars + len(compact) + 2
        if len(selected) >= SUMMARY_MAX_ENTRIES or projected > SUMMARY_MAX_CHARS:
            break

        selected.append(compact)
        total_chars = projected

    return "\n\n".join(selected).strip() + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: uv run merge.py <manifest_json_path>", file=sys.stderr)
        sys.exit(2)

    manifest_path = Path(sys.argv[1]).resolve()

    try:
        manifest = _load_manifest(manifest_path)
        chunk_output_paths = manifest["chunk_output_paths"]
        final_bilingual_path = Path(manifest["final_bilingual_path"]).resolve()
        summary_source_path = Path(manifest["summary_source_path"]).resolve()

        contents = _read_required_files(chunk_output_paths)
        merged_text = "\n\n".join(text.strip() for text in contents if text.strip()).strip() + "\n"
        final_bilingual_path.write_text(merged_text, encoding="utf-8")

        summary_source = _build_summary_source(merged_text)
        summary_source_path.write_text(summary_source, encoding="utf-8")

        print(str(final_bilingual_path))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
