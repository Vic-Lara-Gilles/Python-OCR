---
applyTo: '**'
---

# OCR System with Docker + Streamlit + PaddleOCR

## Project Overview

Fast OCR system for document recognition with table support.

**Tech Stack:**
- Docker (containerized deployment)
- Streamlit (web interface)
- PaddleOCR-VL (vision-language model for tables)
- Python 3.11

**Key Requirement:** Everything must be containerized - no local installation required.

## Project Structure

```
ocr-docker-mvp/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app.py
├── ocr_engine.py
├── .dockerignore
└── outputs/          # Auto-created for results
    ├── *.json        # OCR text results
    └── *.png         # Visualized boxes
```

## File Specifications

### Dockerfile

- **Base image:** `python:3.11-slim`
- **System dependencies:** libsm6, libxext6, libxrender-dev, libgomp1, gcc, g++
- **Port:** 8501
- **Healthcheck:** `curl http://localhost:8501/_stcore/health`
- **Entry command:** `streamlit run app.py --server.port=8501 --server.address=0.0.0.0`

### docker-compose.yml

- **Service name:** ocr-app
- **Container name:** ocr-mvp-streamlit
- **Ports:** 8501:8501
- **Volumes:**
  - `./outputs:/app/outputs` (save OCR results)
  - `./uploads:/app/uploads` (temporary uploads)
- **Environment:** `PYTHONUNBUFFERED=1`
- **Restart policy:** unless-stopped

### requirements.txt

```
streamlit==1.39.0
paddleocr[doc-parser]==2.8.1
pillow==10.4.0
opencv-python==4.10.1.26
numpy==1.26.4
pandas==2.2.3
torch==2.3.1
torchvision==0.18.1
```

### ocr_engine.py

**Class:** `OCREngine`

**Methods:**

#### 1. `get_ocr()` - Cached OCR Model

- Decorator: `@st.cache_resource`
- PaddleOCR parameters:
  - `use_angle_cls=True`
  - `lang="es"` (Spanish support)
  - `use_doc_orientation_classify=False`
  - `use_doc_unwarping=False`
- Returns: PaddleOCR model instance

#### 2. `extract_text_and_boxes(image_path: str) -> dict`

- Execute: `ocr.ocr(image_path, cls=True)`
- Returns dict:
  ```python
  {
    "file": str,           # filename
    "full_text": str,      # concatenated text
    "boxes": [
      {
        "text": str,
        "confidence": float,
        "bbox": list
      }
    ],
    "total_lines": int     # number of detected lines
  }
  ```

#### 3. `visualize_boxes(image_path: str, output_path: str) -> str`

- Opens image with PIL
- Draws bounding boxes in **green** `(0, 255, 0)`
- Places text in **red** `(255, 0, 0)` over boxes
- Saves annotated image
- Returns: path to saved file

### app.py (Streamlit UI)

**Page Configuration:**
- Title: "OCR MVP (Docker + PaddleOCR-VL)"
- Layout: wide
- Auto-create `outputs/` directory

**Sidebar:**
- Radio buttons for task selection:
  1. Extract Text
  2. Visualize Boxes
  3. Multiple Images
- Stack information display

**Main Content Tabs:**

#### Tab 1: Process

**Task 1 - Extract Text:**
- File uploader: single file (JPG, PNG, WEBP)
- Layout: 2 columns
  - Col 1: Display uploaded image
  - Col 2: Show JSON result
- Execute `extract_text_and_boxes()`
- Download JSON button
- Save to: `outputs/ocr_{filename}.json`

**Task 2 - Visualize Boxes:**
- File uploader: single file
- Execute `visualize_boxes()`
- Layout: 2 columns
  - Col 1: Original image
  - Col 2: Image with boxes
- Download annotated image button
- Save to: `outputs/boxes_{filename}.png`

**Task 3 - Multiple Images:**
- File uploader: multiple files
- Process files in loop
- Show progress: "Processed 1/10: file.jpg"
- Generate DataFrame:
  - Columns: Filename, Lines, Text (first 100 chars)
- Display dataframe
- Download CSV button

#### Tab 2: Results

- List all files in `outputs/` directory
- File type handling:
  - `*.json`: Display with `st.json()`
  - `*.png`: Display image
- Sort order: Reverse chronological (most recent first)

### .dockerignore

```
__pycache__
*.pyc
.git
.env
.vscode
.DS_Store
venv
.venv
temp_*
```

## Code Style Requirements

1. **No decorative symbols:** No emojis, emoticons, or decorative symbols in code, comments, or commits
2. **Pure CSS:** No Tailwind CSS or CSS frameworks
3. **Conventional Commits:** Follow strict commit message format
4. **Language usage:**
   - Code and commits: English
   - User interface: Spanish
5. **Naming conventions:**
   - Clear, descriptive variable and function names
   - Proper Python type hints
6. **Comments:** English only, concise and technical

## Usage Instructions

### With Docker (Recommended)

```bash
docker-compose up --build
```

Then open: http://localhost:8501

### Without Docker (Local Development)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Implementation Guidelines

### Language & Localization
- Code, comments, commits: **English**
- Streamlit UI text: **Spanish**
- OCR language: Spanish (`lang="es"`)

### File Management
- Auto-create directories: `outputs/`, `uploads/`
- Save uploaded images temporarily
- Clean up temp files (`temp_*`) after processing
- PaddleOCR models download automatically on first run

### Visual Settings
- Bounding boxes: Green `(0, 255, 0)`
- Text labels: Red `(255, 0, 0)`
- Spinner messages: Clear and concise (e.g., "Running OCR...")

### UI Components
- Include stack information in markdown
- Display processing progress for batch operations
- Show descriptive error messages on OCR failures

## Technical Details

### PaddleOCR Configuration
- **PaddleOCR-VL:** Specialized for tables and complex document AI
- **Package:** `paddleocr[doc-parser]` includes PaddleOCR-VL and PP-StructureV3
- **Supported formats:** JPG, JPEG, PNG, WEBP

### Data Persistence
- JSON results must be downloadable from UI
- Results tab shows persistent file history (saved in `outputs/`)
- Error handling: Display descriptive messages on OCR failures

### Security
- Validate file types (images only)
- Clean temporary files after processing
- Do not store sensitive data without encryption
- Consider upload size limits for production

## Deliverables

Generate **6 complete, production-ready files:**

1. `Dockerfile`
2. `docker-compose.yml`
3. `requirements.txt`
4. `ocr_engine.py`
5. `app.py`
6. `.dockerignore`

### Quality Requirements

- **Complete code:** No TODOs, no placeholders, no omissions
- **Functional:** Ready to run with `docker-compose up --build`
- **Type hints:** All Python functions properly annotated
- **Error handling:** Proper try-catch blocks with user-friendly messages
- **Comments:** Technical, concise, in English

## Commit Message Format

Follow Conventional Commits specification:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation only
- `refactor:` Code restructuring
- `test:` Adding/updating tests
- `chore:` Maintenance tasks

**Example:** `feat(ocr): add table detection with PaddleOCR-VL`
