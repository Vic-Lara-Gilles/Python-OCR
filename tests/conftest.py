"""Pytest configuration and fixtures for OCR tests."""

import os
import tempfile
from pathlib import Path
from typing import Generator
import pytest
from PIL import Image, ImageDraw, ImageFont


@pytest.fixture
def sample_image() -> Generator[str, None, None]:
    """
    Create a temporary sample image with text for OCR testing.

    Yields:
        Path to the temporary image file.
    """
    # Create a simple image with text
    img = Image.new("RGB", (400, 200), color="white")
    draw = ImageDraw.Draw(img)

    # Draw sample text
    draw.text((50, 50), "Hello World", fill="black")
    draw.text((50, 100), "OCR Test Image", fill="black")
    draw.text((50, 150), "Python 2025", fill="black")

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img.save(tmp.name)
        yield tmp.name

    # Cleanup
    if os.path.exists(tmp.name):
        os.remove(tmp.name)


@pytest.fixture
def empty_image() -> Generator[str, None, None]:
    """
    Create a temporary blank image for testing edge cases.

    Yields:
        Path to the temporary blank image file.
    """
    img = Image.new("RGB", (200, 200), color="white")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        img.save(tmp.name)
        yield tmp.name

    if os.path.exists(tmp.name):
        os.remove(tmp.name)


@pytest.fixture
def output_dir() -> Generator[Path, None, None]:
    """
    Create a temporary output directory for test results.

    Yields:
        Path to the temporary output directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def invalid_image_path() -> str:
    """
    Return a path to a non-existent image file.

    Returns:
        Path string to non-existent file.
    """
    return "/nonexistent/path/image.png"
