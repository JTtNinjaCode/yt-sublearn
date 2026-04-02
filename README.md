# yt-sublearn

A Claude Code plugin for English learning through YouTube videos.

Given a YouTube URL, it:
1. Downloads English subtitles (manual or auto-generated) via yt-dlp
2. Translates them into a bilingual EN/ZH file with timestamps using a haiku subagent
3. Generates a concise Traditional Chinese summary of the video (abstract-style)

## Requirements

- [Claude Code](https://claude.ai/code)
- [uv](https://docs.astral.sh/uv/)

## Installation

In Claude Code, run these two commands:
```
/plugin marketplace add JTtNinjaCode/yt-sublearn
/plugin install yt-sublearn@JTtNinjaCode
```

No other setup required. Dependencies (yt-dlp) are downloaded automatically on first use.

## Usage

```
/yt-sublearn <youtube_url> [output_dir]
```

| Argument | Description |
|---|---|
| `youtube_url` | Required. The YouTube video URL. |
| `output_dir` | Optional. Where to save output files. Defaults to `./output/`. |

**Example:**

```
/yt-sublearn https://www.youtube.com/watch?v=dQw4w9WgXcQ ./output/
```

**Output files (saved to `output_dir`):**

- `<video_title>.en.srt` — original English subtitle file
- `<video_title>_bilingual.txt` — bilingual EN/ZH translation with timestamps

**Error handling:**

If the video has no English subtitles, the skill stops with a clear error message. Subtitles in other languages are never downloaded.

## How It Works

```
/yt-sublearn
    │
    ├─ 1. uv run skills/yt-sublearn/scripts/download.py   (PEP 723, auto-installs yt-dlp)
    │       └─ validates English subs exist → downloads .en.srt
    │
    ├─ 2. haiku subagent                                    (lightweight, token-efficient)
    │       └─ translates SRT → bilingual .txt with [HH:MM:SS] timestamps
    │
    └─ 3. main model
            └─ reads bilingual file → writes Traditional Chinese summary
```

The download script uses [PEP 723](https://peps.python.org/pep-0723/) inline script metadata, so `uv run` manages the virtual environment automatically (cached at `~/.cache/uv/`).

## Project Structure

```
.
├── .claude-plugin/plugin.json              — plugin metadata
├── skills/
│   └── yt-sublearn/
│       ├── SKILL.md                        — /yt-sublearn skill definition
│       └── scripts/
│           └── download.py                 — PEP 723 standalone script (yt-dlp)
└── agents/
    └── yt-subtitle-translator.md           — haiku translator subagent
```

## License

MIT — see [LICENSE](LICENSE).
