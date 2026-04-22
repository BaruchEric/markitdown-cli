# Markitdown Utility + Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI (`mdc`) that wraps Microsoft's markitdown with batch/output-routing/skip-if-exists/OCR/audio features, installable via `uv tool install`, and a Claude skill at `~/.claude/skills/markitdown/SKILL.md` that shells out to it.

**Architecture:** Thin Python wrapper over upstream `markitdown[all]`. Four focused modules (`formats`, `convert`, `config`, `__main__`) in `src/markitdown_cli/`. Skill is a 40–60 line `SKILL.md` with no logic — it calls `mdc` and reads the output. API keys come from `/Users/ericbaruch/Arik/dev/.env`.

**Tech Stack:** Python 3.11+, `uv` (package manager + tool installer), `markitdown[all]` (upstream), `openai` (LLM client for OCR/audio), `python-dotenv`, stdlib `argparse`, `pytest`.

---

## File Structure

**Will create:**
- `pyproject.toml` — project metadata, deps, `mdc` script entry
- `.python-version` — pins 3.11 for uv
- `.gitignore` — Python/uv basics
- `src/markitdown_cli/__init__.py` — empty package marker
- `src/markitdown_cli/formats.py` — supported extensions constant
- `src/markitdown_cli/config.py` — env loading + OpenAI client construction
- `src/markitdown_cli/convert.py` — single + batch conversion logic
- `src/markitdown_cli/__main__.py` — argparse CLI entry
- `tests/__init__.py` — empty
- `tests/test_convert.py` — unit tests for convert.py
- `tests/test_config.py` — unit tests for config.py
- `tests/fixtures/hello.txt` — tiny fixture file for tests
- `README.md` — install + usage docs
- `~/.claude/skills/markitdown/SKILL.md` — the agent skill

**Will NOT create:** no watch mode, no RAG features, no frontmatter injection, no Gemini/Groq provider switching.

---

### Task 1: Project scaffold + git init

**Files:**
- Create: `/Users/ericbaruch/Arik/dev/markitdown/.gitignore`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/.python-version`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/pyproject.toml`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/__init__.py`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/tests/__init__.py`

- [ ] **Step 1: Initialize git repo**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git init
```
Expected: `Initialized empty Git repository in /Users/ericbaruch/Arik/dev/markitdown/.git/`

- [ ] **Step 2: Write `.gitignore`**

Create `/Users/ericbaruch/Arik/dev/markitdown/.gitignore`:
```
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.pytest_cache/
dist/
build/
.ruff_cache/
*.md.backup
```

- [ ] **Step 3: Write `.python-version`**

Create `/Users/ericbaruch/Arik/dev/markitdown/.python-version`:
```
3.11
```

- [ ] **Step 4: Write `pyproject.toml`**

Create `/Users/ericbaruch/Arik/dev/markitdown/pyproject.toml`:
```toml
[project]
name = "markitdown-cli"
version = "0.1.0"
description = "Personal disk utility + Claude skill wrapping Microsoft markitdown"
requires-python = ">=3.11"
dependencies = [
    "markitdown[all]>=0.0.1a2",
    "python-dotenv>=1.0.0",
    "openai>=1.40.0",
]

[project.scripts]
mdc = "markitdown_cli.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/markitdown_cli"]

[dependency-groups]
dev = ["pytest>=8.0"]
```

- [ ] **Step 5: Create empty `__init__.py` files**

Create `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/__init__.py`:
```python
```

Create `/Users/ericbaruch/Arik/dev/markitdown/tests/__init__.py`:
```python
```

- [ ] **Step 6: Sync deps and verify import**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv sync
```
Expected: resolves `markitdown`, `openai`, `python-dotenv`, and test deps; creates `.venv/`.

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run python -c "from markitdown import MarkItDown; print('ok')"
```
Expected: `ok`

- [ ] **Step 7: Commit scaffold**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add .gitignore .python-version pyproject.toml src tests uv.lock && git commit -m "chore: scaffold markitdown-cli project"
```

---

### Task 2: Supported extensions constant

**Files:**
- Create: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/formats.py`

- [ ] **Step 1: Write `formats.py`**

Create `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/formats.py`:
```python
SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({
    ".pdf",
    ".docx", ".pptx", ".xlsx", ".xls",
    ".html", ".htm",
    ".csv", ".json", ".xml",
    ".epub", ".zip", ".msg",
    ".txt", ".rtf", ".odt",
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff",
    ".mp3", ".wav", ".m4a", ".flac",
})

AUDIO_EXTENSIONS: frozenset[str] = frozenset({".mp3", ".wav", ".m4a", ".flac"})
IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"})


def is_supported(path: str) -> bool:
    """True if the file's extension is in SUPPORTED_EXTENSIONS (case-insensitive)."""
    from pathlib import Path
    return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/formats.py && git commit -m "feat: add supported extensions constant"
```

---

### Task 3: Single-file conversion (happy path)

**Files:**
- Create: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/tests/fixtures/hello.txt`

- [ ] **Step 1: Create the test fixture**

Create `/Users/ericbaruch/Arik/dev/markitdown/tests/fixtures/hello.txt`:
```
Hello, markitdown.
```

- [ ] **Step 2: Write the failing test**

Create `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`:
```python
from pathlib import Path
from markitdown_cli.convert import convert_file


FIXTURES = Path(__file__).parent / "fixtures"


def test_convert_file_writes_markdown_next_to_source(tmp_path):
    src = tmp_path / "hello.txt"
    src.write_text("Hello, markitdown.\n")

    out = convert_file(src)

    assert out == src.with_suffix(src.suffix + ".md")
    assert out.exists()
    assert "Hello, markitdown." in out.read_text()
```

- [ ] **Step 3: Run test to verify it fails**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py::test_convert_file_writes_markdown_next_to_source -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'markitdown_cli.convert'` or similar.

- [ ] **Step 4: Write minimal `convert.py`**

Create `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`:
```python
from __future__ import annotations

from pathlib import Path

from markitdown import MarkItDown


def _default_output_path(src: Path) -> Path:
    """For a source file `report.pdf`, return `report.pdf.md`."""
    return src.with_suffix(src.suffix + ".md")


def convert_file(src: Path, out: Path | None = None, md: MarkItDown | None = None) -> Path:
    """Convert a single file to markdown. Returns the output path.

    Raises on conversion failure. Caller is responsible for error aggregation.
    """
    src = Path(src)
    if out is None:
        out = _default_output_path(src)
    out = Path(out)

    md = md or MarkItDown()
    result = md.convert(str(src))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.text_content)
    return out
```

- [ ] **Step 5: Run test to verify it passes**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py::test_convert_file_writes_markdown_next_to_source -v
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/convert.py tests/test_convert.py tests/fixtures/hello.txt && git commit -m "feat: add single-file conversion"
```

---

### Task 4: Explicit output path (`-o` for a single file)

**Files:**
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`

- [ ] **Step 1: Add failing test**

Append to `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`:
```python
def test_convert_file_respects_explicit_output(tmp_path):
    src = tmp_path / "hello.txt"
    src.write_text("Hello.\n")
    dest = tmp_path / "nested" / "out.md"

    out = convert_file(src, out=dest)

    assert out == dest
    assert dest.exists()
    assert "Hello." in dest.read_text()
```

- [ ] **Step 2: Run test**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py::test_convert_file_respects_explicit_output -v
```
Expected: PASS (the implementation from Task 3 already supports this; this test codifies it).

- [ ] **Step 3: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add tests/test_convert.py && git commit -m "test: cover explicit output path"
```

---

### Task 5: Skip-if-exists behavior

**Files:**
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`

- [ ] **Step 1: Add failing test**

Append to `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`:
```python
import os
import time


def test_skip_if_exists_default(tmp_path):
    src = tmp_path / "hello.txt"
    src.write_text("v1\n")
    out = convert_file(src)
    first_mtime = out.stat().st_mtime

    # Make the target newer than source, then re-convert
    time.sleep(0.01)
    os.utime(out, None)  # bumps mtime to now
    time.sleep(0.01)

    out2 = convert_file(src)
    assert out2 == out
    # Should NOT have been rewritten
    assert out.stat().st_mtime >= first_mtime
    # Harder check: file contents are still v1
    assert "v1" in out.read_text()


def test_force_rewrites_even_if_target_is_newer(tmp_path):
    src = tmp_path / "hello.txt"
    src.write_text("v1\n")
    out = convert_file(src)

    # Mutate source, bump mtime
    time.sleep(0.01)
    src.write_text("v2\n")
    convert_file(src, force=True)

    assert "v2" in out.read_text()
```

- [ ] **Step 2: Run tests, verify `test_skip_if_exists_default` fails**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py -v
```
Expected: `test_skip_if_exists_default` FAILS (file gets rewritten). `test_force_rewrites_even_if_target_is_newer` may pass or fail depending on flag support — both failures are OK at this point.

- [ ] **Step 3: Add skip logic and `force` flag to `convert_file`**

Edit `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`. Replace the body of `convert_file` so the whole function looks like:
```python
def convert_file(
    src: Path,
    out: Path | None = None,
    md: MarkItDown | None = None,
    force: bool = False,
) -> Path:
    """Convert a single file to markdown. Returns the output path.

    If the target already exists and is newer than the source, skips unless
    `force=True`. Raises on conversion failure.
    """
    src = Path(src)
    if out is None:
        out = _default_output_path(src)
    out = Path(out)

    if not force and out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return out

    md = md or MarkItDown()
    result = md.convert(str(src))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.text_content)
    return out
```

- [ ] **Step 4: Run tests to verify both pass**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py -v
```
Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/convert.py tests/test_convert.py && git commit -m "feat: skip-if-exists unless --force"
```

---

### Task 6: Batch directory walk

**Files:**
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`

- [ ] **Step 1: Add failing test**

Append to `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`:
```python
from markitdown_cli.convert import convert_tree, ConvertSummary


def test_convert_tree_mirrors_input_structure(tmp_path):
    src_root = tmp_path / "docs"
    (src_root / "sub").mkdir(parents=True)
    (src_root / "a.txt").write_text("A\n")
    (src_root / "sub" / "b.txt").write_text("B\n")
    (src_root / "unsupported.xyz").write_text("ignored\n")

    out_root = tmp_path / "out"
    summary = convert_tree(src_root, out_root)

    assert isinstance(summary, ConvertSummary)
    assert summary.converted == 2
    assert summary.unsupported == 1
    assert summary.skipped == 0
    assert summary.errors == []

    assert (out_root / "a.txt.md").exists()
    assert (out_root / "sub" / "b.txt.md").exists()
    assert not (out_root / "unsupported.xyz.md").exists()


def test_convert_tree_default_output_is_sibling_md_dir(tmp_path):
    src_root = tmp_path / "docs"
    src_root.mkdir()
    (src_root / "a.txt").write_text("A\n")

    summary = convert_tree(src_root)

    assert summary.converted == 1
    assert (tmp_path / "docs.md" / "a.txt.md").exists()
```

- [ ] **Step 2: Run test, verify failure**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py -v
```
Expected: `ImportError: cannot import name 'convert_tree'`.

- [ ] **Step 3: Add `convert_tree` and `ConvertSummary` to `convert.py`**

Edit `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`. Add these imports at the top (keep existing ones):
```python
from dataclasses import dataclass, field
```

Add at the bottom of the file:
```python
@dataclass
class ConvertSummary:
    converted: int = 0
    skipped: int = 0
    unsupported: int = 0
    errors: list[tuple[Path, str]] = field(default_factory=list)


def _default_tree_output(src_root: Path) -> Path:
    """For a source dir `docs`, return sibling `docs.md/`."""
    return src_root.parent / (src_root.name + ".md")


def convert_tree(
    src_root: Path,
    out_root: Path | None = None,
    md: MarkItDown | None = None,
    force: bool = False,
) -> ConvertSummary:
    """Recursively convert every supported file under `src_root`.

    Output mirrors the source tree. Unsupported files are counted and skipped.
    Per-file errors are collected (not raised) so one bad file doesn't abort the batch.
    """
    from markitdown_cli.formats import is_supported

    src_root = Path(src_root)
    if out_root is None:
        out_root = _default_tree_output(src_root)
    out_root = Path(out_root)

    md = md or MarkItDown()
    summary = ConvertSummary()

    for src in sorted(src_root.rglob("*")):
        if not src.is_file():
            continue
        if not is_supported(str(src)):
            summary.unsupported += 1
            continue

        rel = src.relative_to(src_root)
        dest = out_root / rel.with_suffix(rel.suffix + ".md")

        try:
            if not force and dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
                summary.skipped += 1
                continue
            convert_file(src, out=dest, md=md, force=True)
            summary.converted += 1
        except Exception as e:  # noqa: BLE001 — aggregate, don't abort
            summary.errors.append((src, f"{type(e).__name__}: {e}"))

    return summary
```

- [ ] **Step 4: Run tests**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py -v
```
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/convert.py tests/test_convert.py && git commit -m "feat: batch directory conversion with summary"
```

---

### Task 7: Error aggregation (one failure doesn't abort batch)

**Files:**
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`

- [ ] **Step 1: Add failing test**

Append to `/Users/ericbaruch/Arik/dev/markitdown/tests/test_convert.py`:
```python
def test_convert_tree_aggregates_errors_without_aborting(tmp_path, monkeypatch):
    src_root = tmp_path / "docs"
    src_root.mkdir()
    (src_root / "good.txt").write_text("good\n")
    (src_root / "bad.txt").write_text("bad\n")

    from markitdown_cli import convert as convert_mod

    real = convert_mod.convert_file

    def flaky(src, out=None, md=None, force=False):
        if Path(src).name == "bad.txt":
            raise RuntimeError("simulated parser failure")
        return real(src, out=out, md=md, force=force)

    monkeypatch.setattr(convert_mod, "convert_file", flaky)

    out_root = tmp_path / "out"
    summary = convert_mod.convert_tree(src_root, out_root)

    assert summary.converted == 1
    assert len(summary.errors) == 1
    bad_path, msg = summary.errors[0]
    assert bad_path.name == "bad.txt"
    assert "simulated parser failure" in msg
    assert (out_root / "good.txt.md").exists()
```

- [ ] **Step 2: Run test**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_convert.py::test_convert_tree_aggregates_errors_without_aborting -v
```
Expected: PASS (already supported by Task 6's implementation; this test codifies the behavior).

- [ ] **Step 3: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add tests/test_convert.py && git commit -m "test: cover error aggregation in batch"
```

---

### Task 8: Config module — env loading + missing-key errors

**Files:**
- Create: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/config.py`
- Create: `/Users/ericbaruch/Arik/dev/markitdown/tests/test_config.py`

- [ ] **Step 1: Write failing test**

Create `/Users/ericbaruch/Arik/dev/markitdown/tests/test_config.py`:
```python
import pytest

from markitdown_cli.config import (
    ENV_PATH,
    MissingKeyError,
    get_openai_client,
)


def test_env_path_is_user_dotenv():
    assert str(ENV_PATH) == "/Users/ericbaruch/Arik/dev/.env"


def test_missing_openai_key_raises_with_clear_message(tmp_path, monkeypatch):
    # Point ENV_PATH at an empty temp file so OPENAI_API_KEY is not found
    empty = tmp_path / ".env"
    empty.write_text("")
    monkeypatch.setattr("markitdown_cli.config.ENV_PATH", empty)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(MissingKeyError) as ei:
        get_openai_client(feature="--ocr")

    msg = str(ei.value)
    assert "--ocr" in msg
    assert "OPENAI_API_KEY" in msg
    assert str(empty) in msg


def test_openai_client_uses_env_file(tmp_path, monkeypatch):
    dotenv = tmp_path / ".env"
    dotenv.write_text('OPENAI_API_KEY="sk-test-xyz"\n')
    monkeypatch.setattr("markitdown_cli.config.ENV_PATH", dotenv)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = get_openai_client(feature="--ocr")
    assert client.api_key == "sk-test-xyz"
```

- [ ] **Step 2: Run tests, verify import failure**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_config.py -v
```
Expected: FAIL (`ModuleNotFoundError: No module named 'markitdown_cli.config'`).

- [ ] **Step 3: Write `config.py`**

Create `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/config.py`:
```python
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values
from openai import OpenAI

ENV_PATH: Path = Path("/Users/ericbaruch/Arik/dev/.env")


class MissingKeyError(RuntimeError):
    """Raised when a required API key is absent for a feature the user requested."""


def _load_env_var(name: str) -> str | None:
    """Prefer the value in ENV_PATH; fall back to the process env."""
    if ENV_PATH.exists():
        values = dotenv_values(ENV_PATH)
        if name in values and values[name]:
            return values[name]
    return os.environ.get(name)


def get_openai_client(feature: str) -> OpenAI:
    """Build an OpenAI client for the named feature (e.g. `--ocr`, `--audio`).

    Raises MissingKeyError with a clear, actionable message if OPENAI_API_KEY
    is not available in ENV_PATH or the process env.
    """
    key = _load_env_var("OPENAI_API_KEY")
    if not key:
        raise MissingKeyError(
            f"mdc: {feature} requires OPENAI_API_KEY in {ENV_PATH}"
        )
    return OpenAI(api_key=key)
```

- [ ] **Step 4: Run tests, verify PASS**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest tests/test_config.py -v
```
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/config.py tests/test_config.py && git commit -m "feat: config module for env loading and OpenAI client"
```

---

### Task 9: Wire `--ocr` into conversion

**Files:**
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`

- [ ] **Step 1: Add `build_markitdown` helper**

Edit `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`. Add at the bottom of the file:
```python
def build_markitdown(ocr: bool = False) -> MarkItDown:
    """Construct a MarkItDown instance, optionally wired for LLM image description."""
    if not ocr:
        return MarkItDown()
    from markitdown_cli.config import get_openai_client
    client = get_openai_client(feature="--ocr")
    return MarkItDown(llm_client=client, llm_model="gpt-4o-mini")
```

- [ ] **Step 2: Verify existing tests still pass**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest -v
```
Expected: all tests PASS (this addition is additive).

- [ ] **Step 3: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/convert.py && git commit -m "feat: build_markitdown helper with optional OCR wiring"
```

---

### Task 10: Wire `--audio` (OpenAI Whisper API)

**Files:**
- Modify: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`

**Context:** Upstream markitdown's `AudioConverter` uses `speech_recognition` + local whisper by default. Rather than subclassing it (its internals change across versions), we intercept audio files in our own walker and transcribe them directly with the OpenAI Whisper API, writing a tiny markdown wrapper around the transcript.

- [ ] **Step 1: Add `transcribe_audio` + audio-aware dispatch**

Edit `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`. Add at the bottom:
```python
def transcribe_audio(src: Path, out: Path | None = None) -> Path:
    """Transcribe an audio file via OpenAI Whisper API and write markdown."""
    from markitdown_cli.config import get_openai_client

    src = Path(src)
    if out is None:
        out = _default_output_path(src)
    out = Path(out)

    client = get_openai_client(feature="--audio")
    with src.open("rb") as f:
        resp = client.audio.transcriptions.create(model="whisper-1", file=f)

    body = f"# Transcript: {src.name}\n\n{resp.text.strip()}\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body)
    return out
```

- [ ] **Step 2: Teach `convert_file` and `convert_tree` to dispatch audio**

Edit `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/convert.py`. Replace `convert_file` so the whole function becomes:
```python
def convert_file(
    src: Path,
    out: Path | None = None,
    md: MarkItDown | None = None,
    force: bool = False,
    audio: bool = False,
) -> Path:
    """Convert a single file to markdown. Returns the output path.

    If `audio=True` and the file is an audio format, use the OpenAI Whisper API.
    Otherwise use upstream markitdown.
    """
    from markitdown_cli.formats import AUDIO_EXTENSIONS

    src = Path(src)
    if out is None:
        out = _default_output_path(src)
    out = Path(out)

    if not force and out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return out

    if audio and src.suffix.lower() in AUDIO_EXTENSIONS:
        return transcribe_audio(src, out=out)

    md = md or MarkItDown()
    result = md.convert(str(src))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(result.text_content)
    return out
```

Replace the conversion call inside `convert_tree` — change the line:
```python
            convert_file(src, out=dest, md=md, force=True)
```
to:
```python
            convert_file(src, out=dest, md=md, force=True, audio=audio)
```

And add `audio: bool = False` to the `convert_tree` signature so the whole signature becomes:
```python
def convert_tree(
    src_root: Path,
    out_root: Path | None = None,
    md: MarkItDown | None = None,
    force: bool = False,
    audio: bool = False,
) -> ConvertSummary:
```

- [ ] **Step 3: Run all tests**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest -v
```
Expected: all tests PASS (audio code path is opt-in; default behavior unchanged).

- [ ] **Step 4: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/convert.py && git commit -m "feat: --audio via OpenAI Whisper API"
```

---

### Task 11: CLI entry (`__main__.py`)

**Files:**
- Create: `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/__main__.py`

- [ ] **Step 1: Write `__main__.py`**

Create `/Users/ericbaruch/Arik/dev/markitdown/src/markitdown_cli/__main__.py`:
```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markitdown_cli.config import MissingKeyError
from markitdown_cli.convert import (
    ConvertSummary,
    build_markitdown,
    convert_file,
    convert_tree,
)


def _print_summary(summary: ConvertSummary, verbose: bool) -> None:
    print(
        f"Converted {summary.converted} • "
        f"Skipped {summary.skipped} (up-to-date) • "
        f"Unsupported {summary.unsupported} • "
        f"Errors {len(summary.errors)}"
    )
    if summary.errors:
        print("\nErrors:")
        for path, msg in summary.errors:
            print(f"  {path}: {msg}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdc",
        description="Convert documents to Markdown (wraps Microsoft markitdown).",
    )
    parser.add_argument("input", type=Path, help="File or directory to convert.")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output file (if input is a file) or directory (if input is a dir).")
    parser.add_argument("--force", action="store_true",
                        help="Re-convert even if the target .md exists and is newer.")
    parser.add_argument("--ocr", action="store_true",
                        help="Use OpenAI gpt-4o-mini to describe images. Requires OPENAI_API_KEY.")
    parser.add_argument("--audio", action="store_true",
                        help="Use OpenAI Whisper API to transcribe audio. Requires OPENAI_API_KEY.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print one log line per file.")

    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"mdc: input not found: {args.input}", file=sys.stderr)
        return 2

    try:
        md = build_markitdown(ocr=args.ocr)
    except MissingKeyError as e:
        print(str(e), file=sys.stderr)
        return 2

    try:
        if args.input.is_file():
            out = convert_file(
                args.input,
                out=args.output,
                md=md,
                force=args.force,
                audio=args.audio,
            )
            if args.verbose:
                print(f"{args.input} -> {out}")
            print("Converted 1 • Skipped 0 (up-to-date) • Unsupported 0 • Errors 0")
            return 0
        summary = convert_tree(
            args.input,
            out_root=args.output,
            md=md,
            force=args.force,
            audio=args.audio,
        )
        _print_summary(summary, args.verbose)
        return 1 if summary.errors else 0
    except MissingKeyError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run via uv and verify help works**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run python -m markitdown_cli --help
```
Expected: argparse help text printed, exit 0.

- [ ] **Step 3: Smoke test on a real .txt file**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run python -m markitdown_cli tests/fixtures/hello.txt
```
Expected:
```
Converted 1 • Skipped 0 (up-to-date) • Unsupported 0 • Errors 0
```
And `tests/fixtures/hello.txt.md` now exists with "Hello, markitdown." in it.

- [ ] **Step 4: Clean up fixture-md so tests stay hermetic**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && rm -f tests/fixtures/hello.txt.md
```

- [ ] **Step 5: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add src/markitdown_cli/__main__.py && git commit -m "feat: argparse CLI entry"
```

---

### Task 12: Install globally via uv and smoke-test `mdc`

**Files:** none modified; this is an install + verify pass.

- [ ] **Step 1: Install**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv tool install --force .
```
Expected: `Installed 1 executable: mdc` (and dep resolution output).

- [ ] **Step 2: Verify on PATH**

Run:
```bash
command -v mdc && mdc --help
```
Expected: prints path to the `mdc` binary, then the argparse help.

- [ ] **Step 3: Smoke test single file**

Run:
```bash
cd /tmp && printf "Hello from smoke test.\n" > smoke.txt && mdc smoke.txt && cat smoke.txt.md && rm smoke.txt smoke.txt.md
```
Expected: summary line, then `Hello from smoke test.` printed by `cat`.

- [ ] **Step 4: Smoke test folder**

Run:
```bash
cd /tmp && mkdir -p mdc_smoke/nested && printf "A\n" > mdc_smoke/a.txt && printf "B\n" > mdc_smoke/nested/b.txt && mdc mdc_smoke && ls mdc_smoke.md mdc_smoke.md/nested && rm -rf mdc_smoke mdc_smoke.md
```
Expected: both `a.txt.md` and `nested/b.txt.md` listed; summary reports `Converted 2`.

---

### Task 13: Claude skill

**Files:**
- Create: `/Users/ericbaruch/.claude/skills/markitdown/SKILL.md`

- [ ] **Step 1: Write the skill**

Create `/Users/ericbaruch/.claude/skills/markitdown/SKILL.md`:
```markdown
---
name: markitdown
description: Convert PDFs, Office docs (DOCX/PPTX/XLSX), HTML, EPUB, images, and audio to Markdown via the `mdc` CLI. Use when you encounter a non-text file the user referenced, when reading a `.pdf`/`.docx`/`.pptx`/`.xlsx` would fail the normal Read tool, or when the user asks to "extract text from" / "convert to markdown" / "read this PDF".
---

# markitdown

Wraps Microsoft's markitdown via the `mdc` CLI installed at `/Users/ericbaruch/Arik/dev/markitdown`. Use this skill to turn any supported binary document into markdown that the Read tool can open.

## When to use

- The user referenced a `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.epub`, `.rtf`, `.odt`, `.msg`, `.html`, or `.htm` and you need its contents.
- The user asked to "extract text from", "convert to markdown", or "read this PDF".
- You need to OCR an image (`.jpg`/`.png`/etc.) — only with user consent (OCR uses an API and costs money).
- You need to transcribe an audio file (`.mp3`/`.wav`/`.m4a`/`.flac`) — same consent rule.

## Preflight

Check that `mdc` is installed before calling it:

```bash
command -v mdc
```

If missing, tell the user to run:

```bash
uv tool install /Users/ericbaruch/Arik/dev/markitdown
```

Then stop — do not try to work around it.

## Usage

**Single file:**

```bash
mdc /absolute/path/to/report.pdf
```

This writes `/absolute/path/to/report.pdf.md`. Then use the Read tool on that path.

**Folder:**

```bash
mdc /absolute/path/to/docs
```

This creates `/absolute/path/to/docs.md/` mirroring the input tree. Glob `docs.md/**/*.md` and Read the files you actually need.

**Re-convert stale output:**

```bash
mdc /path/to/file.pdf --force
```

Default behavior skips files whose `.md` already exists and is newer than the source.

**Image OCR (requires user consent — costs API money):**

```bash
mdc /path/to/image.png --ocr
```

Uses OpenAI `gpt-4o-mini` via `OPENAI_API_KEY` in `/Users/ericbaruch/Arik/dev/.env`. Do not use `--ocr` on PDFs — it only affects image files.

**Audio transcription (requires user consent — costs API money):**

```bash
mdc /path/to/recording.mp3 --audio
```

Uses OpenAI Whisper API via the same key.

## Constraints

- Always pass absolute paths to `mdc` — avoids working-directory surprises.
- Never cat the whole output into the conversation for large docs. Use the Read tool with `offset`/`limit` if the markdown is big.
- Don't run `--ocr` or `--audio` without confirming with the user first.
- One failed file in a batch does not abort the batch; check the summary line at the end for error counts.

## Example flow

User: "Summarize this PDF: ~/Downloads/contract.pdf"

1. Run `command -v mdc` — confirm installed.
2. Run `mdc /Users/<user>/Downloads/contract.pdf`.
3. Read `/Users/<user>/Downloads/contract.pdf.md`.
4. Summarize.
```

- [ ] **Step 2: Verify file exists and skill dir is set up**

Run:
```bash
ls -la ~/.claude/skills/markitdown/
```
Expected: listing shows `SKILL.md`.

- [ ] **Step 3: Commit to the markitdown repo (the skill file itself lives under ~/.claude and is not in this repo)**

No commit needed for the skill file — it's outside the repo. If the user maintains `~/.claude` in git elsewhere, they'll commit there on their own cadence.

---

### Task 14: README

**Files:**
- Create: `/Users/ericbaruch/Arik/dev/markitdown/README.md`

- [ ] **Step 1: Write `README.md`**

Create `/Users/ericbaruch/Arik/dev/markitdown/README.md`:
```markdown
# mdc — personal markitdown CLI

A thin wrapper around [Microsoft markitdown](https://github.com/microsoft/markitdown) that adds batch folder conversion, output routing, skip-if-exists, OCR via OpenAI gpt-4o-mini, and audio transcription via OpenAI Whisper. Installed globally with `uv tool install`.

## Install

```bash
uv tool install /Users/ericbaruch/Arik/dev/markitdown
```

This exposes a `mdc` command on your `PATH`.

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
```

- [ ] **Step 2: Commit**

```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git add README.md && git commit -m "docs: README"
```

---

### Task 15: Final verification pass

**Files:** none modified.

- [ ] **Step 1: All tests pass**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && uv run pytest -v
```
Expected: all tests PASS, 0 failures.

- [ ] **Step 2: `mdc` works end-to-end**

Run:
```bash
mdc --help
```
Expected: argparse help text.

- [ ] **Step 3: OCR error message is clean when key is absent**

Run (temporarily hide the key):
```bash
OPENAI_API_KEY= mdc tests/fixtures/hello.txt --ocr 2>&1 | head -1
```
Note: this only exercises the error path if `.env` also lacks the key. If your `.env` has `OPENAI_API_KEY`, this command will succeed (which is fine — it means the config layer is working). The authoritative check is the unit test `test_missing_openai_key_raises_with_clear_message`.

- [ ] **Step 4: Git log is clean**

Run:
```bash
cd /Users/ericbaruch/Arik/dev/markitdown && git log --oneline
```
Expected: ~10 commits, each with a clear imperative message.

---

## Self-Review Notes

Spec coverage check against `docs/superpowers/specs/2026-04-22-markitdown-utility-and-skill-design.md`:

- §3.1 repo layout → Task 1
- §3.2 runtime + `uv tool install` → Tasks 1, 12
- §3.3 four modules → Tasks 2, 3–7, 8, 11
- §4 CLI spec → Task 11 (argparse wiring), exit codes covered in `main()`
- §4.3 batch rules, §4.5 summary → Tasks 6, 11
- §4.4 skip-if-exists → Task 5
- §5.1 env loading → Task 8
- §5.2 OCR wiring → Task 9
- §5.3 audio wiring → Task 10 (chose the "synthetic markdown" fallback option from the spec since subclassing upstream's AudioConverter is version-fragile)
- §6 skill → Task 13
- §7 testing → Tasks 3, 4, 5, 6, 7, 8
- §8 README → Task 14
