"""Unit tests for the raw Tesseract data parsing, without invoking Tesseract."""

from typing import Any, Dict, List

from ocr.engine import OCREngine


def build_data(entries: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """Build a Tesseract-shaped data dictionary out of simple entries.

    Args:
        entries: Sequence of dicts with ``text``, ``conf`` and geometry keys.

    Returns:
        A dictionary in the same shape ``image_to_data`` returns.
    """
    return {
        "text": [entry["text"] for entry in entries],
        "conf": [entry["conf"] for entry in entries],
        "left": [entry.get("left", 0) for entry in entries],
        "top": [entry.get("top", 0) for entry in entries],
        "width": [entry.get("width", 10) for entry in entries],
        "height": [entry.get("height", 10) for entry in entries],
    }


class TestIterDetections:
    """Tests for filtering and shaping Tesseract detections."""

    def test_skips_layout_placeholders(self) -> None:
        """Test that empty entries with confidence -1 are discarded."""
        data = build_data(
            [
                {"text": "", "conf": "-1"},
                {"text": "   ", "conf": "-1"},
                {"text": "Hola", "conf": "95"},
            ]
        )

        detections = list(OCREngine._iter_detections(data, 0.0))

        assert len(detections) == 1
        assert detections[0]["text"] == "Hola"

    def test_parses_fractional_confidence(self) -> None:
        """Test that float-like confidences do not raise.

        Tesseract 5 reports values such as ``"95.5"``; parsing them as ``int``
        would raise ``ValueError``.
        """
        data = build_data([{"text": "Hola", "conf": "95.5"}])

        detections = list(OCREngine._iter_detections(data, 0.0))

        assert detections[0]["confidence"] == 0.955

    def test_confidence_is_normalized_to_unit_range(self) -> None:
        """Test that confidence is scaled from percent to the 0-1 range."""
        data = build_data([{"text": "Hola", "conf": "80"}])

        detections = list(OCREngine._iter_detections(data, 0.0))

        assert 0.0 <= detections[0]["confidence"] <= 1.0
        assert detections[0]["confidence"] == 0.8

    def test_min_confidence_filters_weak_detections(self) -> None:
        """Test that detections under the threshold are dropped."""
        data = build_data(
            [
                {"text": "seguro", "conf": "90"},
                {"text": "dudoso", "conf": "30"},
            ]
        )

        detections = list(OCREngine._iter_detections(data, 0.5))

        assert [detection["text"] for detection in detections] == ["seguro"]

    def test_text_is_stripped(self) -> None:
        """Test that surrounding whitespace is removed from detections."""
        data = build_data([{"text": "  Hola  ", "conf": "90"}])

        detections = list(OCREngine._iter_detections(data, 0.0))

        assert detections[0]["text"] == "Hola"

    def test_bbox_holds_four_corners(self) -> None:
        """Test that the bounding box is built from the four corners."""
        data = build_data(
            [{"text": "Hola", "conf": "90", "left": 5, "top": 7, "width": 20, "height": 10}]
        )

        bbox = list(OCREngine._iter_detections(data, 0.0))[0]["bbox"]

        assert bbox == [[5, 7], [25, 7], [25, 17], [5, 17]]


class TestIsPdf:
    """Tests for the document type dispatch."""

    def test_detects_pdf_case_insensitively(self) -> None:
        """Test that the PDF check ignores the extension casing."""
        assert OCREngine.is_pdf("document.pdf")
        assert OCREngine.is_pdf("DOCUMENT.PDF")

    def test_rejects_images(self) -> None:
        """Test that images are not treated as PDFs."""
        assert not OCREngine.is_pdf("scan.png")
        assert not OCREngine.is_pdf("scan.jpeg")
