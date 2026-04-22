from __future__ import annotations

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
