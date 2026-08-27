# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Two **independent** implementations of the same OCR product, sharing no code:

- `src/ocr/` — Python + Streamlit UI, the primary implementation (port 8501).
- `ocr-go/` — Go + chi HTTP API with a server-rendered frontend (port 8080).

Both wrap Tesseract and expose the same three operations: extract text, draw
bounding boxes, batch process. Changing behaviour in one does **not** propagate
to the other; decide explicitly whether a change belongs in one or both.

## Commands

### Python (repository root)

```bash
make install        # runtime + dev dependencies locally
make hooks          # install the git hooks (once per clone)
make dev            # docker compose with hot reload, attached
make start          # docker compose in the background
make test           # pytest with coverage (local)
make test-docker    # full suite inside the dev image, Tesseract included
make lint           # ruff check + black --check
make format         # black + ruff --fix
make check          # lint + typecheck + test
```

Run one test:

```bash
pytest tests/test_engine.py::TestOCREngineFormatters::test_markdown_contains_stats
```

The suite needs `src` on the path; `pyproject.toml` sets `pythonpath = ["src"]`
so plain `pytest` works from the root.

### Go (`ocr-go/`)

```bash
make build          # binary into bin/
make run            # go run ./cmd/server
make test           # go test -race -cover ./...
make vet
make docker-run
```

Run one test:

```bash
go test ./internal/handler -run TestPreviewTruncatesLongText
```

`go.sum` is not committed. Run `go mod tidy` before the first build; the
Dockerfile copies it with an optional glob (`go.su[m]`) so image builds work
without it.

## Architecture

### Python: three layers, one invariant

```
config.py  ->  engine.py  ->  app.py / cli.py
```

- **`config.py`** reads every tunable from the environment once at import time
  into a frozen `Settings` dataclass, exported as the module-level `settings`.
  Nothing else reads `os.environ`.
- **`engine.py`** is the OCR core. **It must never import `streamlit`** — this is
  the invariant that makes it usable from the CLI, tests and any future caller.
  A previous version broke it with a `@st.cache_data` decorator.
- **`app.py`** is UI only: staging uploads, rendering, persisting artifacts.

Key engine entry points: `extract_document()` dispatches image vs PDF;
`visualize_document()` does the same for annotation. Prefer these over the
lower-level `extract_text_and_boxes` / `visualize_boxes` in new UI code.

Temporary file ownership lives in context managers — `OCREngine.rasterized_pdf()`
for PDF pages, `app.staged_upload()` for uploads — so cleanup survives a failure
mid-processing. Do not hand-roll `try/finally` cleanup instead.

Upload names are attacker-controlled. Everything written under `OUTPUT_DIR`
goes through `safe_stem()` first.

### Go: pooled engine behind a handler

```
cmd/server/main.go  ->  internal/handler  ->  internal/ocr
                                          ->  internal/model  (transport structs)
```

**`gosseract.Client` is not safe for concurrent use.** `TesseractEngine` keeps a
pool of clients (`internal/ocr/tesseract.go`) and hands out exactly one per
in-flight request via `acquire`/`release`. Never share a single client across
goroutines — the batch endpoint runs several at once.

`handler.Config` carries all tunables and is built in `main.go` from the
environment; handlers read `h.cfg`, never `os.Getenv`. `handler.New` returns an
error rather than panicking on template parse failure.

Upload handling is centralized in `internal/handler/upload.go`:
`parseUpload` applies `http.MaxBytesReader` (`ParseMultipartForm` alone bounds
only in-memory buffering, not body size), and `decodeImageUpload` writes its own
error response and returns an `ok` flag.

Any path derived from a request goes through `Handler.resolveOutputPath`, which
rejects rather than sanitizes.

### Configuration

Both services are configured entirely through environment variables; see
`.env.example` and the table in `README.md`. The Python side reads `OCR_LANG`,
`OCR_PDF_ZOOM`, `OCR_MIN_CONFIDENCE`, `MAX_UPLOAD_SIZE_MB`, `OUTPUT_DIR`,
`LOG_LEVEL`. The Go side reads `TESSERACT_LANG`, `OCR_POOL_SIZE`,
`OCR_TIMEOUT_SECONDS`, `MAX_UPLOAD_SIZE_MB`, `MAX_BATCH_SIZE_MB`,
`ALLOWED_ORIGINS`, `PORT`.

## Testing notes

Tests that shell out to the Tesseract binary carry `@requires_tesseract`
(defined in `tests/conftest.py`) and skip themselves when it is absent, so
`pytest` stays useful on a machine without OCR installed. Keep pure logic —
parsing, sanitizing, formatting — in tests that do **not** need the binary;
`tests/test_detections.py` shows the pattern of feeding a Tesseract-shaped dict
directly to `OCREngine._iter_detections`.

## Committing

`git config core.hooksPath .githooks` is per-clone and not carried by git, so **`make hooks`
has to be run once after cloning** — until it is, nothing enforces any of the below.
`.claude/scripts/commit.sh survey` reports when they are missing.

- `.githooks/pre-commit` holds the fast invariants only: a daily budget of 60 commits
  (warning from 50), a refusal to commit `.env`, `outputs/` or `__pycache__`, and a 5 MB
  size ceiling. It deliberately runs no lint or tests — they would fire against a
  half-trimmed tree while a file is being split across two commits.
- `.githooks/commit-msg` checks the message *shape* against Conventional Commits and
  rejects a `Co-Authored-By` trailer. It cannot check whether the message is true; that is
  what the read-back step in the `commit-procedure` skill is for.
- `CHANGELOG.md` is curated, not generated. A user-visible or architectural change gets one
  line under `[Unreleased]`, staged **in the same commit** as the change it describes;
  internal churn gets nothing. Cutting a release is a separate, user-authorized step.

The full procedure lives in the `commit-procedure` skill and runs through the `committer`
agent, which the user invokes with `/commit`. Do not commit outside it.

## Conventions

From `.github/copilot-instructions.md`, applying repository-wide:

- **No emojis, emoticons or decorative symbols** anywhere — code, comments,
  commits, documentation.
- Code and commits in **English**; user-facing UI text in **Spanish**.
- Pure CSS only, no frameworks.
- **Conventional Commits** (`type(scope): description`). The full workflow,
  including committing in separate functional groups, is in
  `.github/instructions/commit.instructions.md`.

Go specifics worth preserving: `context.Context` as first parameter, errors
returned rather than panics, exported identifiers documented with full sentences
starting with the name, `defer Close()` on every resource.

## Gotchas

- `total_lines` in both APIs counts **words**, not lines — Tesseract reports at
  word level. The name is kept for compatibility with the README and frontend.
- `.github/instructions/ocr.instructions.md` and `ocr-go.md` are the original
  scaffolding specs, not living rules. They have drifted from the code (they
  describe PaddleOCR, a root-level `app.py`, `lang="es"`). Trust the code; use
  those files only for their "Code Style Requirements" sections.
