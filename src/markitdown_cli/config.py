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
