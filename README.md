# JTtNinjaCode Claude Plugins

A Claude Code plugin marketplace for productivity and learning tools.

## Installation

Add this marketplace in Claude Code:
```
/plugin marketplace add JTtNinjaCode/yt-sublearn
```

Then install individual plugins:
```
/plugin install yt-sublearn@JTtNinjaCode
```

## Plugins

### yt-sublearn

Learn English through YouTube videos. Downloads English subtitles, translates them into a bilingual EN/ZH file with timestamps using a haiku subagent, and generates an abstract-style summary.

**Usage:**
```
/yt-sublearn <youtube_url> [output_dir]
```

**Output files (saved to `output_dir`, defaults to `./output/`):**
- `<video_title>.en.srt` — original English subtitle file
- `<video_title>_bilingual.txt` — bilingual EN/ZH translation with timestamps

**How it works:**
```
/yt-sublearn
    │
    ├─ 1. uv run download.py          (PEP 723, auto-installs yt-dlp)
    │       └─ validates English subs exist → downloads .en.srt
    │
    ├─ 2. haiku subagent              (lightweight, token-efficient)
    │       └─ translates SRT → bilingual .txt with [HH:MM:SS] timestamps
    │
    └─ 3. main model
            └─ reads bilingual file → writes Traditional Chinese summary
```

## Requirements

- [Claude Code](https://claude.ai/code)
- [uv](https://docs.astral.sh/uv/)

## Project Structure

```
.
├── .claude-plugin/
│   └── marketplace.json              — marketplace definition
└── plugins/
    └── yt-sublearn/
        ├── .claude-plugin/
        │   └── plugin.json           — plugin metadata
        ├── skills/
        │   └── yt-sublearn/
        │       ├── SKILL.md          — /yt-sublearn skill definition
        │       └── scripts/
        │           └── download.py   — PEP 723 standalone script (yt-dlp)
        └── agents/
            └── yt-subtitle-translator.md  — haiku translator subagent
```

## License

MIT — see [LICENSE](LICENSE).
