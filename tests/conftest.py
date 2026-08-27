"""Pytest configuration and fixtures for the OCR test suite."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

# Candidate fonts, in preference order: the default bitmap font is too small
# for Tesseract to recognize reliably.
_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
)


def _load_font(size: int = 48) -> ImageFont.ImageFont:
    """Return a legible font, falling back to PIL's bitmap default."""
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def tesseract_available() -> bool:
    """Return whether the Tesseract binary can be found on PATH."""
    return shutil.which("tesseract") is not None


#: Skip marker for tests that shell out to the Tesseract binary.
requires_tesseract = pytest.mark.skipif(
    not tesseract_available(),
    reason="Tesseract binary not installed; run the suite inside Docker",
)


@pytest.fixture
def sample_image(tmp_path: Path) -> str:
    """Create a sample image containing legible text.

    Returns:
        Path to the generated image file.
    """
    image = Image.new("RGB", (900, 400), color="white")
    draw = ImageDraw.Draw(image)
    font = _load_font()

    for index, line in enumerate(("Hello World", "OCR Test Image", "Python 2025")):
        draw.text((40, 40 + index * 110), line, fill="black", font=font)

    path = tmp_path / "sample.png"
    image.save(path)
    return str(path)


@pytest.fixture
def empty_image(tmp_path: Path) -> str:
    """Create a blank image for edge case testing.

    Returns:
        Path to the generated blank image file.
    """
    path = tmp_path / "blank.png"
    Image.new("RGB", (200, 200), color="white").save(path)
    return str(path)


@pytest.fixture
def sample_pdf(tmp_path: Path) -> str:
    """Create a two page PDF containing legible text.

    Returns:
        Path to the generated PDF file.
    """
    font = _load_font()
    pages = []

    for page_number in (1, 2):
        image = Image.new("RGB", (900, 400), color="white")
        draw = ImageDraw.Draw(image)
        draw.text((40, 60), f"Pagina {page_number}", fill="black", font=font)
        draw.text((40, 180), "Documento de prueba", fill="black", font=font)
        pages.append(image)

    path = tmp_path / "sample.pdf"
    pages[0].save(path, save_all=True, append_images=pages[1:])
    return str(path)


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for test artifacts."""
    directory = tmp_path / "outputs"
    directory.mkdir()
    return directory


@pytest.fixture
def invalid_image_path(tmp_path: Path) -> str:
    """Return a path to a file that does not exist."""
    return str(tmp_path / "missing" / "image.png")


@pytest.fixture
def corrupt_image(tmp_path: Path) -> str:
    """Create a file with an image extension but no valid image data.

    Returns:
        Path to the corrupt file.
    """
    path = tmp_path / "corrupt.png"
    path.write_bytes(b"this is definitely not a PNG")
    return str(path)
