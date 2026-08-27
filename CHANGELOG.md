# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This file is curated, not generated: it records user-visible and architectural
changes and deliberately omits internal churn. `git log` is the complete record.

## [Unreleased]

## [1.1.0] - 2026-08-27

### Added

- Environment-driven configuration in `src/ocr/config.py`: OCR language, PDF
  rasterization zoom, minimum detection confidence, upload size limit, output
  directory and log level. Documented in `.env.example` and the README.
- PDF support in the bounding box view, which previously accepted PDFs in the UI
  and then failed on them. `visualize_document()` annotates page by page.
- Working `ocr-app` console entry point (`src/ocr/cli.py`).
- Upload size limits, configurable on both services.
- Pool of Tesseract clients in the Go service, with `OCR_POOL_SIZE`.
- Configurable CORS allow list in the Go service, via `ALLOWED_ORIGINS`.
- GitHub Actions workflow covering lint, type checks, tests and image builds for
  both services.
- Test suites for the configuration, the Tesseract detection parser and the
  upload name sanitizer, plus the first tests for the Go service.
- MIT `LICENSE` file, which `pyproject.toml` already referenced.
- Development image stage, so `make test-docker` runs the suite with the
  Tesseract binary present.

### Changed

- The Python OCR engine no longer depends on Streamlit and can be used from the
  CLI, the tests or any other caller.
- `/api/extract` now returns each detection's geometry under `box` rather than
  `bbox`, reusing the typed struct instead of building maps by hand. The bundled
  frontend does not read that field; external clients do.
- Detection confidence is parsed as a float, preserving fractional values.
- The runtime container runs as an unprivileged user and no longer ships a
  compiler toolchain.
- Temporary files are owned by context managers, so cleanup survives a failure
  mid-processing.

### Fixed

- Data race in the Go batch endpoint: a single `gosseract.Client`, which is not
  safe for concurrent use, was shared across four goroutines, so simultaneous
  requests could read each other's results.
- Path traversal in uploaded file names, which reached the filesystem unchanged.
- `ParseMultipartForm` bounded only in-memory buffering, leaving uploads
  effectively unlimited in size.
- File descriptor leak when rasterizing PDF pages, and temporary files left
  behind when extraction failed partway through.
- Batch previews cut extracted text by bytes, producing invalid UTF-8 for
  accented characters.
- The Go Docker build copied a `go.sum` that is not committed, so it never built.
- `make test` invoked pytest inside an image that did not install it.
- `pyproject.toml` declared an entry point to a function that did not exist and a
  license file that was missing; ruff settings sat in a deprecated table.

### Removed

- The `uploads/` directory and its volume mount. Uploads are staged in a private
  temporary directory instead.

### Security

- Uploaded names are sanitized before anything is written under the output
  directory.
- Result downloads in the Go service reject any name carrying a directory
  component rather than cleaning it up.
- Upload size limits are enforced on the request body on both services.

## [1.0.0] - 2026-08-26

### Added

- Initial release: Streamlit OCR application over Tesseract with text
  extraction, bounding box visualization and batch processing, plus an
  independent Go implementation of the same operations.

[Unreleased]: https://github.com/username/python-ocr/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/username/python-ocr/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/username/python-ocr/releases/tag/v1.0.0
