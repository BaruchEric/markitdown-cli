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


def test_convert_tree_aggregates_errors_without_aborting(tmp_path, monkeypatch):
    src_root = tmp_path / "docs"
    src_root.mkdir()
    (src_root / "good.txt").write_text("good\n")
    (src_root / "bad.txt").write_text("bad\n")

    from markitdown_cli import convert as convert_mod

    real = convert_mod.convert_file

    def flaky(src, out=None, md=None, force=False, audio=False):
        if Path(src).name == "bad.txt":
            raise RuntimeError("simulated parser failure")
        return real(src, out=out, md=md, force=force, audio=audio)

    monkeypatch.setattr(convert_mod, "convert_file", flaky)

    out_root = tmp_path / "out"
    summary = convert_mod.convert_tree(src_root, out_root)

    assert summary.converted == 1
    assert len(summary.errors) == 1
    bad_path, msg = summary.errors[0]
    assert bad_path.name == "bad.txt"
    assert "simulated parser failure" in msg
    assert (out_root / "good.txt.md").exists()


def test_single_file_skip_is_reported_as_skipped_not_converted(tmp_path, monkeypatch, capsys):
    from markitdown_cli.__main__ import main

    src = tmp_path / "hello.txt"
    src.write_text("x\n")
    # First run: converts
    rc1 = main([str(src)])
    assert rc1 == 0
    out1 = capsys.readouterr().out
    assert "Converted 1" in out1
    assert "Skipped 0" in out1

    # Second run with no changes: should report as skipped
    rc2 = main([str(src)])
    assert rc2 == 0
    out2 = capsys.readouterr().out
    assert "Converted 0" in out2
    assert "Skipped 1 (up-to-date)" in out2


def test_convert_tree_verbose_prints_per_file(tmp_path, capsys):
    src_root = tmp_path / "docs"
    src_root.mkdir()
    (src_root / "a.txt").write_text("A\n")
    (src_root / "ignored.xyz").write_text("x\n")

    out_root = tmp_path / "out"
    convert_tree(src_root, out_root, verbose=True)
    output = capsys.readouterr().out

    assert "a.txt" in output
    assert "ignored.xyz" in output
    assert "unsupported" in output
