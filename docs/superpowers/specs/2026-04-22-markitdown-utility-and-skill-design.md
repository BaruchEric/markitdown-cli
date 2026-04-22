# Markitdown Conversion Utility + Claude Skill — Design

**Date:** 2026-04-22
**Status:** Approved (pending written-spec review)
**Owner:** ericbaruch

## 1. Goal

Give the user a fast, reliable way to convert arbitrary documents (PDF, DOCX, PPTX, XLSX, HTML, EPUB, images, audio) to Markdown from the command line, and make that capability available to Claude Code via a skill so the agent can read non-text files it encounters during tasks.

The primary use case is **personal document conversion**. The skill is a convenience layer, not the product.

## 2. Non-goals

- No RAG / chunking / embedding features.
- No YAML frontmatter or custom output post-processing.
- No watch mode.
- No provider-switching across LLM vendors.
- No reimplementation of markitdown's format parsers — we wrap upstream.

## 3. Architecture

### 3.1 Repository layout

```
markitdown/
├── pyproject.toml
├── .python-version
├── src/markitdown_cli/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry (argparse)
│   ├── convert.py           # single-file + batch orchestration
│   ├── config.py            # .env loading + LLM client construction
│   └── formats.py           # supported extensions list
├── tests/
│   └── test_convert.py
└── README.md
```

### 3.2 Runtime

- Python 3.11+, managed via `uv`.
- Depends on `markitdown[all]` (upstream), `python-dotenv`, `openai`. CLI parsing via stdlib `argparse` to avoid adding a dep.
- Installed globally with `uv tool install .` → exposes the `mdc` command on `PATH`.

### 3.3 Components and boundaries

| Module | Purpose | Depends on |
|---|---|---|
| `__main__.py` | Parse flags, dispatch to `convert`. No business logic. | `convert`, `config` |
| `convert.py` | Walks inputs, decides per-file output path, calls upstream `MarkItDown`, handles skip-if-exists, aggregates errors. | `markitdown`, `formats`, `config` |
| `config.py` | Loads `/Users/ericbaruch/Arik/dev/.env`, constructs OpenAI client on demand, produces clear error messages when keys are missing. | `python-dotenv`, `openai` |
| `formats.py` | Single constant: the set of supported extensions. Used for the directory walker to decide what to touch. | — |

Each module is independently testable. `convert.py` is the only one with I/O logic worth unit-testing.

## 4. CLI specification

### 4.1 Command

```
mdc <input> [-o <output>] [--force] [--ocr] [--audio] [--verbose]
```

### 4.2 Argument semantics

- `<input>` — required. A file or directory.
- `-o, --output <path>` — optional.
  - If `<input>` is a file: treat `-o` as the output file path.
  - If `<input>` is a directory: treat `-o` as the output directory.
  - If omitted and `<input>` is a file: write `<input>.md` next to the source (e.g. `report.pdf` → `report.pdf.md`).
  - If omitted and `<input>` is a directory: write to `<input>.md/` as a sibling (e.g. `./docs/` → `./docs.md/`).
- `--force` — re-convert even if the target `.md` exists and is newer than the source.
- `--ocr` — enable LLM-based image description via OpenAI gpt-4o-mini.
- `--audio` — enable OpenAI Whisper API transcription for audio files.
- `--verbose` — print one log line per file; default is a single progress indicator.

### 4.3 Batch rules

- Directory walk is recursive.
- Output tree mirrors the input tree structure.
- Files with unsupported extensions are silently skipped; counted in the summary.
- A single file's failure does not abort the batch. All errors are collected and printed at the end with the source file path.

### 4.4 Skip-if-exists

For each input file, compute the target `.md` path. If the target exists **and** `mtime(target) >= mtime(source)`, skip. `--force` bypasses this check.

### 4.5 Exit summary

After a run, always print:

```
Converted N • Skipped N (up-to-date) • Unsupported N • Errors N
```

Followed by a list of errors (path + one-line reason) if any.

### 4.6 Exit codes

- `0` — all inputs either converted, skipped as up-to-date, or skipped as unsupported.
- `1` — at least one file errored during conversion.
- `2` — invocation error (missing input, bad flag, missing required API key for `--ocr`/`--audio`).

### 4.7 Supported extensions

`.pdf .docx .pptx .xlsx .xls .html .htm .csv .json .xml .epub .zip .msg .txt .rtf .odt .jpg .jpeg .png .gif .bmp .tiff .mp3 .wav .m4a .flac`

## 5. Config and secrets

### 5.1 Env loading

- Path: `/Users/ericbaruch/Arik/dev/.env` (hardcoded constant in `config.py`).
- Loaded lazily on first `--ocr`/`--audio` invocation. Plain conversions never touch the file.
- Uses `python-dotenv` to parse. Quoted values are handled by the library.

### 5.2 LLM client (OCR path)

- Provider: OpenAI.
- Key source: `OPENAI_API_KEY` from the `.env`.
- Model: `gpt-4o-mini`.
- Wiring: passed to upstream `MarkItDown(llm_client=openai_client, llm_model="gpt-4o-mini")`.

### 5.3 Audio transcription

- Provider: OpenAI Whisper API (`whisper-1`).
- Key source: same `OPENAI_API_KEY`.
- Wiring: subclass or replace upstream's `AudioConverter` so its transcription step calls `openai.audio.transcriptions.create(model="whisper-1", file=...)` instead of the default local `speech_recognition` backend. Exact subclassing mechanism to be validated against upstream's current API during implementation; if upstream's converter is not cleanly overridable, fall back to: detect audio by extension in our own walker, transcribe via the OpenAI client, and hand the resulting text to `MarkItDown` as synthetic markdown. Either way, no local whisper install is required.

### 5.4 Missing-key behavior

When a required key is absent and the corresponding flag is set, exit with code 2 and this message shape:

```
mdc: --ocr requires OPENAI_API_KEY in /Users/ericbaruch/Arik/dev/.env
```

Unrelated keys in the `.env` (GEMINI, GROQ, OPENROUTER, etc.) are ignored.

## 6. Claude skill

### 6.1 Location

`~/.claude/skills/markitdown/SKILL.md`

### 6.2 Frontmatter

```yaml
---
name: markitdown
description: Convert PDFs, Office docs (DOCX/PPTX/XLSX), HTML, EPUB, images, and audio to Markdown via the `mdc` CLI. Use when you encounter a non-text file the user referenced, when reading a `.pdf`/`.docx`/`.pptx`/`.xlsx` would fail the normal Read tool, or when the user asks to "extract text from" / "convert to markdown" / "read this PDF".
---
```

### 6.3 Body (outline)

Keep it tight (~40–60 lines):

1. **When to use:** list of triggers (user referenced a binary doc; Read tool would fail on a `.pdf`/`.docx`/etc.; user said "convert" or "extract text").
2. **Preflight:** `command -v mdc`. If missing → tell the user to run `uv tool install /Users/ericbaruch/Arik/dev/markitdown` and stop.
3. **Usage patterns:**
   - Single file: `mdc <abs-path>` → Read the resulting `<abs-path>.md`.
   - Folder: `mdc <abs-dir>` → glob `<abs-dir>.md/**/*.md` and Read what's relevant.
   - OCR/audio: add `--ocr` or `--audio`, but only after confirming with the user that they're OK with API cost.
4. **Constraints:**
   - Never cat the whole output into context for large docs — use Read with offsets.
   - Skip-if-exists is default; pass `--force` only when asked to re-convert.
   - Don't use `--ocr` for regular PDFs — it's only for image files.

### 6.4 What the skill does NOT do

- No inline Python execution.
- No file cleanup.
- No chunking or summarization.

## 7. Testing

- `tests/test_convert.py` covers:
  - Single-file conversion of a tiny `.txt` and `.csv` (no API required).
  - Directory walk: mixed supported + unsupported files, verifies output tree.
  - Skip-if-exists: second run converts zero files.
  - `--force`: second run re-converts.
  - Error aggregation: malformed file does not abort the batch.
- OCR/audio paths are NOT unit-tested (would require API calls). Covered by manual smoke tests documented in README.

## 8. README contents

- One-paragraph "what this is"
- Install instructions: `uv tool install .`
- Five usage examples: single file, folder, `-o`, `--force`, `--ocr`
- Note on the `.env` path and which key does what
- How to uninstall: `uv tool uninstall markitdown-cli`

## 9. Implementation order

1. Scaffold `pyproject.toml` + `src/markitdown_cli/` skeleton.
2. `formats.py` constant.
3. `convert.py` single-file path (no batching, no OCR).
4. `__main__.py` argparse.
5. Batch + skip-if-exists in `convert.py`.
6. `config.py` + wire `--ocr` and `--audio`.
7. Tests.
8. `uv tool install .` and smoke test.
9. Write skill at `~/.claude/skills/markitdown/SKILL.md`.
10. README.

## 10. Open questions

None — all resolved during brainstorming.
