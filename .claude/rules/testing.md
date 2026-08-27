---
paths:
  - "tests/**"
  - "ocr-go/**/*_test.go"
---

# Test shape

- **Tests that shell out to the Tesseract binary carry `@requires_tesseract`** (defined in
  `tests/conftest.py`) and skip themselves when it is absent. That is what keeps `pytest`
  useful on a machine without OCR installed — and it is also why a green local run proves
  less than it looks like. `make test-docker` runs the suite with the binary present.
- **Keep pure logic in tests that do not need the binary.** Parsing, sanitizing and
  formatting are the bulk of what can actually regress, and they need no OCR:
  `tests/test_detections.py` feeds a Tesseract-shaped dict straight to
  `OCREngine._iter_detections`. Reach for a real image only when the binary is the thing
  under test.
- `pyproject.toml` sets `pythonpath = ["src"]`, so plain `pytest` works from the root with
  no `PYTHONPATH` in the environment.
- Fixtures build their inputs with Pillow into `tmp_path`; there is no fixture data on disk.
  The sample image is drawn with a real TrueType font at 48px because the PIL bitmap default
  is too small for Tesseract to recognize.
- Tests importing `ocr.app` need Streamlit, so they guard with
  `pytest.importorskip("streamlit")`. Tests importing `ocr.engine` must not need it — if
  that import starts pulling Streamlit in, the engine has regressed, not the test.
- **Go tests build a `Handler` directly** (`newTestHandler` in `handler_test.go`) rather than
  going through `handler.New`, which would need the HTML templates on disk. Route-level tests
  wire a real `chi` router so `chi.URLParam` resolves.
- `go test -race` is not optional here: the client pool is the thing most worth testing and
  the race detector is what tests it.
- A new invariant that spans both services belongs in each suite separately. There is no
  shared harness, and adding one is a larger decision than a test.
