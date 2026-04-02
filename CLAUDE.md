# yt-translate

A Claude Code plugin that downloads YouTube English subtitles, translates them into bilingual EN/ZH format, and generates a video summary for English learning.

## Setup

```bash
# 1. Install the CLI tool globally
uv tool install .

# 2. Register the plugin in Claude Code
#    Add to ~/.claude/plugins/installed_plugins.json:
#    "yt-translate@local": [{
#      "scope": "user",
#      "installPath": "/absolute/path/to/this/plugin/ directory",
#      "version": "0.1.0",
#      "installedAt": "<ISO timestamp>"
#    }]
#
#    Add to ~/.claude/settings.json enabledPlugins:
#    "yt-translate@local": true

# 3. Restart Claude Code
```

## Usage

```
/yt-translate <youtube_url> [output_dir]
```

- `output_dir` defaults to `./output/`
- Only English subtitles are supported; videos without English subs will show an error

## Project Structure

```
src/yt_translate/download.py   — CLI: validates & downloads English SRT via yt-dlp
plugin/skills/yt-translate/    — /yt-translate skill definition
plugin/agents/                 — yt-subtitle-translator haiku subagent
```

## Development

```bash
uv sync          # install deps into .venv
uv tool install . --reinstall   # update the global yt-download after code changes
```
