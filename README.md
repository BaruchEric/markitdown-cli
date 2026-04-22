# mdc — personal markitdown CLI

A thin wrapper around [Microsoft markitdown](https://github.com/microsoft/markitdown) that adds batch folder conversion, output routing, skip-if-exists, OCR via OpenAI gpt-4o-mini, and audio transcription via OpenAI Whisper. Installed globally with `uv tool install`.

## Install

```bash
uv tool install /Users/ericbaruch/Arik/dev/markitdown
```

This exposes a `mdc` command on your `PATH`.

### Reinstalling after local changes

`uv tool install --force .` reuses cached builds and can silently ship stale code. To pick up changes:

```bash
uv tool uninstall markitdown-cli && uv tool install --reinstall --no-cache .
```

## Usage

Single file:
```bash
mdc report.pdf
# writes report.pdf.md next to source
```

Folder (recursive, mirrors tree):
```bash
mdc ./docs
# writes ./docs.md/ as a sibling
```

Explicit output:
```bash
mdc report.pdf -o /tmp/out.md
mdc ./docs -o /tmp/docs-md
```

Force re-conversion:
```bash
mdc report.pdf --force
```

OCR (image description via gpt-4o-mini):
```bash
mdc photo.png --ocr
```

Audio transcription (Whisper API):
```bash
mdc recording.mp3 --audio
```

## API keys

`--ocr` and `--audio` both need `OPENAI_API_KEY` in `/Users/ericbaruch/Arik/dev/.env`. Plain conversions do not need any API key.

## Supported formats

PDF, DOCX, PPTX, XLSX, XLS, HTML, HTM, CSV, JSON, XML, EPUB, ZIP, MSG, TXT, RTF, ODT, JPG, JPEG, PNG, GIF, BMP, TIFF, MP3, WAV, M4A, FLAC.

## Uninstall

```bash
uv tool uninstall markitdown-cli
```

## Claude skill

A companion skill at `~/.claude/skills/markitdown/SKILL.md` lets Claude Code call `mdc` when it encounters a non-text file.
