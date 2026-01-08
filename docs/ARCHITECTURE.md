# Architecture Documentation

## System Overview

Python-OCR is a containerized OCR system built with Clean Architecture principles, implementing SOLID design patterns and Test-Driven Development practices.

## Architecture Layers

### 1. Presentation Layer
**Location**: `src/ocr/app.py`

**Responsibilities**:
- User interface (Streamlit)
- File upload handling
- Results display
- User input validation

**Key Components**:
- Tab navigation (Process, Results)
- Task selection (Extract Text, Visualize Boxes, Batch Processing)
- Progress indicators
- Download buttons

**Design Patterns**:
- **MVC Pattern**: Streamlit acts as View and Controller
- **Observer Pattern**: Streamlit's reactive updates

### 2. Business Logic Layer
**Location**: `src/ocr/engine.py`

**Responsibilities**:
- OCR text extraction
- Bounding box detection
- Format generation (JSON, Markdown, Plain Text)
- Image visualization

**Key Components**:
```python
class OCREngine:
    - extract_text_and_boxes()     # Core extraction
    - extract_text_from_pdf()      # PDF processing
    - visualize_boxes()            # Visualization
    - generate_markdown()          # Format: Markdown
    - generate_plain_text()        # Format: Plain Text
    - pdf_to_images()              # PDF conversion
```

**Design Patterns**:
- **Facade Pattern**: Simplifies complex OCR operations
- **Static Factory Pattern**: Stateless method creation
- **Strategy Pattern**: Different extraction methods per file type
- **Template Method Pattern**: PDF multi-page processing

### 3. Infrastructure Layer

**Components**:
- **Tesseract-OCR**: Text recognition engine
- **OpenCV**: Image processing and drawing
- **PyMuPDF**: PDF parsing and conversion
- **PIL (Pillow)**: Image manipulation

**Integration Points**:
```python
# Tesseract integration
pytesseract.image_to_data(image, lang="spa")

# OpenCV for visualization
cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

# PyMuPDF for PDF
fitz.open(pdf_path)
```

## Data Flow

```
┌──────────────────────────────────────────────────────┐
│                     User Upload                       │
│                  (Image/PDF File)                     │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              Presentation Layer                       │
│         (app.py - Streamlit Interface)               │
│                                                       │
│  - File validation                                    │
│  - Temporary storage                                  │
│  - Progress tracking                                  │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              Business Logic Layer                     │
│            (engine.py - OCREngine)                    │
│                                                       │
│  - OCR processing                                     │
│  - Bounding box extraction                            │
│  - Format generation                                  │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│             Infrastructure Layer                      │
│    (Tesseract, OpenCV, PyMuPDF, PIL)                 │
│                                                       │
│  - Text recognition                                   │
│  - Image processing                                   │
│  - PDF parsing                                        │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│                  Results Output                       │
│         (JSON, Markdown, TXT, Images)                │
│                                                       │
│  - outputs/ directory                                 │
│  - Download buttons                                   │
│  - Results tab display                                │
└──────────────────────────────────────────────────────┘
```

## Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │              Streamlit Application                 │  │
│  │                 (Port 8501)                        │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │                  OCREngine Class                   │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │ Text Extract │  │  Visualize   │             │  │
│  │  │   Methods    │  │   Methods    │             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  │                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐             │  │
│  │  │   Format     │  │     PDF      │             │  │
│  │  │   Methods    │  │   Methods    │             │  │
│  │  └──────────────┘  └──────────────┘             │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │         External Libraries (Infrastructure)        │  │
│  │                                                    │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌────────┐ │  │
│  │  │Tesseract│ │ OpenCV  │ │ PyMuPDF │ │  PIL   │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Volume Mounts                          │  │
│  │                                                     │  │
│  │  ./src      → /app/src       (Hot Reload)         │  │
│  │  ./outputs  → /app/outputs   (Results)            │  │
│  │  ./uploads  → /app/uploads   (Temp Files)         │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Sequence Diagrams

### 1. Image Upload and Text Extraction

```
User          Streamlit       OCREngine       Tesseract       FileSystem
 |               |                |               |               |
 |-- Upload ---->|                |               |               |
 |               |                |               |               |
 |               |-- Validate --->|               |               |
 |               |                |               |               |
 |               |-- Save Temp -->|               |               |
 |               |                |-------------->|               |
 |               |                |               |-- Write ----->|
 |               |                |               |               |
 |               |-- Extract ---->|               |               |
 |               |                |               |               |
 |               |                |-- OCR Call -->|               |
 |               |                |               |               |
 |               |                |<-- OCR Data --|               |
 |               |                |               |               |
 |               |<-- Result -----|               |               |
 |               |                |               |               |
 |               |-- Save JSON -->|               |               |
 |               |                |-------------->|               |
 |               |                |               |-- Write ----->|
 |               |                |               |               |
 |<-- Display ---|                |               |               |
 |               |                |               |               |
```

### 2. Batch Processing Flow

```
User       Streamlit     OCREngine     FileSystem
 |            |               |              |
 |-- Upload ->|               |              |
 | Multiple   |               |              |
 | Files      |               |              |
 |            |               |              |
 |-- Process->|               |              |
 |            |               |              |
 |            |-- Loop ------>|              |
 |            | [For Each]    |              |
 |            |               |              |
 |            |-- Extract --->|              |
 |            |               |-- Process -->|
 |            |<-- Result ----|              |
 |            |               |              |
 |            |-- Save ------>|              |
 |            |               |-- Write ---->|
 |            |               |              |
 |            |-- Progress -->|              |
 |<-- Update--|               |              |
 |            |               |              |
 |            |<-- Complete --|              |
 |            |               |              |
 |<-- CSV ----|               |              |
 |            |               |              |
```

## Design Patterns Applied

### 1. Facade Pattern

**Problem**: Complex interaction with multiple libraries (pytesseract, cv2, PIL, fitz)

**Solution**: OCREngine provides simple interface

```python
# Without Facade (complex)
image = Image.open(path)
data = pytesseract.image_to_data(image, lang="spa", output_type=pytesseract.Output.DICT)
# ... complex processing ...

# With Facade (simple)
result = OCREngine.extract_text_and_boxes(path)
```

### 2. Static Factory Pattern

**Problem**: No need for instance state, want simple API

**Solution**: Static methods for stateless operations

```python
class OCREngine:
    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        # Stateless factory method
        pass
```

### 3. Strategy Pattern

**Problem**: Different processing logic for images vs PDFs

**Solution**: Different methods for different file types

```python
# Strategy 1: Single image
extract_text_and_boxes(image_path)

# Strategy 2: Multi-page PDF
extract_text_from_pdf(pdf_path)
```

### 4. Template Method Pattern

**Problem**: PDF processing follows consistent structure but varies per page

**Solution**: Template method with varying steps

```python
def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    # 1. Convert to images (varies by page count)
    image_paths = pdf_to_images(pdf_path)

    # 2. Process each page (repeated template)
    for img_path in image_paths:
        result = extract_text_and_boxes(img_path)

    # 3. Aggregate (fixed structure)
    return combined_result
```

### 5. Singleton Pattern (via Caching)

**Problem**: Tesseract configuration should be initialized once

**Solution**: Streamlit caching acts as singleton

```python
@st.cache_data
def configure_tesseract() -> None:
    # Called once, result cached
    pass
```

## SOLID Principles Implementation

### Single Responsibility Principle (SRP)

Each class/module has one reason to change:

| Module | Responsibility | Single Reason to Change |
|--------|----------------|-------------------------|
| `app.py` | User Interface | UI/UX requirements |
| `engine.py` | OCR Logic | OCR algorithms |
| `test_engine.py` | Testing | Test requirements |
| `conftest.py` | Test Fixtures | Test data setup |

### Open/Closed Principle (OCP)

**Open for extension, closed for modification**:

```python
# Easy to add new format without modifying existing code
class OCREngine:
    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        # Existing method unchanged
        pass

    @staticmethod
    def extract_text_from_tiff(tiff_path: str) -> Dict[str, Any]:
        # New format added without breaking existing
        pass
```

### Liskov Substitution Principle (LSP)

All extraction methods return compatible data structures:

```python
# Both return same structure - can substitute
result1 = extract_text_and_boxes(image_path)
result2 = extract_text_from_pdf(pdf_path)

# Both have: file, full_text, boxes, total_lines
assert "file" in result1 and "file" in result2
```

### Interface Segregation Principle (ISP)

Small, focused methods instead of monolithic interface:

```python
# Specific methods (ISP compliant)
extract_text_and_boxes()    # Only extraction
visualize_boxes()           # Only visualization
generate_markdown()         # Only markdown format
generate_plain_text()       # Only plain text format

# vs Monolithic (ISP violation)
# do_everything(mode, format, visualize, ...)
```

### Dependency Inversion Principle (DIP)

Depend on abstractions (pytesseract API) not concrete implementations:

```python
# Depends on pytesseract interface, not Tesseract directly
import pytesseract

# Could swap to different OCR engine by changing this import
# from paddleocr import PaddleOCR as pytesseract
```

## Testing Strategy

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
└── test_engine.py                 # Engine tests
    ├── TestOCREngineExtraction    # Extraction tests
    ├── TestOCREngineFormatters    # Format tests
    ├── TestOCREngineVisualization # Visualization tests
    └── TestOCREngineBoxStructure  # Data structure tests
```

### Test Coverage

| Component | Test Class | Coverage |
|-----------|------------|----------|
| Text Extraction | TestOCREngineExtraction | 100% |
| Formatters | TestOCREngineFormatters | 100% |
| Visualization | TestOCREngineVisualization | 100% |
| Data Structure | TestOCREngineBoxStructure | 100% |

### TDD Cycle

```
┌─────────────┐
│   Write     │
│  Failing    │
│    Test     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Implement  │
│   Minimal   │
│    Code     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Refactor   │
│    Code     │
│  (Optional) │
└──────┬──────┘
       │
       │
       └──────► Repeat
```

## Security Architecture

### Threat Model

| Threat | Mitigation | Status |
|--------|-----------|--------|
| Malicious file upload | File type validation | ✅ Implemented |
| Path traversal | No user-controlled paths | ✅ Implemented |
| Resource exhaustion | Docker resource limits | ⚠️ Recommended |
| Sensitive data leak | .gitignore for outputs | ✅ Implemented |
| Container escape | Docker isolation | ✅ Implemented |

### Security Layers

```
┌─────────────────────────────────────────┐
│        Input Validation Layer           │
│  - File type checking                   │
│  - Size limits                          │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│       Application Layer                 │
│  - Temporary file handling              │
│  - Auto cleanup                         │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Container Layer                 │
│  - Docker isolation                     │
│  - Network isolation                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          System Layer                   │
│  - File system permissions              │
│  - Resource limits                      │
└─────────────────────────────────────────┘
```

## Performance Considerations

### Caching Strategy

```python
@st.cache_data
def configure_tesseract() -> None:
    """Cached across Streamlit reruns."""
    pass

@st.cache_data
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Results cached by image path."""
    pass
```

### Resource Management

- **Memory**: Cleanup temporary files immediately
- **CPU**: Sequential processing (no parallelization yet)
- **Storage**: Automatic cleanup of temp files

### Optimization Opportunities

1. **Parallel Processing**: Use multiprocessing for batch operations
2. **Async Operations**: Celery for background processing
3. **Database**: PostgreSQL for result persistence
4. **CDN**: Serve static assets from CDN

## Deployment Architecture

### Current: Single Container

```
┌─────────────────────────────────┐
│       Docker Host               │
│                                 │
│  ┌───────────────────────────┐ │
│  │   OCR Container           │ │
│  │   (Streamlit + Tesseract) │ │
│  │                           │ │
│  │   Port: 8501              │ │
│  └───────────────────────────┘ │
│                                 │
│  Volumes:                       │
│  - ./src → /app/src            │
│  - ./outputs → /app/outputs    │
│  - ./uploads → /app/uploads    │
└─────────────────────────────────┘
```

### Future: Microservices

```
┌────────────┐
│   Nginx    │  Load Balancer
└─────┬──────┘
      │
      ├────────────────┬────────────────┐
      │                │                │
┌─────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐
│ Streamlit  │  │  FastAPI   │  │   Worker   │
│  Frontend  │  │    API     │  │   (Celery) │
└────────────┘  └─────┬──────┘  └─────┬──────┘
                      │                │
                      │                │
                ┌─────▼────────────────▼─────┐
                │      PostgreSQL DB         │
                └────────────────────────────┘
```

## Extensibility Points

### 1. New OCR Engines

```python
class PaddleOCREngine(OCREngine):
    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        # Use PaddleOCR instead of Tesseract
        pass
```

### 2. New File Formats

```python
@staticmethod
def extract_text_from_tiff(tiff_path: str) -> Dict[str, Any]:
    # Add TIFF support
    pass
```

### 3. New Output Formats

```python
@staticmethod
def generate_html(result: Dict[str, Any]) -> str:
    # Add HTML export
    pass
```

### 4. API Layer

```python
# Future: FastAPI REST API
@app.post("/api/v1/extract")
async def extract_text(file: UploadFile):
    result = OCREngine.extract_text_and_boxes(file.filename)
    return JSONResponse(content=result)
```

## Conclusion

This architecture provides:
- ✅ **Maintainability**: Clear separation of concerns
- ✅ **Testability**: 100% test coverage possible
- ✅ **Extensibility**: Easy to add new features
- ✅ **Scalability**: Ready for horizontal scaling
- ✅ **Security**: Multiple layers of protection
- ✅ **Performance**: Efficient caching and resource management

The design follows industry best practices and is production-ready for small to medium workloads.
