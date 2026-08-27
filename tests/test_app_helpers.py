"""Unit tests for the Streamlit application helpers."""

import pytest

streamlit = pytest.importorskip("streamlit")

from ocr.app import preview_text, safe_stem, safe_suffix  # noqa: E402


class TestSafeStem:
    """Tests for upload name sanitization."""

    @pytest.mark.parametrize(
        "filename",
        [
            "../../etc/passwd",
            "/etc/passwd",
            "..\\..\\windows\\system32\\config",
        ],
    )
    def test_strips_path_traversal(self, filename: str) -> None:
        """Test that directory components never survive sanitization."""
        stem = safe_stem(filename)

        assert "/" not in stem
        assert "\\" not in stem
        assert ".." not in stem

    def test_keeps_readable_names(self) -> None:
        """Test that ordinary names are preserved."""
        assert safe_stem("factura_2025.pdf") == "factura_2025"

    def test_replaces_unsafe_characters(self) -> None:
        """Test that spaces and accents are replaced, not dropped silently."""
        stem = safe_stem("mi factura ñ.png")

        assert " " not in stem
        assert stem.replace("_", "").isalnum()

    def test_never_returns_empty(self) -> None:
        """Test that a fully stripped name falls back to a default."""
        assert safe_stem("...") == "documento"
        assert safe_stem("") == "documento"


class TestSafeSuffix:
    """Tests for extension validation."""

    def test_accepts_supported_extensions(self) -> None:
        """Test that supported extensions are normalized to lowercase."""
        assert safe_suffix("scan.PNG") == ".png"
        assert safe_suffix("doc.pdf") == ".pdf"

    def test_rejects_unsupported_extensions(self) -> None:
        """Test that an unknown extension is discarded."""
        assert safe_suffix("payload.exe") == ""
        assert safe_suffix("archive.tar.gz") == ""


class TestPreviewText:
    """Tests for tabular text previews."""

    def test_short_text_is_untouched(self) -> None:
        """Test that short text is returned as is."""
        assert preview_text("hola") == "hola"

    def test_long_text_is_truncated(self) -> None:
        """Test that long text is cut and suffixed with an ellipsis."""
        preview = preview_text("a" * 500)

        assert preview.endswith("...")
        assert len(preview) == 103
