# Clean Code Guidelines - Python-OCR

## Table of Contents
- [Naming Conventions](#naming-conventions)
- [Functions](#functions)
- [Classes](#classes)
- [Comments and Documentation](#comments-and-documentation)
- [Error Handling](#error-handling)
- [Type Hints](#type-hints)
- [Code Organization](#code-organization)
- [Best Practices](#best-practices)

## Naming Conventions

### Variables

**Rule**: Use descriptive `snake_case` names that reveal intention.

✅ **Good**:
```python
image_path = "/path/to/image.jpg"
full_text = result["full_text"]
total_lines = len(boxes)
confidence_threshold = 0.5
```

❌ **Bad**:
```python
ip = "/path/to/image.jpg"  # Too short
imgPth = "..."             # Abbreviations
x = result["full_text"]    # Meaningless
n = len(boxes)             # Single letter
```

### Functions

**Rule**: Use verb phrases in `snake_case` that describe actions.

✅ **Good**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Clear verb phrase indicating action."""
    pass

def visualize_boxes(image_path: str, output_path: str) -> str:
    """Verb + noun describes exactly what it does."""
    pass

def generate_markdown(result: Dict[str, Any]) -> str:
    """Generate indicates creation of output."""
    pass
```

❌ **Bad**:
```python
def process(data):           # Too vague
    pass

def get_data():             # What data?
    pass

def do_ocr_stuff(img):      # Unprofessional
    pass
```

### Classes

**Rule**: Use `PascalCase` nouns or noun phrases.

✅ **Good**:
```python
class OCREngine:
    """Noun phrase - clear purpose."""
    pass

class TextExtractor:
    """Noun - describes entity."""
    pass

class BoundingBoxVisualizer:
    """Descriptive noun phrase."""
    pass
```

❌ **Bad**:
```python
class ocr_engine:          # Wrong case
    pass

class DoOCR:              # Verb phrase (should be noun)
    pass

class Helper:             # Too generic
    pass
```

### Constants

**Rule**: Use `UPPER_SNAKE_CASE` for module-level constants.

✅ **Good**:
```python
OUTPUT_DIR = Path("outputs")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
DEFAULT_LANGUAGE = "spa"
TESSERACT_CONFIDENCE_THRESHOLD = 0.5
```

❌ **Bad**:
```python
outputDir = Path("outputs")     # Wrong case
maxsize = 10000000             # Not clear
lang = "spa"                   # Too short
```

## Functions

### Single Responsibility Principle

**Rule**: Each function should do one thing and do it well.

✅ **Good**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Only extracts text and boxes - nothing else."""
    OCREngine.configure_tesseract()
    image = Image.open(image_path)
    data = pytesseract.image_to_data(image, lang="spa", output_type=pytesseract.Output.DICT)

    boxes = _process_ocr_data(data)
    full_text = _combine_text(boxes)

    return {
        "file": os.path.basename(image_path),
        "full_text": full_text,
        "boxes": boxes,
        "total_lines": len(boxes),
    }

def _process_ocr_data(data: dict) -> List[Dict[str, Any]]:
    """Helper function - processes raw OCR data."""
    boxes = []
    n_boxes = len(data["text"])
    for i in range(n_boxes):
        if int(data["conf"][i]) > 0 and data["text"][i].strip():
            boxes.append(_create_box(data, i))
    return boxes

def _create_box(data: dict, index: int) -> Dict[str, Any]:
    """Helper function - creates single box structure."""
    x, y, w, h = data["left"][index], data["top"][index], data["width"][index], data["height"][index]
    return {
        "text": data["text"][index],
        "confidence": float(data["conf"][index]) / 100.0,
        "bbox": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
    }
```

❌ **Bad**:
```python
def extract_and_save_and_visualize_and_format(image_path: str, output_path: str, format: str):
    """Does too many things - violates SRP."""
    # Extract text
    result = pytesseract.image_to_data(...)

    # Visualize boxes
    cv2.rectangle(...)

    # Save to file
    with open(...) as f:
        f.write(...)

    # Format output
    if format == "json":
        return json.dumps(...)
    elif format == "markdown":
        return generate_markdown(...)
```

### Function Size

**Rule**: Functions should be small - ideally 10-20 lines max.

✅ **Good**:
```python
def visualize_boxes(image_path: str, output_path: str) -> str:
    """Short, focused function."""
    OCREngine.configure_tesseract()

    image = _load_and_convert_image(image_path)
    data = _get_ocr_data(image_path)

    _draw_boxes_on_image(image, data)

    cv2.imwrite(output_path, _convert_to_bgr(image))
    return output_path
```

❌ **Bad**:
```python
def visualize_boxes(image_path: str, output_path: str) -> str:
    """Too long - 100+ lines with all logic inline."""
    # 30 lines of image loading...
    # 40 lines of drawing logic...
    # 20 lines of text rendering...
    # 10 lines of saving...
    pass
```

### Function Arguments

**Rule**: Limit to 3 parameters. Use objects for more.

✅ **Good**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """1 parameter - ideal."""
    pass

def visualize_boxes(image_path: str, output_path: str) -> str:
    """2 parameters - good."""
    pass

# If more parameters needed, use config object
@dataclass
class OCRConfig:
    language: str = "spa"
    confidence_threshold: float = 0.5
    dpi: int = 300

def extract_with_config(image_path: str, config: OCRConfig) -> Dict[str, Any]:
    """2 parameters using config object."""
    pass
```

❌ **Bad**:
```python
def extract_text(image_path, lang, dpi, threshold, mode, format, debug, verbose, output_dir):
    """Too many parameters - hard to remember order."""
    pass
```

### Return Values

**Rule**: Be consistent with return types. Avoid flag returns.

✅ **Good**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Always returns same structure."""
    return {
        "file": "...",
        "full_text": "...",
        "boxes": [...],
        "total_lines": 0
    }

def validate_image(image_path: str) -> bool:
    """Returns boolean for validation."""
    return os.path.exists(image_path) and image_path.endswith(('.jpg', '.png'))
```

❌ **Bad**:
```python
def extract_text(image_path: str):
    """Inconsistent return types."""
    try:
        return {"success": True, "data": ...}
    except:
        return {"success": False, "error": ...}  # Different structure

def process_image(path: str) -> int:
    """Returns int as flag - unclear meaning."""
    if success:
        return 1
    elif partial:
        return 0
    else:
        return -1
```

## Classes

### Class Size

**Rule**: Classes should be small and focused (< 300 lines).

✅ **Good**:
```python
class OCREngine:
    """Single responsibility - OCR operations only."""

    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        pass

    @staticmethod
    def visualize_boxes(image_path: str, output_path: str) -> str:
        pass

    @staticmethod
    def generate_markdown(result: Dict[str, Any]) -> str:
        pass
```

### Cohesion

**Rule**: Class methods should use class data or call each other.

✅ **Good**:
```python
class TextFormatter:
    """High cohesion - all methods work with result data."""

    def __init__(self, result: Dict[str, Any]):
        self.result = result
        self.file_name = result["file"]
        self.full_text = result["full_text"]

    def to_markdown(self) -> str:
        """Uses self.result."""
        return self._format_header() + self.full_text

    def to_plain_text(self) -> str:
        """Uses self.full_text."""
        return self.full_text

    def _format_header(self) -> str:
        """Helper used by other methods."""
        return f"# {self.file_name}\n\n"
```

❌ **Bad**:
```python
class Utilities:
    """Low cohesion - unrelated methods."""

    def extract_text(self, image_path: str):
        pass

    def send_email(self, to: str, subject: str):
        pass

    def calculate_tax(self, amount: float):
        pass
```

## Comments and Documentation

### Docstrings

**Rule**: All public functions/classes must have docstrings.

✅ **Good**:
```python
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

    Raises:
        FileNotFoundError: If image file does not exist.
        ValueError: If image format is not supported.

    Example:
        >>> result = OCREngine.extract_text_and_boxes("invoice.jpg")
        >>> print(result["full_text"])
        "Invoice Number: 12345..."
    """
    pass
```

❌ **Bad**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    # Extract text
    pass
```

### Inline Comments

**Rule**: Explain WHY, not WHAT. Code should be self-explanatory.

✅ **Good**:
```python
# Convert confidence from 0-100 range to 0-1 range for consistency with ML models
confidence = float(data["conf"][i]) / 100.0

# Tesseract bbox format is [x, y, w, h], convert to 4 corner points for OpenCV
bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

# Clean up temp files to avoid disk space exhaustion in long-running processes
if os.path.exists(temp_path):
    os.remove(temp_path)
```

❌ **Bad**:
```python
# Divide by 100
confidence = float(data["conf"][i]) / 100.0

# Create bbox
bbox = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

# Remove file
if os.path.exists(temp_path):
    os.remove(temp_path)
```

### TODOs

**Rule**: Include name and date. Track in issue tracker.

✅ **Good**:
```python
# TODO(username, 2025-01-08): Add support for TIFF format
# Issue: #42
def extract_text_from_tiff(tiff_path: str) -> Dict[str, Any]:
    raise NotImplementedError("TIFF support coming in v2.0")
```

❌ **Bad**:
```python
# TODO: fix this
# FIXME
# HACK
```

## Error Handling

### Specific Exceptions

**Rule**: Catch specific exceptions, not bare `except`.

✅ **Good**:
```python
try:
    result = OCREngine.extract_text_and_boxes(temp_path)
except FileNotFoundError:
    st.error(f"File not found: {temp_path}")
except PIL.UnidentifiedImageError:
    st.error("Invalid image format. Please upload JPG, PNG, or WEBP.")
except pytesseract.TesseractError as e:
    st.error(f"OCR processing failed: {str(e)}")
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
    logger.exception("Unexpected error in OCR processing")
```

❌ **Bad**:
```python
try:
    result = OCREngine.extract_text_and_boxes(temp_path)
except:
    st.error("Error occurred")  # Too generic
    pass  # Silently swallowing exceptions
```

### Finally Blocks

**Rule**: Use finally for cleanup, especially with files.

✅ **Good**:
```python
temp_path = None
try:
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    result = OCREngine.extract_text_and_boxes(temp_path)
except Exception as e:
    st.error(f"Error: {str(e)}")
finally:
    # Always cleanup, even if exception occurred
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
```

### Early Returns

**Rule**: Validate early and return/raise early.

✅ **Good**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Validate early, exit early."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    if not image_path.endswith(('.jpg', '.png', '.jpeg', '.webp')):
        raise ValueError(f"Unsupported format: {image_path}")

    # Main logic here - only executes if validation passed
    image = Image.open(image_path)
    # ...
```

❌ **Bad**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Nested conditions - hard to read."""
    if os.path.exists(image_path):
        if image_path.endswith(('.jpg', '.png')):
            # Main logic deeply nested
            image = Image.open(image_path)
            # ...
        else:
            raise ValueError("Invalid format")
    else:
        raise FileNotFoundError("File not found")
```

## Type Hints

### Function Signatures

**Rule**: All public functions must have complete type hints.

✅ **Good**:
```python
from typing import Dict, Any, List

def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Fully typed."""
    pass

def visualize_boxes(image_path: str, output_path: str) -> str:
    """Clear input and output types."""
    pass

def pdf_to_images(pdf_path: str) -> List[str]:
    """List type specified."""
    pass
```

❌ **Bad**:
```python
def extract_text_and_boxes(image_path):
    """No type hints."""
    pass

def visualize_boxes(image_path: str, output_path):
    """Partial type hints."""
    pass
```

### Complex Types

**Rule**: Use typing module for complex types.

✅ **Good**:
```python
from typing import Dict, List, Optional, Union, Tuple

Box = Dict[str, Union[str, float, List[List[int]]]]
OCRResult = Dict[str, Union[str, int, List[Box]]]

def extract_text_and_boxes(image_path: str) -> OCRResult:
    """Type alias for complex structure."""
    pass

def find_box_by_text(boxes: List[Box], text: str) -> Optional[Box]:
    """Optional for nullable return."""
    for box in boxes:
        if box["text"] == text:
            return box
    return None
```

### Variables

**Rule**: Type hint variables when type is not obvious.

✅ **Good**:
```python
# Clear from assignment - no hint needed
image_path = "invoice.jpg"
total_lines = 42

# Not obvious - type hint helps
boxes: List[Dict[str, Any]] = []
result: Optional[OCRResult] = None
config: OCRConfig = OCRConfig(language="spa")
```

## Code Organization

### Import Order

**Rule**: Follow PEP 8 import order.

✅ **Good**:
```python
# 1. Standard library imports
import os
import json
from pathlib import Path
from typing import Dict, Any, List

# 2. Related third-party imports
import streamlit as st
import pandas as pd
from PIL import Image
import cv2
import numpy as np
import pytesseract
import fitz

# 3. Local application imports
from ocr.engine import OCREngine
from ocr.config import settings
```

### File Structure

**Rule**: Organize code top-down by abstraction level.

✅ **Good**:
```python
"""Module docstring at top."""

# Imports
import os
from typing import Dict, Any

# Constants
OUTPUT_DIR = Path("outputs")
MAX_FILE_SIZE = 10 * 1024 * 1024

# Classes (public first, then private)
class OCREngine:
    """Public class."""
    pass

class _InternalHelper:
    """Private class."""
    pass

# Public functions
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Public API."""
    pass

# Private helper functions
def _process_ocr_data(data: dict) -> List[Dict[str, Any]]:
    """Private helper."""
    pass
```

### Module Size

**Rule**: Keep modules focused and under 500 lines.

✅ **Good**:
```
src/ocr/
├── __init__.py           # 10 lines
├── engine.py             # 259 lines - core OCR
├── formatters.py         # 100 lines - formatting (future)
└── validators.py         # 50 lines - validation (future)
```

## Best Practices

### DRY (Don't Repeat Yourself)

✅ **Good**:
```python
def save_result(result: Dict[str, Any], base_name: str, format: str) -> Path:
    """Reusable save function."""
    output_path = OUTPUT_DIR / f"ocr_{base_name}.{format}"

    if format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    elif format == "txt":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["full_text"])

    return output_path

# Use in multiple places
save_result(result, filename, "json")
save_result(result, filename, "txt")
```

❌ **Bad**:
```python
# Repeated code in multiple places
json_path = OUTPUT_DIR / f"ocr_{filename}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

txt_path = OUTPUT_DIR / f"ocr_{filename}.txt"
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(result["full_text"])
```

### YAGNI (You Aren't Gonna Need It)

✅ **Good**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Simple implementation - no unnecessary features."""
    # Only what's needed now
    pass
```

❌ **Bad**:
```python
def extract_text_and_boxes(
    image_path: str,
    cache: bool = False,        # Not used
    async_mode: bool = False,   # Not implemented
    callback: Callable = None,  # No callbacks needed
    timeout: int = 30,          # Not enforced
    retry: int = 3,             # No retry logic
) -> Dict[str, Any]:
    """Over-engineered with unused features."""
    pass
```

### KISS (Keep It Simple, Stupid)

✅ **Good**:
```python
def generate_plain_text(result: Dict[str, Any]) -> str:
    """Simple and direct."""
    return result["full_text"]
```

❌ **Bad**:
```python
def generate_plain_text(result: Dict[str, Any]) -> str:
    """Over-complicated."""
    text_parts = []
    for box in result["boxes"]:
        if box["text"] not in text_parts:
            text_parts.append(box["text"])
    return " ".join(text_parts)  # Same as result["full_text"]
```

## Checklist

Before committing code, verify:

- [ ] Functions are small (< 20 lines ideally)
- [ ] Functions do one thing
- [ ] Variables have descriptive names
- [ ] All public functions have docstrings
- [ ] Type hints are complete
- [ ] No code duplication (DRY)
- [ ] No over-engineering (YAGNI)
- [ ] Simple solutions (KISS)
- [ ] Proper error handling
- [ ] Tests cover new code
- [ ] Imports organized by PEP 8
- [ ] No commented-out code
- [ ] No debug print statements

## Tools

### Linting
```bash
# Ruff (modern fast linter)
ruff check src/

# Fix automatically
ruff check --fix src/
```

### Formatting
```bash
# Black (standard formatter)
black src/

# Ruff format (compatible with Black)
ruff format src/
```

### Type Checking
```bash
# Mypy
mypy src/ --strict
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

## References

- **Clean Code** by Robert C. Martin
- **The Pragmatic Programmer** by Hunt & Thomas
- **Python PEP 8** - Style Guide
- **Google Python Style Guide**
- **Effective Python** by Brett Slatkin
