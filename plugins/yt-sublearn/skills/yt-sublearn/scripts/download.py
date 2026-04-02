# /// script
# requires-python = ">=3.11"
# dependencies = ["yt-dlp>=2024.0.0"]
# ///
"""
Download English subtitles from YouTube, normalize them, and split them into
50-entry SRT chunks for parallel translation.

Usage:
  uv run download.py <youtube_url> <output_dir>

Exit codes:
  0 — success; absolute path to manifest JSON printed to stdout
  1 — no English subtitles available
  2 — other error
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CHUNK_SIZE = 50


@dataclass
class SRTEntry:
    start: str
    end: str
    text: str


def _clean_srt(srt_path: Path) -> None:
    """Remove duplicate rolling lines from YouTube auto-caption SRT files."""
    content = srt_path.read_text(encoding="utf-8")

    blocks = re.split(r"\n{2,}", content.strip())
    entries: list[tuple[str, list[str]]] = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        try:
            int(lines[0].strip())
        except ValueError:
            continue
        if "-->" not in lines[1]:
            continue
        entries.append((lines[1].strip(), lines[2:]))

    cleaned: list[tuple[str, list[str]]] = []
    prev_seen: set[str] = set()

    for timing, text_lines in entries:
        nonempty = {line.strip() for line in text_lines if line.strip()}
        new_lines = [
            line for line in text_lines if line.strip() and line.strip() not in prev_seen
        ]
        if new_lines:
            cleaned.append((timing, new_lines))
        if nonempty:
            prev_seen = nonempty

    output_blocks = [
        f"{i}\n{timing}\n" + "\n".join(text_lines)
        for i, (timing, text_lines) in enumerate(cleaned, 1)
    ]
    srt_path.write_text("\n\n".join(output_blocks) + "\n", encoding="utf-8")


def _normalize_join(left: str, right: str) -> str:
    left = left.strip()
    right = right.strip()

    if not left:
        return right
    if not right:
        return left
    if left.endswith("-"):
        return left[:-1] + right
    return f"{left} {right}"


def _extract_complete_sentences(text: str) -> tuple[list[str], str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return [], ""

    sentences: list[str] = []
    pos = 0
    pattern = re.compile(r'.*?[.!?]["\']?(?=\s|$)')

    while pos < len(text):
        match = pattern.match(text, pos)
        if not match:
            break
        sentence = match.group().strip()
        if not sentence:
            break
        sentences.append(sentence)
        pos = match.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1

    remaining = text[pos:].strip()
    return sentences, remaining


def _merge_short_sentences(entries: list[SRTEntry]) -> list[SRTEntry]:
    """Merge short sentences to avoid overly fragmented subtitles."""
    min_len = 30
    if not entries:
        return entries

    merged: list[SRTEntry] = []
    buffer = entries[0]

    for entry in entries[1:]:
        if len(buffer.text) < min_len:
            buffer = SRTEntry(
                start=buffer.start,
                end=entry.end,
                text=f"{buffer.text} {entry.text}".strip(),
            )
        else:
            merged.append(buffer)
            buffer = entry

    merged.append(buffer)
    return merged


def _parse_srt_entries(content: str) -> list[SRTEntry]:
    blocks = re.split(r"\n{2,}", content.strip())
    entries: list[SRTEntry] = []

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        try:
            int(lines[0].strip())
        except ValueError:
            continue

        timing = lines[1].strip()
        if "-->" not in timing:
            continue
        parts = timing.split("-->")
        if len(parts) != 2:
            continue

        start_time = parts[0].strip()
        end_time = parts[1].strip()
        text = " ".join(line.strip() for line in lines[2:] if line.strip())
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue

        entries.append(SRTEntry(start=start_time, end=end_time, text=text))

    return entries


def _merge_srt_to_sentences_inplace(srt_path: Path) -> None:
    content = srt_path.read_text(encoding="utf-8")
    entries = _parse_srt_entries(content)
    if not entries:
        return

    merged_entries: list[SRTEntry] = []
    buffer = ""
    sentence_start_time: str | None = None

    for entry in entries:
        if sentence_start_time is None:
            sentence_start_time = entry.start

        buffer = _normalize_join(buffer, entry.text)
        buffer = re.sub(r"\s+", " ", buffer).strip()
        complete_sentences, remaining = _extract_complete_sentences(buffer)

        if complete_sentences:
            for sentence in complete_sentences:
                merged_entries.append(
                    SRTEntry(start=sentence_start_time, end=entry.end, text=sentence)
                )
            buffer = remaining
            sentence_start_time = entry.start if remaining else None

    if buffer.strip() and sentence_start_time is not None:
        merged_entries.append(
            SRTEntry(start=sentence_start_time, end=entries[-1].end, text=buffer.strip())
        )

    merged_entries = _merge_short_sentences(merged_entries)

    output_blocks = [
        f"{i}\n{entry.start} --> {entry.end}\n{entry.text}"
        for i, entry in enumerate(merged_entries, 1)
    ]
    srt_path.write_text("\n\n".join(output_blocks) + "\n", encoding="utf-8")


def _has_english_subs(url: str) -> bool:
    result = subprocess.run(
        ["yt-dlp", "--list-subs", "--skip-download", url],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(re.search(r"^\s*en\b", result.stdout, re.MULTILINE))


def _download_srt(url: str, output_dir: Path) -> Path:
    subprocess.run(
        [
            "yt-dlp",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang",
            "en",
            "--convert-subs",
            "srt",
            "--skip-download",
            "-o",
            str(output_dir / "%(title)s.%(ext)s"),
            url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    srt_files = sorted(output_dir.glob("*.en.srt"), key=lambda p: p.stat().st_mtime)
    if not srt_files:
        raise FileNotFoundError("No .en.srt file found.")
    return srt_files[-1]


def _slugify_filename(name: str) -> str:
    name = re.sub(r"\s+", "_", name.strip())
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("._") or "subtitle"


def _iter_chunks(items: list[SRTEntry], size: int) -> Iterable[list[SRTEntry]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _write_srt_entries(entries: list[SRTEntry], output_path: Path) -> None:
    blocks = [
        f"{i}\n{entry.start} --> {entry.end}\n{entry.text}"
        for i, entry in enumerate(entries, 1)
    ]
    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def _split_into_chunk_files(srt_path: Path, output_dir: Path) -> dict[str, object]:
    entries = _parse_srt_entries(srt_path.read_text(encoding="utf-8"))
    if not entries:
        raise ValueError("Normalized subtitle file contains no valid entries.")

    stem = srt_path.name[:-4] if srt_path.name.endswith(".srt") else srt_path.stem
    safe_stem = _slugify_filename(stem)
    chunk_dir = output_dir / f"{safe_stem}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)

    bilingual_dir = output_dir / f"{safe_stem}_translated_chunks"
    bilingual_dir.mkdir(parents=True, exist_ok=True)

    chunk_paths: list[str] = []
    chunk_output_paths: list[str] = []

    for idx, chunk_entries in enumerate(_iter_chunks(entries, CHUNK_SIZE), 1):
        chunk_path = chunk_dir / f"chunk_{idx:03d}.srt"
        chunk_output_path = bilingual_dir / f"chunk_{idx:03d}_bilingual.txt"
        _write_srt_entries(chunk_entries, chunk_path)
        chunk_paths.append(str(chunk_path.resolve()))
        chunk_output_paths.append(str(chunk_output_path.resolve()))

    final_bilingual_path = output_dir / f"{safe_stem}_bilingual.txt"
    summary_source_path = output_dir / f"{safe_stem}_summary_source.txt"
    manifest_path = output_dir / f"{safe_stem}_manifest.json"

    manifest = {
        "source_srt": str(srt_path.resolve()),
        "chunk_size": CHUNK_SIZE,
        "chunk_dir": str(chunk_dir.resolve()),
        "translated_chunk_dir": str(bilingual_dir.resolve()),
        "chunk_paths": chunk_paths,
        "chunk_output_paths": chunk_output_paths,
        "final_bilingual_path": str(final_bilingual_path.resolve()),
        "summary_source_path": str(summary_source_path.resolve()),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {"manifest_path": str(manifest_path.resolve()), **manifest}


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: uv run download.py <youtube_url> <output_dir>", file=sys.stderr)
        sys.exit(2)

    url = sys.argv[1]
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        has_en = _has_english_subs(url)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: yt-dlp failed:\n{exc.stderr}", file=sys.stderr)
        sys.exit(2)

    if not has_en:
        print("ERROR: No English subtitles.", file=sys.stderr)
        sys.exit(1)

    try:
        srt_path = _download_srt(url, output_dir)
        _clean_srt(srt_path)
        _merge_srt_to_sentences_inplace(srt_path)
        result = _split_into_chunk_files(srt_path, output_dir)
        print(result["manifest_path"])
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: yt-dlp failed:\n{exc.stderr}", file=sys.stderr)
        sys.exit(2)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
