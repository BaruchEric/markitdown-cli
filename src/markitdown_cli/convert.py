from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from markitdown import MarkItDown


def _default_output_path(src: Path) -> Path:
    """For a source file `report.pdf`, return `report.pdf.md`."""
    return src.with_suffix(src.suffix + ".md")


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
    audio: bool = False,
    verbose: bool = False,
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
            if verbose:
                print(f"{src}: unsupported")
            continue

        rel = src.relative_to(src_root)
        dest = out_root / rel.with_suffix(rel.suffix + ".md")

        try:
            if not force and dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
                summary.skipped += 1
                if verbose:
                    print(f"{src}: skipped (up-to-date)")
                continue
            convert_file(src, out=dest, md=md, force=True, audio=audio)
            summary.converted += 1
            if verbose:
                print(f"{src} -> {dest}")
        except Exception as e:  # noqa: BLE001 — aggregate, don't abort
            summary.errors.append((src, f"{type(e).__name__}: {e}"))
            if verbose:
                print(f"{src}: ERROR {type(e).__name__}: {e}")

    return summary


def build_markitdown(ocr: bool = False) -> MarkItDown:
    """Construct a MarkItDown instance, optionally wired for LLM image description."""
    if not ocr:
        return MarkItDown()
    from markitdown_cli.config import get_openai_client
    client = get_openai_client(feature="--ocr")
    return MarkItDown(llm_client=client, llm_model="gpt-4o-mini")


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
