"""Unit tests for the environment-driven configuration."""

from pathlib import Path

import pytest

from ocr.config import SUPPORTED_SUFFIXES, Settings


class TestSettingsFromEnv:
    """Tests for building settings out of environment variables."""

    def test_defaults_when_env_is_empty(self, monkeypatch) -> None:
        """Test that missing variables fall back to sane defaults."""
        for name in (
            "OCR_LANG",
            "OUTPUT_DIR",
            "OCR_PDF_ZOOM",
            "MAX_UPLOAD_SIZE_MB",
            "OCR_MIN_CONFIDENCE",
            "LOG_LEVEL",
        ):
            monkeypatch.delenv(name, raising=False)

        config = Settings.from_env()

        assert config.lang == "spa"
        assert config.output_dir == Path("outputs")
        assert config.pdf_zoom == 2.0
        assert config.max_upload_bytes == 25 * 1024 * 1024
        assert config.min_confidence == 0.0
        assert config.log_level == "INFO"

    def test_values_are_read_from_env(self, monkeypatch) -> None:
        """Test that environment variables override the defaults."""
        monkeypatch.setenv("OCR_LANG", "eng")
        monkeypatch.setenv("OUTPUT_DIR", "/tmp/ocr-out")
        monkeypatch.setenv("OCR_PDF_ZOOM", "3.5")
        monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "10")
        monkeypatch.setenv("OCR_MIN_CONFIDENCE", "0.6")

        config = Settings.from_env()

        assert config.lang == "eng"
        assert config.output_dir == Path("/tmp/ocr-out")
        assert config.pdf_zoom == 3.5
        assert config.max_upload_bytes == 10 * 1024 * 1024
        assert config.min_confidence == 0.6

    def test_invalid_numeric_values_fall_back(self, monkeypatch) -> None:
        """Test that unparsable numbers do not crash the application."""
        monkeypatch.setenv("OCR_PDF_ZOOM", "not-a-number")
        monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "")

        config = Settings.from_env()

        assert config.pdf_zoom == 2.0
        assert config.max_upload_bytes == 25 * 1024 * 1024

    def test_settings_are_immutable(self) -> None:
        """Test that settings cannot be mutated at runtime."""
        config = Settings.from_env()

        with pytest.raises(Exception):
            config.lang = "eng"  # type: ignore[misc]


class TestSupportedSuffixes:
    """Tests for the supported extension registry."""

    def test_contains_images_and_pdf(self) -> None:
        """Test that the common formats are accepted."""
        assert ".png" in SUPPORTED_SUFFIXES
        assert ".jpg" in SUPPORTED_SUFFIXES
        assert ".pdf" in SUPPORTED_SUFFIXES

    def test_suffixes_are_lowercase_with_dot(self) -> None:
        """Test the normalized shape of every registered suffix."""
        for suffix in SUPPORTED_SUFFIXES:
            assert suffix.startswith(".")
            assert suffix == suffix.lower()
