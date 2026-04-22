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


def _print_summary(summary: ConvertSummary) -> None:
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
            default_out = args.output or args.input.with_suffix(args.input.suffix + ".md")
            would_skip = (
                not args.force
                and default_out.exists()
                and default_out.stat().st_mtime >= args.input.stat().st_mtime
            )
            out = convert_file(
                args.input,
                out=args.output,
                md=md,
                force=args.force,
                audio=args.audio,
            )
            if args.verbose:
                status = "skipped" if would_skip else "converted"
                print(f"{args.input} -> {out} ({status})")
            if would_skip:
                print("Converted 0 • Skipped 1 (up-to-date) • Unsupported 0 • Errors 0")
            else:
                print("Converted 1 • Skipped 0 (up-to-date) • Unsupported 0 • Errors 0")
            return 0
        summary = convert_tree(
            args.input,
            out_root=args.output,
            md=md,
            force=args.force,
            audio=args.audio,
            verbose=args.verbose,
        )
        _print_summary(summary)
        return 1 if summary.errors else 0
    except MissingKeyError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
