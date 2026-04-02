---
name: yt-sublearn
description: Download English subtitles from a YouTube video, translate them into a bilingual EN/ZH file with timestamps, and generate a concise abstract-style summary of the video. Use this skill when the user wants to study English through YouTube content.
---

You help the user learn English by processing YouTube videos into bilingual study materials.

## Invocation

The user calls this skill as:
```
/yt-sublearn <youtube_url> [output_dir]
```

- `<youtube_url>` — required, the YouTube video URL
- `[output_dir]` — optional, defaults to `./output/`

---

## Workflow

### Step 1 — Download English Subtitles

Run:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/download.py" <youtube_url> <output_dir>
```

- `uv run` automatically installs yt-dlp into an isolated cache and runs the script — no manual setup needed.
- If the exit code is **not 0**: display the error message from stderr to the user and **stop**.
- If exit code is **0**: stdout contains the absolute path to the downloaded `.en.srt` file.

### Step 2 — Read the Subtitle File

Read the full content of the `.en.srt` file.

Compute the bilingual output path by replacing `.en.srt` with `_bilingual.txt` in the same directory.

### Step 3 — Translate via Haiku Subagent

Spawn a `yt-sublearn:yt-subtitle-translator` Agent to perform the translation. Pass it a prompt containing:

1. The complete raw SRT file content (verbatim, inside a code block)
2. The absolute bilingual output file path

The subagent will translate every subtitle entry to Traditional Chinese and write the bilingual file.

### Step 4 — Generate Video Summary

After the subagent completes, read the bilingual output file.

Write a concise summary of **150–250 words** that plays the role of a paper's **abstract + introduction + conclusion**. The summary must tell the user:

- **Main topic**: What is this video fundamentally about?
- **Purpose**: What problem does it solve or what concept does it teach?
- **Key concepts & technologies**: List the major technical terms, tools, or ideas covered
- **Content structure**: How does the video progress (overview → demo → conclusion, etc.)
- **Takeaway**: What will the viewer know or be able to do after watching?

Write the summary in **Traditional Chinese (繁體中文)**, since it serves as the user's pre-watch orientation.

### Step 5 — Present Results

Display to the user:
1. The summary (formatted clearly)
2. A single line showing the bilingual file path
