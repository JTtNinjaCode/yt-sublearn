# JTtNinjaCode Claude Plugins

A Claude Code plugin marketplace. Add new plugins under `plugins/<plugin-name>/`.

## Install (in Claude Code)

```
/plugin marketplace add JTtNinjaCode/yt-sublearn
/plugin install yt-sublearn@JTtNinjaCode
```

## Adding a New Plugin

1. Create `plugins/<plugin-name>/` with its own `.claude-plugin/plugin.json`
2. Add skills to `plugins/<plugin-name>/skills/<plugin-name>/`
3. Add agents to `plugins/<plugin-name>/agents/`
4. Register in `.claude-plugin/marketplace.json`

## Structure

```
.
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    └── yt-sublearn/
        ├── .claude-plugin/plugin.json
        ├── skills/yt-sublearn/
        │   ├── SKILL.md
        │   └── scripts/download.py      — PEP 723 standalone script (yt-dlp)
        └── agents/yt-subtitle-translator.md
```
