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


def build_markitdown(ocr: bool = False) -> MarkItDown:
    """Construct a MarkItDown instance, optionally wired for LLM image description."""
    if not ocr:
        return MarkItDown()
    from markitdown_cli.config import get_openai_client
    client = get_openai_client(feature="--ocr")
    return MarkItDown(llm_client=client, llm_model="gpt-4o-mini")
