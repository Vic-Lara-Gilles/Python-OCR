"""Runtime configuration for the OCR package, sourced from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

#: Image extensions the engine can read directly.
IMAGE_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"})

#: Document extensions that are rasterized before OCR.
PDF_SUFFIXES = frozenset({".pdf"})

#: Every extension accepted by the application.
SUPPORTED_SUFFIXES = IMAGE_SUFFIXES | PDF_SUFFIXES


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value or default


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env_str(name, str(default)))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(_env_str(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable snapshot of the environment-driven configuration.

    Attributes:
        lang: Tesseract language code (e.g. ``spa``, ``eng``, ``spa+eng``).
        output_dir: Directory where generated artifacts are written.
        pdf_zoom: Scale factor applied when rasterizing PDF pages. Higher
            values improve OCR accuracy at the cost of memory and time.
        max_upload_bytes: Largest accepted upload, in bytes.
        min_confidence: Detections below this confidence (0-1) are discarded.
        log_level: Logging level name for the package logger.
    """

    lang: str
    output_dir: Path
    pdf_zoom: float
    max_upload_bytes: int
    min_confidence: float
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables, falling back to defaults."""
        return cls(
            lang=_env_str("OCR_LANG", "spa"),
            output_dir=Path(_env_str("OUTPUT_DIR", "outputs")),
            pdf_zoom=_env_float("OCR_PDF_ZOOM", 2.0),
            max_upload_bytes=_env_int("MAX_UPLOAD_SIZE_MB", 25) * 1024 * 1024,
            min_confidence=_env_float("OCR_MIN_CONFIDENCE", 0.0),
            log_level=_env_str("LOG_LEVEL", "INFO"),
        )


settings = Settings.from_env()
