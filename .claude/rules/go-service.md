---
paths:
  - "ocr-go/**"
---

# Go service

Layout is `cmd/server -> internal/handler -> internal/ocr`, with `internal/model` holding
the transport structs. The constraints below are not visible from any single file.

- **`gosseract.Client` is not safe for concurrent use.** It wraps a C API handle: two
  goroutines sharing one client interleave `SetImage` and `Text` and read each other's
  results. `TesseractEngine` keeps a pool and hands out exactly one client per in-flight
  request via `acquire`/`release`. The batch endpoint runs several at once, so this is the
  live case, not a hypothetical. `go test -race ./...` is the only thing that catches a
  regression.
- **`ParseMultipartForm` does not limit upload size** — it bounds only what is buffered in
  memory before spilling to disk. `parseUpload` wraps the body in `http.MaxBytesReader`,
  which is what actually caps it. Every upload path goes through `parseUpload`.
- **Any path derived from a request goes through `Handler.resolveOutputPath`**, which
  rejects a name with a directory component rather than sanitizing it. Do not
  `filepath.Join` a request value directly.
- Tunables come from `h.cfg` (`handler.Config`), populated in `main.go` from the
  environment. Handlers never call `os.Getenv`.
- **The JSON tags in `internal/model` are the public API shape**, and
  `web/static/js/app.js` reads `total_lines`, `full_text`, `total_boxes` and `download_url`
  by name. Nothing tests that pair, so renaming a tag breaks the page silently.
- Truncating extracted text cuts by **runes**, not bytes — Spanish output is multi-byte and
  a byte slice yields invalid UTF-8 in the response.
- `go.sum` is not committed. Run `go mod tidy` before the first build; the Dockerfile copies
  it with an optional glob (`go.su[m]`) so image builds work without it.
- `main.go` returns errors from `run()` rather than calling `log.Fatal` inline, so the
  deferred `engine.Close()` actually runs. Keep new startup failures on that path.
- Doc comments are full sentences starting with the name being documented; `context.Context`
  is the first parameter; errors are returned, not panicked.
