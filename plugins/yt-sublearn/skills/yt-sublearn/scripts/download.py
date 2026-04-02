# /// script
# requires-python = ">=3.11"
# dependencies = ["yt-dlp>=2024.0.0"]
# ///
"""
Download English subtitles from YouTube using yt-dlp.

Usage: uv run download.py <youtube_url> <output_dir>

Exit codes:
  0 — success; absolute path to .en.srt file printed to stdout
  1 — no English subtitles available
  2 — other error (network, invalid URL, etc.)
"""

import re
import sys
import subprocess
from pathlib import Path


def _clean_srt(srt_path: Path) -> None:
    """Remove duplicate rolling lines from YouTube auto-caption SRT files."""
    content = srt_path.read_text(encoding="utf-8")

    blocks = re.split(r"\n{2,}", content.strip())
    entries = []
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

    cleaned = []
    prev_seen = set()

    for timing, text_lines in entries:
        nonempty = {line.strip() for line in text_lines if line.strip()}
        new_lines = [
            line for line in text_lines
            if line.strip() and line.strip() not in prev_seen
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


def _extract_complete_sentences(text: str):
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return [], ""

    sentences = []
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


def _merge_short_sentences(entries):
    """Merge short sentences to avoid overly fragmented subtitles."""
    MIN_LEN = 30  # 👈 可以自行調整

    if not entries:
        return entries

    merged = []
    buffer_start, buffer_end, buffer_text = entries[0]

    for start, end, text in entries[1:]:
        if len(buffer_text) < MIN_LEN:
            buffer_text = buffer_text + " " + text
            buffer_end = end
        else:
            merged.append((buffer_start, buffer_end, buffer_text))
            buffer_start, buffer_end, buffer_text = start, end, text

    merged.append((buffer_start, buffer_end, buffer_text))
    return merged


def _merge_srt_to_sentences_inplace(srt_path: Path) -> None:
    content = srt_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n{2,}", content.strip())

    entries = []
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

        entries.append((start_time, end_time, text))

    if not entries:
        return

    merged_entries = []

    buffer = ""
    sentence_start_time = None

    for start_time, end_time, text in entries:
        if sentence_start_time is None:
            sentence_start_time = start_time

        buffer = _normalize_join(buffer, text)
        buffer = re.sub(r"\s+", " ", buffer).strip()

        complete_sentences, remaining = _extract_complete_sentences(buffer)

        if complete_sentences:
            for sentence in complete_sentences:
                merged_entries.append((sentence_start_time, end_time, sentence))

            buffer = remaining
            sentence_start_time = start_time if remaining else None

    if buffer.strip() and sentence_start_time is not None:
        last_end_time = entries[-1][1]
        merged_entries.append((sentence_start_time, last_end_time, buffer.strip()))

    # ⭐ 加這行：避免句子太碎
    merged_entries = _merge_short_sentences(merged_entries)

    output_blocks = [
        f"{i}\n{start} --> {end}\n{text}"
        for i, (start, end, text) in enumerate(merged_entries, 1)
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
            "--sub-lang", "en",
            "--convert-subs", "srt",
            "--skip-download",
            "-o", str(output_dir / "%(title)s.%(ext)s"),
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
        print(str(srt_path))
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: yt-dlp failed:\n{exc.stderr}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
