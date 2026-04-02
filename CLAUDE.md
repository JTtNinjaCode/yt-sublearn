# yt-translate

A Claude Code plugin that downloads YouTube English subtitles, translates them into bilingual EN/ZH format using a haiku subagent, and generates an abstract-style summary for English learning.

## Setup

```bash
# 1. Register the plugin in Claude Code
#    Add to ~/.claude/plugins/installed_plugins.json:
#
#    "yt-translate@local": [{
#      "scope": "user",
#      "installPath": "/absolute/path/to/this/plugin/ directory",
#      "version": "0.1.0",
#      "installedAt": "<ISO timestamp>"
#    }]
#
#    Add to ~/.claude/settings.json > enabledPlugins:
#    "yt-translate@local": true

# 2. Restart Claude Code
```

No other setup required. Dependencies (yt-dlp) are downloaded automatically on first use via `uv run`.

## Usage

```
/yt-translate <youtube_url> [output_dir]
```

- `output_dir` defaults to `./output/`
- Only English subtitles are supported; videos without English subs show an error

## Project Structure

```
plugin/
├── .claude-plugin/plugin.json          — plugin metadata
├── scripts/download.py                 — PEP 723 standalone script (yt-dlp)
├── skills/yt-translate/SKILL.md        — /yt-translate skill definition
└── agents/yt-subtitle-translator.md    — haiku translator subagent
```

`download.py` uses PEP 723 inline script metadata — `uv run` handles the venv automatically, cached at `~/.cache/uv/`.
