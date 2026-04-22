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
