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
    """Remove duplicate rolling lines from YouTube auto-caption SRT files.

    YouTube auto-captions use a "rolling" format where each entry repeats the
    last line of the previous entry. This function deduplicates those lines so
    each entry contains only the text that first appears in it.
    """
    content = srt_path.read_text(encoding="utf-8")

    # Parse SRT blocks separated by blank lines
    blocks = re.split(r"\n{2,}", content.strip())
    entries = []
    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue
        try:
            int(lines[0])  # must start with a sequence number
        except ValueError:
            continue
        if "-->" not in lines[1]:
            continue
        entries.append((lines[1], lines[2:]))  # (timing, text_lines)

    cleaned: list[tuple[str, list[str]]] = []
    prev_seen: set[str] = set()

    for timing, text_lines in entries:
        nonempty = {l.strip() for l in text_lines if l.strip()}
        new_lines = [l for l in text_lines if l.strip() and l.strip() not in prev_seen]
        if new_lines:
            cleaned.append((timing, new_lines))
        if nonempty:
            prev_seen = nonempty

    output_blocks = [
        f"{i}\n{timing}\n" + "\n".join(text_lines)
        for i, (timing, text_lines) in enumerate(cleaned, 1)
    ]
    srt_path.write_text("\n\n".join(output_blocks) + "\n", encoding="utf-8")


def _has_english_subs(url: str) -> bool:
    """Return True if the video has English subtitles (manual or auto-generated).

    Raises subprocess.CalledProcessError if yt-dlp fails (invalid URL, network error, etc.).
    """
    result = subprocess.run(
        ["yt-dlp", "--list-subs", "--skip-download", url],
        capture_output=True,
        text=True,
        check=True,
    )
    # Match "en" at the start of a line (covers en, en-US, en-GB, etc.)
    return bool(re.search(r"^\s*en\b", result.stdout, re.MULTILINE))


def _download_srt(url: str, output_dir: Path) -> Path:
    """Download English subtitles and convert to SRT. Returns path to .en.srt file."""
    subprocess.run(
        [
            "yt-dlp",
            "--write-sub",       # manual subtitles
            "--write-auto-sub",  # auto-generated (filtered to English via --sub-lang)
            "--sub-lang", "en",  # English only — rejects all other languages
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
        raise FileNotFoundError(
            "yt-dlp reported success but no .en.srt file was found in the output directory."
        )
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
        print(
            "ERROR: This video has no English subtitles (neither manual nor auto-generated).\n"
            "Only English subtitles are supported. Please choose a video with English subtitles.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        srt_path = _download_srt(url, output_dir)
        _clean_srt(srt_path)
        print(str(srt_path))
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: yt-dlp failed:\n{exc.stderr}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
