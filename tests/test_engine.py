"""Unit tests for OCR Engine module."""

import os
from pathlib import Path
import pytest


class TestOCREngineExtraction:
    """Tests for text extraction functionality."""

    def test_extract_text_returns_dict(self, sample_image: str) -> None:
        """Test that extract_text_and_boxes returns a dictionary."""
        # Import here to avoid Streamlit issues in test environment
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        assert isinstance(result, dict)
        assert "file" in result
        assert "full_text" in result
        assert "boxes" in result
        assert "total_lines" in result

    def test_extract_text_file_field(self, sample_image: str) -> None:
        """Test that file field contains correct filename."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        assert result["file"] == os.path.basename(sample_image)

    def test_extract_text_boxes_is_list(self, sample_image: str) -> None:
        """Test that boxes field is a list."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        assert isinstance(result["boxes"], list)

    def test_extract_text_total_lines_matches_boxes(self, sample_image: str) -> None:
        """Test that total_lines matches the number of boxes."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        assert result["total_lines"] == len(result["boxes"])

    def test_extract_empty_image(self, empty_image: str) -> None:
        """Test extraction from blank image returns empty results."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(empty_image)

        assert result["full_text"] == ""
        assert result["boxes"] == []
        assert result["total_lines"] == 0


class TestOCREngineFormatters:
    """Tests for text formatting functionality."""

    def test_generate_markdown_contains_header(self, sample_image: str) -> None:
        """Test that markdown output contains header."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)
        markdown = OCREngine.generate_markdown(result)

        assert markdown.startswith("# OCR Result:")
        assert "## Extracted Text" in markdown

    def test_generate_markdown_contains_stats(self, sample_image: str) -> None:
        """Test that markdown output contains statistics."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)
        markdown = OCREngine.generate_markdown(result)

        assert "**Total Lines:**" in markdown

    def test_generate_plain_text(self, sample_image: str) -> None:
        """Test plain text generation."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)
        plain = OCREngine.generate_plain_text(result)

        assert plain == result["full_text"]


class TestOCREngineVisualization:
    """Tests for bounding box visualization functionality."""

    def test_visualize_boxes_creates_file(
        self, sample_image: str, output_dir: Path
    ) -> None:
        """Test that visualize_boxes creates an output file."""
        from ocr.engine import OCREngine

        output_path = output_dir / "output.png"
        result = OCREngine.visualize_boxes(sample_image, str(output_path))

        assert os.path.exists(result)
        assert result == str(output_path)

    def test_visualize_boxes_returns_path(
        self, sample_image: str, output_dir: Path
    ) -> None:
        """Test that visualize_boxes returns the output path."""
        from ocr.engine import OCREngine

        output_path = output_dir / "output.png"
        result = OCREngine.visualize_boxes(sample_image, str(output_path))

        assert isinstance(result, str)
        assert result.endswith(".png")

    def test_visualize_boxes_invalid_image_raises(
        self, invalid_image_path: str, output_dir: Path
    ) -> None:
        """Test that invalid image path raises ValueError."""
        from ocr.engine import OCREngine

        output_path = output_dir / "output.png"

        with pytest.raises(ValueError):
            OCREngine.visualize_boxes(invalid_image_path, str(output_path))


class TestOCREngineBoxStructure:
    """Tests for box data structure."""

    def test_box_contains_required_fields(self, sample_image: str) -> None:
        """Test that each box contains required fields."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        for box in result["boxes"]:
            assert "text" in box
            assert "confidence" in box
            assert "bbox" in box

    def test_box_confidence_is_float(self, sample_image: str) -> None:
        """Test that confidence values are floats."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        for box in result["boxes"]:
            assert isinstance(box["confidence"], float)
            assert 0.0 <= box["confidence"] <= 1.0

    def test_box_bbox_is_list(self, sample_image: str) -> None:
        """Test that bbox is a list of coordinates."""
        from ocr.engine import OCREngine

        result = OCREngine.extract_text_and_boxes(sample_image)

        for box in result["boxes"]:
            assert isinstance(box["bbox"], list)
            assert len(box["bbox"]) == 4  # Four corner points
