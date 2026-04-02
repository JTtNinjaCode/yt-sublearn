---
name: yt_translate
description: Download English subtitles from a YouTube video, split them into 50-entry chunks, translate the chunks in parallel with a minimal subtitle subagent, merge the bilingual outputs, and generate a concise Traditional Chinese summary.
---

You orchestrate a low-latency YouTube subtitle translation workflow.

## Invocation

The user calls this skill as:

```bash
/yt_translate <youtube_url> [output_dir]
```

- `<youtube_url>`: required
- `[output_dir]`: optional, defaults to `./output/`

## Design Goals

- Keep main-agent context small
- Push mechanical work into Python scripts
- Keep subtitle subagents minimal
- Parallelize translation across chunk files
- Avoid passing raw full SRT content between agents

## Workflow

### Step 1 — Download, normalize, and split subtitles

Run:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/download.py" <youtube_url> <output_dir>
```

Behavior:
- Downloads English subtitles with `yt-dlp`
- Cleans rolling auto-caption duplication
- Merges fragmented subtitles into sentence-style entries
- Splits the normalized SRT into multiple chunk files, each containing **50 subtitle entries**
- Writes a manifest JSON file describing all generated paths

Exit handling:
- If exit code is **1**, report that no English subtitles are available and stop.
- If exit code is **2**, report stderr and stop.
- If exit code is **0**, stdout is the absolute path to the manifest JSON file.

### Step 2 — Read only the manifest

Read the manifest JSON file produced by `download.py`.

The manifest contains at least:
- source SRT path
- chunk directory
- ordered chunk file paths
- final bilingual output path
- chunk bilingual output paths
- summary source path

Do **not** read the full source SRT in the main agent.

### Step 3 — Translate chunks in parallel with subagents

For each chunk listed in the manifest, spawn a `yt_translate:yt-subtitle-translator` subagent.

Pass each subagent only:
- the absolute input chunk path
- the absolute output bilingual chunk path

Do not inline subtitle content into the prompt.
Do not ask the subagent to summarize.
Do not give the subagent any extra context.

All chunk translations should be launched in parallel whenever the runtime allows it.

### Step 4 — Merge bilingual chunk outputs

After all subtitle subagents finish, run:

```bash
uv run "${CLAUDE_SKILL_DIR}/scripts/merge.py" <manifest_json_path>
```

Behavior:
- Verifies all translated chunk files exist
- Merges chunk outputs in chunk index order
- Writes the final bilingual file
- Writes a smaller `summary_source.txt` for summary generation

If merge fails, show the error and stop.

### Step 5 — Generate the video summary

Read only the generated `summary_source.txt`.

Using that file, write a concise **150–250 word Traditional Chinese summary** that acts like:
- abstract
- introduction
- conclusion

The summary should cover:
- main topic
- purpose
- major concepts / tools / technologies
- content flow
- final takeaway

Do not read every chunk file again unless merge output is missing.

### Step 6 — Present results

Return:
1. The Traditional Chinese summary
2. The final bilingual file path
3. The chunk directory path

## Important Rules

- The main agent should not ingest raw full-subtitle content unless recovery is absolutely necessary.
- The main agent is an orchestrator, not a translator.
- All heavy file transformation should stay in Python scripts.
- Summary input must come from `summary_source.txt`, not by concatenating every chunk in the prompt.
