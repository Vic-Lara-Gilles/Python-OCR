---
paths:
  - "src/ocr/**"
  - "pyproject.toml"
  - "requirements*.txt"
---

# Python service

The layering is `config.py -> engine.py -> app.py / cli.py`, and the couplings below are
not visible from any single file.

- **`engine.py` must never import `streamlit`.** That is what lets the CLI, the tests and
  any future caller use it. It was broken once by an `@st.cache_data` decorator on a
  function that did nothing, which also made the tests need a Streamlit runtime. Nothing
  enforces this — no lint rule, no gate — so it holds only as long as it is read.
- **`config.py` is the only module that reads `os.environ`.** Everything else takes
  `settings`. The `Settings` dataclass is frozen and built once at import, so a variable
  changed after import does not take effect; that is deliberate.
- Adding a field to `Settings` means updating `.env.example` and the environment table in
  `README.md` in the same change. Three copies, no check between them.
- **Prefer the dispatchers** `extract_document()` and `visualize_document()` over
  `extract_text_and_boxes` / `visualize_boxes` in new UI code: they pick image vs PDF
  themselves, which is the bug the UI had before they existed.
- Detection filtering lives once, in `_iter_detections`, and feeds both extraction and
  annotation. Parsing Tesseract's `conf` as `float` (never `int`) is load-bearing: the
  value can arrive as a decimal string.
- **Temporary files are owned by context managers** — `OCREngine.rasterized_pdf()` for PDF
  pages, `app.staged_upload()` for uploads. Do not hand-roll `try/finally` cleanup instead;
  the hand-rolled version leaked a descriptor per page and left files behind on failure.
- Everything written under `OUTPUT_DIR` passes through `safe_stem()` first. Upload names
  are attacker-controlled and reached the filesystem directly once.
- Errors the user should see are `OCRError`, which subclasses `ValueError` so existing
  `except ValueError` handlers keep working.
- UI strings are **Spanish**; code, comments and docstrings are **English**.
- The same behaviour exists independently in `ocr-go/`. Before changing a rule here, decide
  whether the Go side needs it too — the `parity-auditor` agent exists for that question.
