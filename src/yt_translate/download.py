"""
Download English subtitles from YouTube using yt-dlp.

Usage: yt-download <url> <output_dir>

Exit codes:
  0 — success; absolute path to .en.srt file printed to stdout
  1 — no English subtitles available
  2 — other error (network, invalid URL, etc.)
"""

import re
import sys
import subprocess
from pathlib import Path


def _has_english_subs(url: str) -> bool:
    """Return True if the video has English subtitles (manual or auto-generated)."""
    result = subprocess.run(
        ["yt-dlp", "--list-subs", "--skip-download", url],
        capture_output=True,
        text=True,
    )
    # yt-dlp lists subtitles as lines starting with the language code.
    # We match "en" at the start of a line (possibly with leading whitespace),
    # covering en, en-US, en-GB, etc.
    return bool(re.search(r"^\s*en\b", result.stdout, re.MULTILINE))


def _download_srt(url: str, output_dir: Path) -> Path:
    """Download English subtitles and convert to SRT. Returns path to .en.srt file."""
    subprocess.run(
        [
            "yt-dlp",
            "--write-sub",        # manual subtitles
            "--write-auto-sub",   # auto-generated (English only via --sub-lang)
            "--sub-lang", "en",   # English only — rejects all other languages
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
    return srt_files[-1]  # most recently modified


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: yt-download <youtube_url> <output_dir>",
            file=sys.stderr,
        )
        sys.exit(2)

    url = sys.argv[1]
    output_dir = Path(sys.argv[2]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not _has_english_subs(url):
        print(
            "ERROR: This video has no English subtitles (neither manual nor auto-generated).\n"
            "Only English subtitles are supported. Please choose a video with English subtitles.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        srt_path = _download_srt(url, output_dir)
        print(str(srt_path))
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: yt-dlp failed:\n{exc.stderr}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
