"""Unit tests for the OCR engine."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ocr.engine import OCREngine, OCRError

from .conftest import requires_tesseract


class TestOCREngineErrors:
    """Tests for error handling on unreadable inputs."""

    def test_missing_file_raises_ocr_error(self, invalid_image_path: str) -> None:
        """Test that a nonexistent path raises OCRError."""
        with pytest.raises(OCRError):
            OCREngine.extract_text_and_boxes(invalid_image_path)

    def test_corrupt_file_raises_ocr_error(self, corrupt_image: str) -> None:
        """Test that a file with invalid image data raises OCRError."""
        with pytest.raises(OCRError):
            OCREngine.extract_text_and_boxes(corrupt_image)

    def test_ocr_error_is_a_value_error(self) -> None:
        """Test that OCRError stays compatible with ValueError handlers."""
        assert issubclass(OCRError, ValueError)

    def test_visualize_invalid_image_raises(
        self, invalid_image_path: str, output_dir: Path
    ) -> None:
        """Test that visualizing a missing image raises ValueError."""
        with pytest.raises(ValueError):
            OCREngine.visualize_boxes(
                invalid_image_path, str(output_dir / "output.png")
            )


class TestOCREngineFormatters:
    """Tests for the output formatters, independent of the OCR binary."""

    @staticmethod
    def build_result(**overrides: object) -> dict:
        """Return a minimal OCR result dictionary."""
        result = {
            "file": "scan.png",
            "full_text": "Hola mundo",
            "boxes": [],
            "total_lines": 2,
        }
        result.update(overrides)
        return result

    def test_markdown_contains_header_and_section(self) -> None:
        """Test that the Markdown rendering has a title and a text section."""
        markdown = OCREngine.generate_markdown(self.build_result())

        assert markdown.startswith("# OCR Result: scan.png")
        assert "## Extracted Text" in markdown

    def test_markdown_contains_stats(self) -> None:
        """Test that the Markdown rendering reports the detection count."""
        markdown = OCREngine.generate_markdown(self.build_result())

        assert "**Total Lines:** 2" in markdown

    def test_markdown_includes_page_count_for_pdfs(self) -> None:
        """Test that PDF results add the page count to the Markdown output."""
        markdown = OCREngine.generate_markdown(self.build_result(total_pages=3))

        assert "**Total Pages:** 3" in markdown

    def test_markdown_omits_page_count_for_images(self) -> None:
        """Test that image results do not mention pages."""
        markdown = OCREngine.generate_markdown(self.build_result())

        assert "Total Pages" not in markdown

    def test_markdown_contains_extracted_text(self) -> None:
        """Test that the extracted text is included verbatim."""
        markdown = OCREngine.generate_markdown(self.build_result())

        assert "Hola mundo" in markdown

    def test_plain_text_returns_full_text(self) -> None:
        """Test that plain text rendering returns the raw text."""
        result = self.build_result()

        assert OCREngine.generate_plain_text(result) == result["full_text"]


@requires_tesseract
class TestOCREngineExtraction:
    """Tests for text extraction. Requires the Tesseract binary."""

    def test_returns_expected_shape(self, sample_image: str) -> None:
        """Test that extraction returns the documented dictionary keys."""
        result = OCREngine.extract_text_and_boxes(sample_image)

        assert set(result) == {"file", "full_text", "boxes", "total_lines"}

    def test_file_field_is_the_basename(self, sample_image: str) -> None:
        """Test that the file field holds the source file name."""
        result = OCREngine.extract_text_and_boxes(sample_image)

        assert result["file"] == os.path.basename(sample_image)

    def test_total_lines_matches_boxes(self, sample_image: str) -> None:
        """Test that the reported count matches the number of boxes."""
        result = OCREngine.extract_text_and_boxes(sample_image)

        assert result["total_lines"] == len(result["boxes"])

    def test_detects_known_text(self, sample_image: str) -> None:
        """Test that a legible word from the sample image is recognized."""
        result = OCREngine.extract_text_and_boxes(sample_image, lang="eng")

        assert "Hello" in result["full_text"]

    def test_blank_image_yields_no_detections(self, empty_image: str) -> None:
        """Test that a blank image produces an empty result."""
        result = OCREngine.extract_text_and_boxes(empty_image)

        assert result["full_text"] == ""
        assert result["boxes"] == []
        assert result["total_lines"] == 0

    def test_min_confidence_filters_detections(self, sample_image: str) -> None:
        """Test that an impossible threshold discards every detection."""
        result = OCREngine.extract_text_and_boxes(sample_image, min_confidence=1.01)

        assert result["boxes"] == []


@requires_tesseract
class TestOCREngineBoxStructure:
    """Tests for the shape of individual detections."""

    def test_boxes_have_required_fields(self, sample_image: str) -> None:
        """Test that every box carries text, confidence and geometry."""
        result = OCREngine.extract_text_and_boxes(sample_image)

        assert result["boxes"], "expected at least one detection"
        for box in result["boxes"]:
            assert {"text", "confidence", "bbox"} <= set(box)

    def test_confidence_is_a_unit_float(self, sample_image: str) -> None:
        """Test that confidences are floats in the 0-1 range."""
        result = OCREngine.extract_text_and_boxes(sample_image)

        for box in result["boxes"]:
            assert isinstance(box["confidence"], float)
            assert 0.0 <= box["confidence"] <= 1.0

    def test_bbox_has_four_corners(self, sample_image: str) -> None:
        """Test that each bounding box holds four corner points."""
        result = OCREngine.extract_text_and_boxes(sample_image)

        for box in result["boxes"]:
            assert len(box["bbox"]) == 4
            assert all(len(corner) == 2 for corner in box["bbox"])


@requires_tesseract
class TestOCREnginePdf:
    """Tests for PDF handling."""

    def test_rasterized_pdf_cleans_up_pages(self, sample_pdf: str) -> None:
        """Test that temporary page images are deleted on exit."""
        with OCREngine.rasterized_pdf(sample_pdf) as pages:
            assert len(pages) == 2
            assert all(os.path.exists(page) for page in pages)

        assert not any(os.path.exists(page) for page in pages)

    def test_extract_from_pdf_reports_pages(self, sample_pdf: str) -> None:
        """Test that PDF extraction reports the page count."""
        result = OCREngine.extract_text_from_pdf(sample_pdf)

        assert result["total_pages"] == 2

    def test_pdf_boxes_carry_page_numbers(self, sample_pdf: str) -> None:
        """Test that every PDF detection knows which page it came from."""
        result = OCREngine.extract_text_from_pdf(sample_pdf)

        pages = {box["page"] for box in result["boxes"]}
        assert pages <= {1, 2}
        assert pages, "expected at least one detection"

    def test_extract_document_dispatches_to_pdf(self, sample_pdf: str) -> None:
        """Test that the dispatcher recognizes PDFs."""
        result = OCREngine.extract_document(sample_pdf)

        assert "total_pages" in result

    def test_extract_document_dispatches_to_image(self, sample_image: str) -> None:
        """Test that the dispatcher recognizes images."""
        result = OCREngine.extract_document(sample_image)

        assert "total_pages" not in result


@requires_tesseract
class TestOCREngineVisualization:
    """Tests for bounding box rendering."""

    def test_creates_output_file(self, sample_image: str, output_dir: Path) -> None:
        """Test that the annotated image is written to disk."""
        output_path = output_dir / "output.png"

        result = OCREngine.visualize_boxes(sample_image, str(output_path))

        assert result == str(output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_creates_missing_parent_directory(
        self, sample_image: str, output_dir: Path
    ) -> None:
        """Test that a missing destination directory is created."""
        output_path = output_dir / "nested" / "output.png"

        OCREngine.visualize_boxes(sample_image, str(output_path))

        assert output_path.exists()

    def test_visualize_document_returns_one_image_per_page(
        self, sample_pdf: str, output_dir: Path
    ) -> None:
        """Test that a PDF is annotated page by page."""
        outputs = OCREngine.visualize_document(sample_pdf, str(output_dir), "sample")

        assert len(outputs) == 2
        assert all(Path(path).exists() for path in outputs)

    def test_visualize_document_handles_images(
        self, sample_image: str, output_dir: Path
    ) -> None:
        """Test that a plain image yields a single annotated file."""
        outputs = OCREngine.visualize_document(sample_image, str(output_dir), "sample")

        assert len(outputs) == 1
        assert Path(outputs[0]).name == "boxes_sample.png"
