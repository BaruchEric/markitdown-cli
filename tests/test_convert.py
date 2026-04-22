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


def test_convert_file_respects_explicit_output(tmp_path):
    src = tmp_path / "hello.txt"
    src.write_text("Hello.\n")
    dest = tmp_path / "nested" / "out.md"

    out = convert_file(src, out=dest)

    assert out == dest
    assert dest.exists()
    assert "Hello." in dest.read_text()


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
