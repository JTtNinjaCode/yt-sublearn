# yt-sublearn

A Claude Code plugin for English learning via YouTube subtitles.

## Install

In Claude Code:
```
/plugin marketplace add JTtNinjaCode/yt-sublearn
/plugin install yt-sublearn@JTtNinjaCode
```

## Usage

```
/yt-sublearn <youtube_url> [output_dir]
```

`output_dir` defaults to `./output/`. Only English subtitles are supported.

## Structure

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

`download.py` uses PEP 723 inline script metadata — `uv run` handles the venv automatically, cached at `~/.cache/uv/`.
