# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Base: system libraries and runtime dependencies shared by every stage.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# opencv-python-headless ships prebuilt wheels, so no compiler toolchain is
# needed here; libglib2.0-0 and libgl1 are its only shared library needs.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libgl1 \
        libglib2.0-0 \
        tesseract-ocr \
        tesseract-ocr-spa \
        tesseract-ocr-eng \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Dev: adds the test and lint toolchain. Build with --target dev.
# ---------------------------------------------------------------------------
FROM base AS dev

COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/

CMD ["pytest", "tests/"]

# ---------------------------------------------------------------------------
# Runtime: the shipped image. Runs unprivileged.
# ---------------------------------------------------------------------------
FROM base AS runtime

RUN useradd --create-home --uid 1000 appuser

COPY src/ ./src/

RUN mkdir -p outputs && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "src/ocr/app.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.headless=true", \
            "--browser.gatherUsageStats=false"]
