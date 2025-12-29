"""OCR Engine module for text extraction and visualization using Tesseract-OCR."""

import os
import tempfile
from typing import Dict, Any, List
import streamlit as st
import pytesseract
from PIL import Image
import cv2
import numpy as np
import fitz


class OCREngine:
    """OCR Engine class for document text extraction and bounding box visualization."""

    @staticmethod
    @st.cache_data
    def configure_tesseract() -> None:
        """
        Configure Tesseract OCR settings.

        Note: Tesseract binary should be installed on the system.
        Docker image includes it via apt-get.
        """
        # Tesseract is configured via system installation
        # No runtime configuration needed for basic usage
        pass

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
        Extract text and bounding boxes from an image using Tesseract.

        Args:
            image_path: Path to the input image file.

        Returns:
            Dictionary containing:
                - file: filename
                - full_text: concatenated text from all detected lines
                - boxes: list of dictionaries with text, confidence, and bbox
                - total_lines: number of detected text lines
        """
        OCREngine.configure_tesseract()

        # Open image
        image = Image.open(image_path)

        # Get detailed data with bounding boxes
        data = pytesseract.image_to_data(
            image, lang="spa", output_type=pytesseract.Output.DICT
        )

        boxes = []
        full_text_parts = []

        # Process each detected word
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            # Filter out empty detections
            if int(data["conf"][i]) > 0 and data["text"][i].strip():
                x, y, w, h = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )
                text = data["text"][i]
                confidence = float(data["conf"][i]) / 100.0  # Convert to 0-1 range

                # Tesseract bbox format: [[x,y], [x+w,y], [x+w,y+h], [x,y+h]]
                bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

                boxes.append({"text": text, "confidence": confidence, "bbox": bbox})
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
        OCREngine.configure_tesseract()

        # Load image with opencv
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Get OCR data
        pil_image = Image.open(image_path)
        data = pytesseract.image_to_data(
            pil_image, lang="spa", output_type=pytesseract.Output.DICT
        )

        # Draw boxes and text
        n_boxes = len(data["text"])
        for i in range(n_boxes):
            if int(data["conf"][i]) > 0 and data["text"][i].strip():
                x, y, w, h = (
                    data["left"][i],
                    data["top"][i],
                    data["width"][i],
                    data["height"][i],
                )
                text = data["text"][i]
                confidence = float(data["conf"][i]) / 100.0

                # Draw green bounding box
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Draw red text label with confidence
                label = f"{text} ({confidence:.2f})"
                text_position = (x, max(y - 10, 20))

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
