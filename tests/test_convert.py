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
