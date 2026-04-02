# yt-translate

A Claude Code plugin for English learning through YouTube videos.

Given a YouTube URL, it:
1. Downloads English subtitles (manual or auto-generated) via yt-dlp
2. Translates them into a bilingual EN/ZH file with timestamps using a haiku subagent
3. Generates a concise Traditional Chinese summary of the video (abstract-style)

## Requirements

- [Claude Code](https://claude.ai/code)
- [uv](https://docs.astral.sh/uv/) — for running the download script

## Setup

**1. Clone the repo**

```bash
git clone <repo_url>
cd yt-translate
```

**2. Register the plugin in Claude Code**

Add to `~/.claude/plugins/installed_plugins.json`:

```json
"yt-translate@local": [{
  "scope": "user",
  "installPath": "/absolute/path/to/yt-translate/plugin",
  "version": "0.1.0",
  "installedAt": "2026-01-01T00:00:00.000Z"
}]
```

Add to `~/.claude/settings.json` under `enabledPlugins`:

```json
"yt-translate@local": true
```

**3. Restart Claude Code**

No other setup needed — dependencies are downloaded automatically on first use.

## Usage

```
/yt-translate <youtube_url> [output_dir]
```

| Argument | Description |
|---|---|
| `youtube_url` | Required. The YouTube video URL. |
| `output_dir` | Optional. Where to save output files. Defaults to `./output/`. |

**Example:**

```
/yt-translate https://www.youtube.com/watch?v=dQw4w9WgXcQ ./output/
```

**Output files (saved to `output_dir`):**

- `<video_title>.en.srt` — original English subtitle file
- `<video_title>_bilingual.txt` — bilingual EN/ZH translation with timestamps

**Error handling:**

If the video has no English subtitles, the skill stops with a clear error message. Subtitles in other languages are never downloaded.

## How It Works

```
/yt-translate
    │
    ├─ 1. uv run plugin/scripts/download.py   (PEP 723 script, auto-installs yt-dlp)
    │       └─ validates English subs exist → downloads .en.srt
    │
    ├─ 2. haiku subagent                       (lightweight, token-efficient)
    │       └─ translates SRT → bilingual .txt with [HH:MM:SS] timestamps
    │
    └─ 3. main model
            └─ reads bilingual file → writes Traditional Chinese summary
```

The download script uses [PEP 723](https://peps.python.org/pep-0723/) inline script metadata, so `uv run` manages the virtual environment automatically (cached at `~/.cache/uv/`).

## Project Structure

```
plugin/
├── .claude-plugin/plugin.json          — plugin metadata
├── scripts/download.py                 — PEP 723 standalone script (yt-dlp)
├── skills/yt-translate/SKILL.md        — /yt-translate skill definition
└── agents/yt-subtitle-translator.md    — haiku translator subagent
```
