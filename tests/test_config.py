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
