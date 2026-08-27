"""OCR package for document text extraction using Tesseract-OCR."""

from ocr.config import Settings, settings
from ocr.engine import OCREngine, OCRError

__version__ = "1.1.0"
__all__ = ["OCREngine", "OCRError", "Settings", "settings"]
