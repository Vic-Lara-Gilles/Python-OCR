"""OCR Engine module for text extraction and visualization using PaddleOCR."""

import os
import tempfile
from typing import Dict, List, Any, Optional
import streamlit as st
from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import fitz


class OCREngine:
    """OCR Engine class for document text extraction and bounding box visualization."""

    @staticmethod
    @st.cache_resource
    def get_ocr() -> PaddleOCR:
        """
        Initialize and cache PaddleOCR model instance.

        Returns:
            PaddleOCR: Cached OCR model instance configured for Spanish language.
        """
        return PaddleOCR(
            use_angle_cls=True,
            lang="es",
            use_gpu=False,
            show_log=False,
            det_db_thresh=0.3,
            det_db_box_thresh=0.5,
            rec_batch_num=6,
        )

    @staticmethod
    def pdf_to_images(pdf_path: str) -> List[str]:
        """
        Convert PDF pages to images.

        Args:
            pdf_path: Path to the input PDF file.

        Returns:
            List of paths to temporary image files.
        """
        doc = fitz.open(pdf_path)
        image_paths = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            pix.save(temp_file.name)
            image_paths.append(temp_file.name)

        doc.close()
        return image_paths

    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        """
        Extract text and bounding boxes from an image.

        Args:
            image_path: Path to the input image file.

        Returns:
            Dictionary containing:
                - file: filename
                - full_text: concatenated text from all detected lines
                - boxes: list of dictionaries with text, confidence, and bbox
                - total_lines: number of detected text lines
        """
        ocr = OCREngine.get_ocr()
        result = ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            return {
                "file": os.path.basename(image_path),
                "full_text": "",
                "boxes": [],
                "total_lines": 0,
            }

        boxes = []
        full_text_parts = []

        for line in result[0]:
            bbox = line[0]
            text_info = line[1]
            text = text_info[0]
            confidence = text_info[1]

            boxes.append({"text": text, "confidence": float(confidence), "bbox": bbox})
            full_text_parts.append(text)

        return {
            "file": os.path.basename(image_path),
            "full_text": " ".join(full_text_parts),
            "boxes": boxes,
            "total_lines": len(boxes),
        }

    @staticmethod
    def generate_markdown(result: Dict[str, Any]) -> str:
        """
        Generate markdown formatted text from OCR result.

        Args:
            result: OCR extraction result dictionary.

        Returns:
            Markdown formatted string.
        """
        md_lines = []
        md_lines.append(f"# OCR Result: {result['file']}\n")

        if result.get("total_pages"):
            md_lines.append(f"**Total Pages:** {result['total_pages']}\n")

        md_lines.append(f"**Total Lines:** {result['total_lines']}\n")
        md_lines.append("---\n")
        md_lines.append("## Extracted Text\n")
        md_lines.append(result["full_text"])

        return "\n".join(md_lines)

    @staticmethod
    def generate_plain_text(result: Dict[str, Any]) -> str:
        """
        Generate plain text from OCR result.

        Args:
            result: OCR extraction result dictionary.

        Returns:
            Plain text string.
        """
        return result["full_text"]

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
        """
        Extract text from all pages of a PDF.

        Args:
            pdf_path: Path to the input PDF file.

        Returns:
            Dictionary containing combined results from all pages.
        """
        image_paths = OCREngine.pdf_to_images(pdf_path)
        all_boxes = []
        all_text_parts = []

        for idx, img_path in enumerate(image_paths):
            result = OCREngine.extract_text_and_boxes(img_path)

            # Add page number to each box
            for box in result["boxes"]:
                box["page"] = idx + 1
                all_boxes.append(box)

            if result["full_text"]:
                all_text_parts.append(f"[Page {idx + 1}] {result['full_text']}")

            # Clean up temp image
            os.remove(img_path)

        return {
            "file": os.path.basename(pdf_path),
            "full_text": "\n\n".join(all_text_parts),
            "boxes": all_boxes,
            "total_lines": len(all_boxes),
            "total_pages": len(image_paths),
        }

    @staticmethod
    def visualize_boxes(image_path: str, output_path: str) -> str:
        """
        Visualize bounding boxes on an image and save the result.

        Args:
            image_path: Path to the input image file.
            output_path: Path where the annotated image will be saved.

        Returns:
            Path to the saved annotated image.
        """
        ocr = OCREngine.get_ocr()
        result = ocr.ocr(image_path, cls=True)

        # Load image with opencv for better drawing performance
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        if result and result[0]:
            for line in result[0]:
                bbox = line[0]
                text = line[1][0]
                confidence = line[1][1]

                # Convert bbox to integer coordinates
                points = np.array(
                    [[int(p[0]), int(p[1])] for p in bbox], dtype=np.int32
                )

                # Draw green bounding box
                cv2.polylines(
                    image, [points], isClosed=True, color=(0, 255, 0), thickness=2
                )

                # Draw red text label with confidence
                label = f"{text} ({confidence:.2f})"
                text_position = (int(bbox[0][0]), max(int(bbox[0][1]) - 10, 20))

                # Add background for text
                (text_width, text_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
                )
                cv2.rectangle(
                    image,
                    (text_position[0], text_position[1] - text_height - 5),
                    (text_position[0] + text_width, text_position[1] + 5),
                    (255, 255, 255),
                    -1,
                )

                # Draw text in red
                cv2.putText(
                    image,
                    label,
                    text_position,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    1,
                    cv2.LINE_AA,
                )

        # Convert back to BGR and save
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output_path, image)
        return output_path
