"""OCR Engine for text extraction and visualization using Tesseract-OCR.

The engine is deliberately free of any UI dependency so it can be reused from
the Streamlit app, a CLI, a test suite or any other caller.
"""

from __future__ import annotations

import logging
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import cv2
import fitz
import numpy as np
import pytesseract
from PIL import Image, UnidentifiedImageError

from ocr.config import PDF_SUFFIXES, settings

logger = logging.getLogger(__name__)

# Bounding box colors, in RGB.
_BOX_COLOR = (0, 255, 0)
_LABEL_COLOR = (255, 0, 0)
_LABEL_BACKGROUND = (255, 255, 255)
_FONT = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 0.5
_FONT_THICKNESS = 1


class OCRError(ValueError):
    """Raised when a document cannot be read or processed.

    Inherits from ``ValueError`` so existing callers catching ``ValueError``
    keep working.
    """


class OCREngine:
    """Document text extraction and bounding box visualization."""

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_image(image_path: str) -> Image.Image:
        """Load an image from disk as RGB.

        Args:
            image_path: Path to the input image file.

        Returns:
            The decoded image in RGB mode.

        Raises:
            OCRError: If the file is missing or is not a readable image.
        """
        try:
            with Image.open(image_path) as handle:
                return handle.convert("RGB")
        except (FileNotFoundError, OSError, UnidentifiedImageError) as exc:
            raise OCRError(f"Could not load image from {image_path}: {exc}") from exc

    @staticmethod
    def _run_tesseract(image: Image.Image, lang: str) -> Dict[str, List[Any]]:
        """Run Tesseract and return its raw per-word data dictionary."""
        try:
            return pytesseract.image_to_data(
                image, lang=lang, output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractError as exc:
            raise OCRError(f"Tesseract failed (lang={lang!r}): {exc}") from exc
        except pytesseract.TesseractNotFoundError as exc:
            raise OCRError(
                "Tesseract binary not found. Install tesseract-ocr and make "
                "sure it is on PATH."
            ) from exc

    @staticmethod
    def _iter_detections(
        data: Dict[str, List[Any]], min_confidence: float
    ) -> Iterator[Dict[str, Any]]:
        """Yield the meaningful word detections from raw Tesseract data.

        Tesseract emits one entry per layout element, including page, block and
        line placeholders that carry no text and a confidence of ``-1``. Those
        are skipped, as are detections below ``min_confidence``.

        Args:
            data: Raw dictionary returned by ``image_to_data``.
            min_confidence: Minimum confidence, in the 0-1 range.

        Yields:
            Dictionaries with ``text``, ``confidence`` and ``bbox`` keys, where
            ``bbox`` holds the four corners as ``[[x, y], ...]``.
        """
        for index, raw_text in enumerate(data["text"]):
            text = raw_text.strip()
            if not text:
                continue

            # Tesseract 5 reports confidence as a float-like string.
            raw_confidence = float(data["conf"][index])
            if raw_confidence <= 0:
                continue

            confidence = raw_confidence / 100.0
            if confidence < min_confidence:
                continue

            x = data["left"][index]
            y = data["top"][index]
            width = data["width"][index]
            height = data["height"][index]

            yield {
                "text": text,
                "confidence": confidence,
                "bbox": [
                    [x, y],
                    [x + width, y],
                    [x + width, y + height],
                    [x, y + height],
                ],
            }

    # ------------------------------------------------------------------
    # PDF handling
    # ------------------------------------------------------------------

    @staticmethod
    def pdf_to_images(pdf_path: str, zoom: Optional[float] = None) -> List[str]:
        """Rasterize every page of a PDF into temporary PNG files.

        The caller owns the returned files and is responsible for deleting
        them; prefer :meth:`rasterized_pdf` which cleans up automatically.

        Args:
            pdf_path: Path to the input PDF file.
            zoom: Scale factor for rendering. Defaults to the configured zoom.

        Returns:
            List of paths to temporary image files, one per page.

        Raises:
            OCRError: If the PDF cannot be opened or rendered.
        """
        scale = settings.pdf_zoom if zoom is None else zoom
        matrix = fitz.Matrix(scale, scale)
        image_paths: List[str] = []

        try:
            with fitz.open(pdf_path) as document:
                for page in document:
                    pixmap = page.get_pixmap(matrix=matrix)
                    # Close the handle immediately: PyMuPDF writes by path and
                    # leaving it open would leak a descriptor per page.
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".png"
                    ) as temp_file:
                        temp_path = temp_file.name
                    pixmap.save(temp_path)
                    image_paths.append(temp_path)
        except Exception as exc:
            OCREngine._remove_files(image_paths)
            raise OCRError(f"Could not rasterize PDF {pdf_path}: {exc}") from exc

        logger.debug("Rasterized %s into %d page(s)", pdf_path, len(image_paths))
        return image_paths

    @staticmethod
    @contextmanager
    def rasterized_pdf(
        pdf_path: str, zoom: Optional[float] = None
    ) -> Iterator[List[str]]:
        """Context manager yielding rasterized PDF pages and cleaning them up."""
        image_paths = OCREngine.pdf_to_images(pdf_path, zoom=zoom)
        try:
            yield image_paths
        finally:
            OCREngine._remove_files(image_paths)

    @staticmethod
    def _remove_files(paths: List[str]) -> None:
        """Delete temporary files, ignoring the ones already gone."""
        for path in paths:
            try:
                os.remove(path)
            except OSError:  # pragma: no cover - best effort cleanup
                logger.warning("Could not remove temporary file %s", path)

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def extract_text_and_boxes(
        image_path: str,
        lang: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Extract text and word-level bounding boxes from an image.

        Args:
            image_path: Path to the input image file.
            lang: Tesseract language code. Defaults to the configured language.
            min_confidence: Minimum confidence (0-1) a detection must reach.

        Returns:
            Dictionary containing:
                - ``file``: source filename
                - ``full_text``: detected words joined by spaces
                - ``boxes``: list of ``{text, confidence, bbox}`` entries
                - ``total_lines``: number of detections (word level)

        Raises:
            OCRError: If the image cannot be read or Tesseract fails.
        """
        language = lang or settings.lang
        threshold = (
            settings.min_confidence if min_confidence is None else min_confidence
        )

        image = OCREngine._load_image(image_path)
        data = OCREngine._run_tesseract(image, language)
        boxes = list(OCREngine._iter_detections(data, threshold))

        logger.info(
            "Extracted %d detection(s) from %s", len(boxes), os.path.basename(image_path)
        )

        return {
            "file": os.path.basename(image_path),
            "full_text": " ".join(box["text"] for box in boxes),
            "boxes": boxes,
            "total_lines": len(boxes),
        }

    @staticmethod
    def extract_text_from_pdf(
        pdf_path: str,
        lang: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Extract text from every page of a PDF.

        Args:
            pdf_path: Path to the input PDF file.
            lang: Tesseract language code. Defaults to the configured language.
            min_confidence: Minimum confidence (0-1) a detection must reach.

        Returns:
            Dictionary with the combined results of all pages, where every box
            carries an extra ``page`` key (1-indexed).

        Raises:
            OCRError: If the PDF cannot be rasterized or OCR fails.
        """
        all_boxes: List[Dict[str, Any]] = []
        text_parts: List[str] = []

        with OCREngine.rasterized_pdf(pdf_path) as image_paths:
            for page_number, image_path in enumerate(image_paths, start=1):
                result = OCREngine.extract_text_and_boxes(
                    image_path, lang=lang, min_confidence=min_confidence
                )

                for box in result["boxes"]:
                    box["page"] = page_number
                    all_boxes.append(box)

                if result["full_text"]:
                    text_parts.append(f"[Page {page_number}] {result['full_text']}")

            page_count = len(image_paths)

        return {
            "file": os.path.basename(pdf_path),
            "full_text": "\n\n".join(text_parts),
            "boxes": all_boxes,
            "total_lines": len(all_boxes),
            "total_pages": page_count,
        }

    @staticmethod
    def extract_document(
        document_path: str,
        lang: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Extract text from an image or a PDF, picking the right strategy.

        Args:
            document_path: Path to an image or PDF file.
            lang: Tesseract language code. Defaults to the configured language.
            min_confidence: Minimum confidence (0-1) a detection must reach.

        Returns:
            The extraction result dictionary.
        """
        if OCREngine.is_pdf(document_path):
            return OCREngine.extract_text_from_pdf(
                document_path, lang=lang, min_confidence=min_confidence
            )
        return OCREngine.extract_text_and_boxes(
            document_path, lang=lang, min_confidence=min_confidence
        )

    @staticmethod
    def is_pdf(document_path: str) -> bool:
        """Return whether the given path points to a PDF, by extension."""
        return Path(document_path).suffix.lower() in PDF_SUFFIXES

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    @staticmethod
    def generate_markdown(result: Dict[str, Any]) -> str:
        """Render an OCR result as Markdown.

        Args:
            result: OCR extraction result dictionary.

        Returns:
            Markdown formatted string.
        """
        lines = [f"# OCR Result: {result['file']}\n"]

        if result.get("total_pages"):
            lines.append(f"**Total Pages:** {result['total_pages']}\n")

        lines.append(f"**Total Lines:** {result['total_lines']}\n")
        lines.append("---\n")
        lines.append("## Extracted Text\n")
        lines.append(result["full_text"])

        return "\n".join(lines)

    @staticmethod
    def generate_plain_text(result: Dict[str, Any]) -> str:
        """Return the raw extracted text of an OCR result."""
        return result["full_text"]

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    @staticmethod
    def visualize_boxes(
        image_path: str,
        output_path: str,
        lang: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> str:
        """Draw the detected bounding boxes on an image and save the result.

        Args:
            image_path: Path to the input image file.
            output_path: Path where the annotated image will be saved.
            lang: Tesseract language code. Defaults to the configured language.
            min_confidence: Minimum confidence (0-1) a detection must reach.

        Returns:
            Path to the saved annotated image.

        Raises:
            OCRError: If the image cannot be read, OCR fails or the annotated
                image cannot be written.
        """
        language = lang or settings.lang
        threshold = (
            settings.min_confidence if min_confidence is None else min_confidence
        )

        image = OCREngine._load_image(image_path)
        data = OCREngine._run_tesseract(image, language)

        canvas = np.array(image)
        for detection in OCREngine._iter_detections(data, threshold):
            OCREngine._draw_detection(canvas, detection)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(output_path, cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR)):
            raise OCRError(f"Could not write annotated image to {output_path}")

        return output_path

    @staticmethod
    def _draw_detection(canvas: np.ndarray, detection: Dict[str, Any]) -> None:
        """Draw a single detection - box plus confidence label - on the canvas."""
        (x, y), _, (x_end, y_end), _ = detection["bbox"]
        cv2.rectangle(canvas, (x, y), (x_end, y_end), _BOX_COLOR, 2)

        label = f"{detection['text']} ({detection['confidence']:.2f})"
        label_x, label_y = x, max(y - 10, 20)

        (label_width, label_height), _ = cv2.getTextSize(
            label, _FONT, _FONT_SCALE, _FONT_THICKNESS
        )
        cv2.rectangle(
            canvas,
            (label_x, label_y - label_height - 5),
            (label_x + label_width, label_y + 5),
            _LABEL_BACKGROUND,
            -1,
        )
        cv2.putText(
            canvas,
            label,
            (label_x, label_y),
            _FONT,
            _FONT_SCALE,
            _LABEL_COLOR,
            _FONT_THICKNESS,
            cv2.LINE_AA,
        )

    @staticmethod
    def visualize_document(
        document_path: str,
        output_dir: str,
        stem: str,
        lang: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> List[str]:
        """Annotate an image or every page of a PDF.

        Args:
            document_path: Path to an image or PDF file.
            output_dir: Directory where annotated images are written.
            stem: Base name used for the generated files.
            lang: Tesseract language code. Defaults to the configured language.
            min_confidence: Minimum confidence (0-1) a detection must reach.

        Returns:
            Paths to the annotated images, in page order.
        """
        destination = Path(output_dir)
        destination.mkdir(parents=True, exist_ok=True)

        if not OCREngine.is_pdf(document_path):
            output_path = destination / f"boxes_{stem}.png"
            return [
                OCREngine.visualize_boxes(
                    document_path,
                    str(output_path),
                    lang=lang,
                    min_confidence=min_confidence,
                )
            ]

        outputs: List[str] = []
        with OCREngine.rasterized_pdf(document_path) as image_paths:
            for page_number, image_path in enumerate(image_paths, start=1):
                output_path = destination / f"boxes_{stem}_p{page_number}.png"
                outputs.append(
                    OCREngine.visualize_boxes(
                        image_path,
                        str(output_path),
                        lang=lang,
                        min_confidence=min_confidence,
                    )
                )
        return outputs
