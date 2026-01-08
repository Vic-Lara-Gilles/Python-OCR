---
applyTo: '**'
---

# OCR System with Docker + Go + Tesseract

## Project Overview

High-performance OCR system for document recognition with concurrent processing capabilities.

**Tech Stack:**
- Docker (containerized deployment)
- Go 1.21+ (high-performance runtime)
- Chi Router (lightweight HTTP router)
- Tesseract-OCR (OCR engine via gosseract)
- Go Templates (server-side rendering)

**Key Requirement:** Everything must be containerized - no local installation required.

## Project Structure

```
ocr-go/
├── cmd/
│   └── server/
│       └── main.go           # Application entry point
├── internal/
│   ├── handler/
│   │   ├── handler.go        # HTTP handlers
│   │   ├── extract.go        # Text extraction handler
│   │   ├── visualize.go      # Box visualization handler
│   │   └── batch.go          # Batch processing handler
│   ├── ocr/
│   │   ├── engine.go         # OCR engine interface
│   │   ├── tesseract.go      # Tesseract implementation
│   │   └── processor.go      # Document processor
│   ├── model/
│   │   └── result.go         # Data models
│   └── middleware/
│       └── logger.go         # HTTP middleware
├── web/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       └── results.html
├── outputs/                  # Auto-created for results
├── uploads/                  # Temporary uploads
├── Dockerfile
├── docker-compose.yml
├── go.mod
├── go.sum
├── .dockerignore
├── Makefile
└── README.md
```

## File Specifications

### Dockerfile

```dockerfile
# Multi-stage build for optimal image size
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev tesseract-ocr-dev leptonica-dev

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary with optimizations
RUN CGO_ENABLED=1 GOOS=linux go build -ldflags="-s -w" -o ocr-server ./cmd/server

# Runtime stage
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-data-spa \
    leptonica \
    ca-certificates

WORKDIR /app

# Copy binary and web assets
COPY --from=builder /build/ocr-server .
COPY --from=builder /build/web ./web

# Create directories
RUN mkdir -p outputs uploads

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run as non-root user
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["./ocr-server"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  ocr-go:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ocr-go-server
    ports:
      - "8080:8080"
    volumes:
      - ./outputs:/app/outputs
      - ./uploads:/app/uploads
    environment:
      - APP_ENV=production
      - PORT=8080
      - LOG_LEVEL=info
      - MAX_UPLOAD_SIZE=10485760  # 10MB
      - TESSERACT_LANG=spa
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:8080/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### go.mod

```go
module github.com/username/ocr-go

go 1.21

require (
    github.com/go-chi/chi/v5 v5.0.11
    github.com/go-chi/cors v1.2.1
    github.com/otiai10/gosseract/v2 v2.4.1
    github.com/gofrs/uuid v4.4.0+incompatible
    github.com/disintegration/imaging v1.6.2
    github.com/pdfcpu/pdfcpu v0.6.0
)
```

### cmd/server/main.go

```go
package main

import (
    "context"
    "fmt"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/username/ocr-go/internal/handler"
    "github.com/username/ocr-go/internal/middleware"
    "github.com/username/ocr-go/internal/ocr"
    "github.com/go-chi/chi/v5"
    chimiddleware "github.com/go-chi/chi/v5/middleware"
    "github.com/go-chi/cors"
)

func main() {
    // Initialize OCR engine
    engine, err := ocr.NewTesseractEngine("spa")
    if err != nil {
        log.Fatalf("Failed to initialize OCR engine: %v", err)
    }
    defer engine.Close()

    // Initialize handler
    h := handler.New(engine)

    // Setup router
    r := chi.NewRouter()

    // Middleware
    r.Use(chimiddleware.RequestID)
    r.Use(chimiddleware.RealIP)
    r.Use(middleware.Logger)
    r.Use(chimiddleware.Recoverer)
    r.Use(chimiddleware.Timeout(60 * time.Second))

    // CORS
    r.Use(cors.Handler(cors.Options{
        AllowedOrigins:   []string{"*"},
        AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
        AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
        AllowCredentials: false,
        MaxAge:           300,
    }))

    // Static files
    r.Handle("/static/*", http.StripPrefix("/static/",
        http.FileServer(http.Dir("web/static"))))

    // Routes
    r.Get("/", h.Index)
    r.Get("/health", h.Health)
    r.Post("/api/extract", h.ExtractText)
    r.Post("/api/visualize", h.VisualizeBoxes)
    r.Post("/api/batch", h.BatchProcess)
    r.Get("/api/results", h.ListResults)
    r.Get("/api/results/{filename}", h.GetResult)

    // Server configuration
    port := getEnv("PORT", "8080")
    srv := &http.Server{
        Addr:         fmt.Sprintf(":%s", port),
        Handler:      r,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Graceful shutdown
    go func() {
        log.Printf("Server starting on port %s", port)
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server failed to start: %v", err)
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    log.Println("Server shutting down...")

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("Server forced to shutdown: %v", err)
    }

    log.Println("Server exited")
}

func getEnv(key, defaultValue string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultValue
}
```

### internal/ocr/engine.go

```go
package ocr

import (
    "context"
    "image"
)

// Engine defines the OCR engine interface
type Engine interface {
    // ExtractText extracts text from an image
    ExtractText(ctx context.Context, img image.Image) (*Result, error)

    // ExtractTextWithBoxes extracts text with bounding box information
    ExtractTextWithBoxes(ctx context.Context, img image.Image) (*DetailedResult, error)

    // Close releases engine resources
    Close() error
}

// Result represents basic OCR result
type Result struct {
    Text       string  `json:"text"`
    Confidence float64 `json:"confidence"`
}

// BoundingBox represents text location
type BoundingBox struct {
    X      int     `json:"x"`
    Y      int     `json:"y"`
    Width  int     `json:"width"`
    Height int     `json:"height"`
}

// TextBox represents detected text with its location
type TextBox struct {
    Text       string      `json:"text"`
    Confidence float64     `json:"confidence"`
    Box        BoundingBox `json:"box"`
}

// DetailedResult represents OCR result with boxes
type DetailedResult struct {
    FullText   string     `json:"full_text"`
    Boxes      []TextBox  `json:"boxes"`
    TotalLines int        `json:"total_lines"`
    Language   string     `json:"language"`
}
```

### internal/ocr/tesseract.go

```go
package ocr

import (
    "context"
    "fmt"
    "image"
    "strings"

    "github.com/otiai10/gosseract/v2"
)

// TesseractEngine implements Engine using Tesseract OCR
type TesseractEngine struct {
    client *gosseract.Client
    lang   string
}

// NewTesseractEngine creates a new Tesseract OCR engine
func NewTesseractEngine(lang string) (*TesseractEngine, error) {
    client := gosseract.NewClient()
    if err := client.SetLanguage(lang); err != nil {
        return nil, fmt.Errorf("failed to set language: %w", err)
    }

    return &TesseractEngine{
        client: client,
        lang:   lang,
    }, nil
}

// ExtractText extracts text from image
func (e *TesseractEngine) ExtractText(ctx context.Context, img image.Image) (*Result, error) {
    if err := e.client.SetImageFromImage(img); err != nil {
        return nil, fmt.Errorf("failed to set image: %w", err)
    }

    text, err := e.client.Text()
    if err != nil {
        return nil, fmt.Errorf("failed to extract text: %w", err)
    }

    confidence, err := e.client.GetMeanConfidence()
    if err != nil {
        confidence = 0
    }

    return &Result{
        Text:       strings.TrimSpace(text),
        Confidence: float64(confidence) / 100.0,
    }, nil
}

// ExtractTextWithBoxes extracts text with bounding boxes
func (e *TesseractEngine) ExtractTextWithBoxes(ctx context.Context, img image.Image) (*DetailedResult, error) {
    if err := e.client.SetImageFromImage(img); err != nil {
        return nil, fmt.Errorf("failed to set image: %w", err)
    }

    // Get bounding boxes
    boxes, err := e.client.GetBoundingBoxes(gosseract.RIL_WORD)
    if err != nil {
        return nil, fmt.Errorf("failed to get bounding boxes: %w", err)
    }

    var textBoxes []TextBox
    var fullTextParts []string

    for _, box := range boxes {
        if strings.TrimSpace(box.Word) == "" {
            continue
        }

        textBoxes = append(textBoxes, TextBox{
            Text:       box.Word,
            Confidence: float64(box.Confidence) / 100.0,
            Box: BoundingBox{
                X:      box.Box.Min.X,
                Y:      box.Box.Min.Y,
                Width:  box.Box.Max.X - box.Box.Min.X,
                Height: box.Box.Max.Y - box.Box.Min.Y,
            },
        })

        fullTextParts = append(fullTextParts, box.Word)
    }

    return &DetailedResult{
        FullText:   strings.Join(fullTextParts, " "),
        Boxes:      textBoxes,
        TotalLines: len(textBoxes),
        Language:   e.lang,
    }, nil
}

// Close releases resources
func (e *TesseractEngine) Close() error {
    return e.client.Close()
}
```

### internal/handler/handler.go

```go
package handler

import (
    "encoding/json"
    "html/template"
    "net/http"
    "path/filepath"

    "github.com/username/ocr-go/internal/ocr"
)

// Handler contains dependencies for HTTP handlers
type Handler struct {
    engine    ocr.Engine
    templates *template.Template
}

// New creates a new handler
func New(engine ocr.Engine) *Handler {
    tmpl := template.Must(template.ParseGlob("web/templates/*.html"))

    return &Handler{
        engine:    engine,
        templates: tmpl,
    }
}

// Index renders the main page
func (h *Handler) Index(w http.ResponseWriter, r *http.Request) {
    if err := h.templates.ExecuteTemplate(w, "index.html", nil); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
}

// Health check endpoint
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]string{
        "status": "healthy",
    })
}

// respondJSON sends JSON response
func (h *Handler) respondJSON(w http.ResponseWriter, status int, data interface{}) {
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(status)
    json.NewEncoder(w).Encode(data)
}

// respondError sends error response
func (h *Handler) respondError(w http.ResponseWriter, status int, message string) {
    h.respondJSON(w, status, map[string]string{
        "error": message,
    })
}
```

### internal/handler/extract.go

```go
package handler

import (
    "context"
    "encoding/json"
    "fmt"
    "image"
    _ "image/jpeg"
    _ "image/png"
    "net/http"
    "os"
    "path/filepath"
    "time"

    "github.com/gofrs/uuid"
)

// ExtractTextResponse represents the response
type ExtractTextResponse struct {
    Filename   string                 `json:"filename"`
    FullText   string                 `json:"full_text"`
    Boxes      []map[string]interface{} `json:"boxes"`
    TotalLines int                    `json:"total_lines"`
    ProcessedAt time.Time             `json:"processed_at"`
}

// ExtractText handles text extraction from uploaded image
func (h *Handler) ExtractText(w http.ResponseWriter, r *http.Request) {
    // Parse multipart form
    if err := r.ParseMultipartForm(10 << 20); err != nil { // 10MB max
        h.respondError(w, http.StatusBadRequest, "Failed to parse form")
        return
    }

    // Get uploaded file
    file, header, err := r.FormFile("file")
    if err != nil {
        h.respondError(w, http.StatusBadRequest, "No file uploaded")
        return
    }
    defer file.Close()

    // Decode image
    img, _, err := image.Decode(file)
    if err != nil {
        h.respondError(w, http.StatusBadRequest, "Invalid image file")
        return
    }

    // Extract text with boxes
    ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
    defer cancel()

    result, err := h.engine.ExtractTextWithBoxes(ctx, img)
    if err != nil {
        h.respondError(w, http.StatusInternalServerError,
            fmt.Sprintf("OCR failed: %v", err))
        return
    }

    // Convert boxes to map format
    boxes := make([]map[string]interface{}, len(result.Boxes))
    for i, box := range result.Boxes {
        boxes[i] = map[string]interface{}{
            "text":       box.Text,
            "confidence": box.Confidence,
            "bbox": map[string]int{
                "x":      box.Box.X,
                "y":      box.Box.Y,
                "width":  box.Box.Width,
                "height": box.Box.Height,
            },
        }
    }

    // Save result to file
    resultID := uuid.Must(uuid.NewV4()).String()
    outputPath := filepath.Join("outputs", fmt.Sprintf("ocr_%s.json", resultID))

    response := ExtractTextResponse{
        Filename:    header.Filename,
        FullText:    result.FullText,
        Boxes:       boxes,
        TotalLines:  result.TotalLines,
        ProcessedAt: time.Now(),
    }

    // Save to disk
    outputFile, err := os.Create(outputPath)
    if err == nil {
        defer outputFile.Close()
        json.NewEncoder(outputFile).Encode(response)
    }

    // Send response
    h.respondJSON(w, http.StatusOK, response)
}
```

### internal/handler/visualize.go

```go
package handler

import (
    "context"
    "fmt"
    "image"
    "image/color"
    "image/draw"
    "image/png"
    "net/http"
    "os"
    "path/filepath"
    "time"

    "github.com/gofrs/uuid"
    "golang.org/x/image/font"
    "golang.org/x/image/font/basicfont"
    "golang.org/x/image/math/fixed"
)

// VisualizeBoxes handles bounding box visualization
func (h *Handler) VisualizeBoxes(w http.ResponseWriter, r *http.Request) {
    // Parse multipart form
    if err := r.ParseMultipartForm(10 << 20); err != nil {
        h.respondError(w, http.StatusBadRequest, "Failed to parse form")
        return
    }

    // Get uploaded file
    file, header, err := r.FormFile("file")
    if err != nil {
        h.respondError(w, http.StatusBadRequest, "No file uploaded")
        return
    }
    defer file.Close()

    // Decode image
    img, _, err := image.Decode(file)
    if err != nil {
        h.respondError(w, http.StatusBadRequest, "Invalid image file")
        return
    }

    // Extract text with boxes
    ctx, cancel := context.WithTimeout(r.Context(), 30*time.Second)
    defer cancel()

    result, err := h.engine.ExtractTextWithBoxes(ctx, img)
    if err != nil {
        h.respondError(w, http.StatusInternalServerError,
            fmt.Sprintf("OCR failed: %v", err))
        return
    }

    // Create drawable image
    bounds := img.Bounds()
    rgba := image.NewRGBA(bounds)
    draw.Draw(rgba, bounds, img, bounds.Min, draw.Src)

    // Draw bounding boxes
    green := color.RGBA{0, 255, 0, 255}
    red := color.RGBA{255, 0, 0, 255}

    for _, box := range result.Boxes {
        // Draw green rectangle
        drawRect(rgba, box.Box.X, box.Box.Y,
            box.Box.X+box.Box.Width, box.Box.Y+box.Box.Height, green, 2)

        // Draw red text label
        drawText(rgba, box.Box.X, max(box.Box.Y-15, 10),
            fmt.Sprintf("%s (%.2f)", box.Text, box.Confidence), red)
    }

    // Save annotated image
    resultID := uuid.Must(uuid.NewV4()).String()
    outputPath := filepath.Join("outputs", fmt.Sprintf("boxes_%s.png", resultID))

    outputFile, err := os.Create(outputPath)
    if err != nil {
        h.respondError(w, http.StatusInternalServerError, "Failed to save image")
        return
    }
    defer outputFile.Close()

    if err := png.Encode(outputFile, rgba); err != nil {
        h.respondError(w, http.StatusInternalServerError, "Failed to encode image")
        return
    }

    // Send response
    h.respondJSON(w, http.StatusOK, map[string]interface{}{
        "filename":    header.Filename,
        "output_file": filepath.Base(outputPath),
        "total_boxes": len(result.Boxes),
        "download_url": fmt.Sprintf("/api/results/%s", filepath.Base(outputPath)),
    })
}

// Helper functions
func drawRect(img *image.RGBA, x1, y1, x2, y2 int, c color.Color, thickness int) {
    for t := 0; t < thickness; t++ {
        for x := x1; x <= x2; x++ {
            img.Set(x, y1+t, c)
            img.Set(x, y2-t, c)
        }
        for y := y1; y <= y2; y++ {
            img.Set(x1+t, y, c)
            img.Set(x2-t, y, c)
        }
    }
}

func drawText(img *image.RGBA, x, y int, text string, c color.Color) {
    point := fixed.Point26_6{
        X: fixed.Int26_6(x * 64),
        Y: fixed.Int26_6(y * 64),
    }

    d := &font.Drawer{
        Dst:  img,
        Src:  image.NewUniform(c),
        Face: basicfont.Face7x13,
        Dot:  point,
    }
    d.DrawString(text)
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}
```

### internal/handler/batch.go

```go
package handler

import (
    "context"
    "encoding/json"
    "fmt"
    "image"
    "mime/multipart"
    "net/http"
    "os"
    "path/filepath"
    "sync"
    "time"

    "github.com/gofrs/uuid"
)

// BatchResult represents result for single file
type BatchResult struct {
    Filename   string `json:"filename"`
    Lines      int    `json:"lines"`
    Success    bool   `json:"success"`
    Error      string `json:"error,omitempty"`
    Preview    string `json:"preview"`
    OutputFile string `json:"output_file"`
}

// BatchProcessResponse represents batch processing response
type BatchProcessResponse struct {
    TotalFiles     int           `json:"total_files"`
    SuccessCount   int           `json:"success_count"`
    FailureCount   int           `json:"failure_count"`
    Results        []BatchResult `json:"results"`
    ProcessingTime string        `json:"processing_time"`
}

// BatchProcess handles batch processing of multiple files
func (h *Handler) BatchProcess(w http.ResponseWriter, r *http.Request) {
    startTime := time.Now()

    // Parse multipart form
    if err := r.ParseMultipartForm(50 << 20); err != nil { // 50MB max
        h.respondError(w, http.StatusBadRequest, "Failed to parse form")
        return
    }

    files := r.MultipartForm.File["files"]
    if len(files) == 0 {
        h.respondError(w, http.StatusBadRequest, "No files uploaded")
        return
    }

    // Process files concurrently
    results := make([]BatchResult, len(files))
    var wg sync.WaitGroup
    semaphore := make(chan struct{}, 4) // Limit to 4 concurrent processes

    for i, fileHeader := range files {
        wg.Add(1)
        go func(index int, header *multipart.FileHeader) {
            defer wg.Done()
            semaphore <- struct{}{}
            defer func() { <-semaphore }()

            results[index] = h.processFile(r.Context(), header)
        }(i, fileHeader)
    }

    wg.Wait()

    // Count successes and failures
    successCount := 0
    failureCount := 0
    for _, result := range results {
        if result.Success {
            successCount++
        } else {
            failureCount++
        }
    }

    response := BatchProcessResponse{
        TotalFiles:     len(files),
        SuccessCount:   successCount,
        FailureCount:   failureCount,
        Results:        results,
        ProcessingTime: time.Since(startTime).String(),
    }

    h.respondJSON(w, http.StatusOK, response)
}

func (h *Handler) processFile(ctx context.Context, header *multipart.FileHeader) BatchResult {
    result := BatchResult{
        Filename: header.Filename,
    }

    file, err := header.Open()
    if err != nil {
        result.Error = fmt.Sprintf("Failed to open file: %v", err)
        return result
    }
    defer file.Close()

    img, _, err := image.Decode(file)
    if err != nil {
        result.Error = fmt.Sprintf("Invalid image: %v", err)
        return result
    }

    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    ocrResult, err := h.engine.ExtractTextWithBoxes(ctx, img)
    if err != nil {
        result.Error = fmt.Sprintf("OCR failed: %v", err)
        return result
    }

    result.Lines = ocrResult.TotalLines
    result.Success = true

    if len(ocrResult.FullText) > 100 {
        result.Preview = ocrResult.FullText[:100] + "..."
    } else {
        result.Preview = ocrResult.FullText
    }

    resultID := uuid.Must(uuid.NewV4()).String()
    outputPath := filepath.Join("outputs", fmt.Sprintf("ocr_%s.json", resultID))

    outputFile, err := os.Create(outputPath)
    if err == nil {
        defer outputFile.Close()
        json.NewEncoder(outputFile).Encode(map[string]interface{}{
            "filename":   header.Filename,
            "full_text":  ocrResult.FullText,
            "boxes":      ocrResult.Boxes,
            "total_lines": ocrResult.TotalLines,
        })
        result.OutputFile = filepath.Base(outputPath)
    }

    return result
}
```

### internal/middleware/logger.go

```go
package middleware

import (
    "log"
    "net/http"
    "time"

    "github.com/go-chi/chi/v5/middleware"
)

// Logger is a middleware that logs HTTP requests
func Logger(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
        next.ServeHTTP(ww, r)

        log.Printf(
            "%s %s %d %s %s",
            r.Method,
            r.RequestURI,
            ww.Status(),
            time.Since(start),
            r.RemoteAddr,
        )
    })
}
```

### Makefile

```makefile
.PHONY: help build run test clean docker-build docker-run docker-stop

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the application
	go build -o bin/ocr-server ./cmd/server

run: ## Run the application locally
	go run ./cmd/server/main.go

test: ## Run tests
	go test -v -race -cover ./...

clean: ## Clean build artifacts
	rm -rf bin/ outputs/* uploads/*

docker-build: ## Build Docker image
	docker-compose build

docker-run: ## Run with Docker Compose
	docker-compose up

docker-stop: ## Stop Docker containers
	docker-compose down

fmt: ## Format code
	go fmt ./...

lint: ## Run linter
	golangci-lint run

mod: ## Download dependencies
	go mod download
	go mod tidy
```

### web/templates/base.html

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{block "title" .}}OCR System{{end}}</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <header>
        <h1>OCR System - Go + Tesseract</h1>
        <nav>
            <a href="/">Home</a>
            <a href="/results">Results</a>
        </nav>
    </header>

    <main>
        {{block "content" .}}{{end}}
    </main>

    <footer>
        <p>Powered by Go 1.21 + Tesseract OCR</p>
    </footer>

    <script src="/static/js/app.js"></script>
</body>
</html>
```

### web/templates/index.html

```html
{{template "base.html" .}}

{{define "title"}}OCR - Extract Text{{end}}

{{define "content"}}
<div class="container">
    <section class="upload-section">
        <h2>Extraer Texto</h2>
        <form id="extractForm" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit">Procesar</button>
        </form>
        <div id="result"></div>
    </section>

    <section class="visualize-section">
        <h2>Visualizar Cajas</h2>
        <form id="visualizeForm" enctype="multipart/form-data">
            <input type="file" name="file" accept="image/*" required>
            <button type="submit">Visualizar</button>
        </form>
        <div id="visualResult"></div>
    </section>

    <section class="batch-section">
        <h2>Procesamiento por Lotes</h2>
        <form id="batchForm" enctype="multipart/form-data">
            <input type="file" name="files" accept="image/*" multiple required>
            <button type="submit">Procesar Todo</button>
        </form>
        <div id="batchResult"></div>
    </section>
</div>
{{end}}
```

### web/static/js/app.js

```javascript
// Extract Text Form Handler
document.getElementById('extractForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        document.getElementById('result').innerHTML = `
            <h3>Resultado:</h3>
            <p><strong>Archivo:</strong> ${data.filename}</p>
            <p><strong>Líneas:</strong> ${data.total_lines}</p>
            <pre>${data.full_text}</pre>
        `;
    } catch (error) {
        document.getElementById('result').innerHTML = `
            <p class="error">Error: ${error.message}</p>
        `;
    }
});

// Visualize Boxes Form Handler
document.getElementById('visualizeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
        const response = await fetch('/api/visualize', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        document.getElementById('visualResult').innerHTML = `
            <h3>Imagen Procesada:</h3>
            <p><strong>Cajas Detectadas:</strong> ${data.total_boxes}</p>
            <a href="${data.download_url}" download>Descargar Imagen</a>
        `;
    } catch (error) {
        document.getElementById('visualResult').innerHTML = `
            <p class="error">Error: ${error.message}</p>
        `;
    }
});

// Batch Process Form Handler
document.getElementById('batchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);

    try {
        const response = await fetch('/api/batch', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        let resultsHTML = `
            <h3>Resultados del Lote:</h3>
            <p><strong>Total:</strong> ${data.total_files}</p>
            <p><strong>Exitosos:</strong> ${data.success_count}</p>
            <p><strong>Fallidos:</strong> ${data.failure_count}</p>
            <p><strong>Tiempo:</strong> ${data.processing_time}</p>
            <table>
                <thead>
                    <tr>
                        <th>Archivo</th>
                        <th>Líneas</th>
                        <th>Estado</th>
                        <th>Preview</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.results.forEach(result => {
            resultsHTML += `
                <tr class="${result.success ? 'success' : 'error'}">
                    <td>${result.filename}</td>
                    <td>${result.lines || '-'}</td>
                    <td>${result.success ? 'OK' : 'Error'}</td>
                    <td>${result.preview || result.error}</td>
                </tr>
            `;
        });

        resultsHTML += `
                </tbody>
            </table>
        `;

        document.getElementById('batchResult').innerHTML = resultsHTML;
    } catch (error) {
        document.getElementById('batchResult').innerHTML = `
            <p class="error">Error: ${error.message}</p>
        `;
    }
});
```

### web/static/css/style.css

```css
:root {
    --primary-color: #2563eb;
    --success-color: #16a34a;
    --error-color: #dc2626;
    --border-color: #e5e7eb;
    --bg-color: #f9fafb;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #1f2937;
    background-color: var(--bg-color);
}

header {
    background-color: var(--primary-color);
    color: white;
    padding: 1rem 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

header h1 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

nav a {
    color: white;
    text-decoration: none;
    margin-right: 1rem;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.2s;
}

nav a:hover {
    background-color: rgba(255,255,255,0.1);
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 1rem;
}

.container {
    display: grid;
    gap: 2rem;
}

section {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

h2 {
    color: var(--primary-color);
    margin-bottom: 1rem;
}

form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

input[type="file"] {
    padding: 0.5rem;
    border: 2px dashed var(--border-color);
    border-radius: 4px;
    cursor: pointer;
}

button {
    background-color: var(--primary-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.2s;
}

button:hover {
    background-color: #1d4ed8;
}

button:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
}

#result, #visualResult, #batchResult {
    margin-top: 1rem;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th, td {
    text-align: left;
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
}

th {
    background-color: var(--bg-color);
    font-weight: 600;
}

tr.success {
    background-color: rgba(22, 163, 74, 0.05);
}

tr.error {
    background-color: rgba(220, 38, 38, 0.05);
}

.error {
    color: var(--error-color);
    background-color: rgba(220, 38, 38, 0.1);
    padding: 1rem;
    border-radius: 4px;
    border-left: 4px solid var(--error-color);
}

pre {
    background-color: var(--bg-color);
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    border: 1px solid var(--border-color);
}

footer {
    text-align: center;
    padding: 2rem;
    color: #6b7280;
    margin-top: 4rem;
}
```

### .dockerignore

```
.git
.gitignore
.vscode
.idea
*.swp
*.swo
*.exe
*.test
*.out
bin/
vendor/
.DS_Store
Thumbs.db
outputs/
uploads/
temp_*
*.log
*.md
docs/
.github/
.gitlab-ci.yml
```

## Code Style Requirements

### Go Best Practices

1. **Project Layout:** Follow [Standard Go Project Layout](https://github.com/golang-standards/project-layout)
2. **Error Handling:** Always check and handle errors explicitly
3. **Naming Conventions:**
   - Package names: lowercase, single word
   - Exported identifiers: PascalCase
   - Unexported identifiers: camelCase
   - Interfaces: -er suffix (e.g., `Reader`, `Writer`)
4. **Comments:**
   - Document all exported functions, types, and packages
   - Use full sentences starting with the name being documented
5. **Formatting:** Use `go fmt` and `goimports`
6. **Concurrency:**
   - Use channels and goroutines appropriately
   - Implement proper synchronization with `sync` package
   - Avoid goroutine leaks
7. **Testing:**
   - Write table-driven tests
   - Use testify/assert for assertions
   - Achieve >80% code coverage

### Code Quality Rules

- **No panic:** Use error returns instead of panic (except truly exceptional cases)
- **Context propagation:** Pass `context.Context` as first parameter for cancellation
- **Interface segregation:** Define small, focused interfaces
- **Dependency injection:** Use constructor functions to inject dependencies
- **Configuration:** Use environment variables or config files (no hardcoded values)
- **Logging:** Use structured logging with standard library or zerolog
- **HTTP handlers:** Return early on errors to avoid nested if statements
- **Resource management:** Always defer Close() for resources

### Security Best Practices

1. **Input Validation:**
   - Validate file types and sizes
   - Sanitize file names
   - Limit upload sizes
2. **Error Handling:**
   - Don't leak internal errors to clients
   - Log detailed errors server-side only
3. **Timeouts:**
   - Set context timeouts for all operations
   - Configure HTTP client/server timeouts
4. **CORS:**
   - Configure appropriate CORS policies
   - Whitelist specific origins in production

## Performance Optimization

### Concurrency Patterns

```go
// Worker pool for batch processing
func processFilesConcurrently(files []FileHeader, maxWorkers int) []Result {
    jobs := make(chan FileHeader, len(files))
    results := make(chan Result, len(files))

    var wg sync.WaitGroup
    for w := 0; w < maxWorkers; w++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for file := range jobs {
                results <- processFile(file)
            }
        }()
    }

    for _, file := range files {
        jobs <- file
    }
    close(jobs)

    go func() {
        wg.Wait()
        close(results)
    }()

    var allResults []Result
    for result := range results {
        allResults = append(allResults, result)
    }

    return allResults
}
```

### Memory Management

- Use `sync.Pool` for frequently allocated objects
- Stream large files instead of loading into memory
- Implement proper cleanup with defer statements
- Monitor goroutine counts and prevent leaks

## Testing Strategy

### Unit Tests

```go
func TestTesseractEngine_ExtractText(t *testing.T) {
    tests := []struct {
        name      string
        image     string
        wantText  string
        wantError bool
    }{
        {
            name:      "valid image",
            image:     "testdata/sample.png",
            wantText:  "Expected Text",
            wantError: false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            engine, err := ocr.NewTesseractEngine("spa")
            require.NoError(t, err)
            defer engine.Close()

            img := loadImage(tt.image)
            result, err := engine.ExtractText(context.Background(), img)

            if tt.wantError {
                assert.Error(t, err)
                return
            }

            assert.NoError(t, err)
            assert.Contains(t, result.Text, tt.wantText)
        })
    }
}
```

### Integration Tests

```go
func TestAPI_ExtractText(t *testing.T) {
    engine, _ := ocr.NewTesseractEngine("spa")
    h := handler.New(engine)
    r := chi.NewRouter()
    r.Post("/api/extract", h.ExtractText)
    ts := httptest.NewServer(r)
    defer ts.Close()

    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)
    file, _ := writer.CreateFormFile("file", "test.png")
    file.Write(loadTestImageBytes())
    writer.Close()

    req, _ := http.NewRequest("POST", ts.URL+"/api/extract", body)
    req.Header.Set("Content-Type", writer.FormDataContentType())

    resp, err := http.DefaultClient.Do(req)
    require.NoError(t, err)
    defer resp.Body.Close()

    assert.Equal(t, http.StatusOK, resp.StatusCode)

    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    assert.NotEmpty(t, result["full_text"])
}
```

## Deployment

### Docker Production Build

```dockerfile
FROM golang:1.21-alpine AS builder

RUN apk add --no-cache gcc musl-dev tesseract-ocr-dev leptonica-dev upx

WORKDIR /build
COPY . .

RUN go mod download
RUN CGO_ENABLED=1 GOOS=linux go build \
    -ldflags="-s -w" \
    -tags=prod \
    -o ocr-server \
    ./cmd/server

RUN upx --best --lzma ocr-server

FROM alpine:3.19

RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-data-spa \
    leptonica \
    ca-certificates

WORKDIR /app
COPY --from=builder /build/ocr-server .
COPY --from=builder /build/web ./web

RUN mkdir -p outputs uploads && \
    adduser -D -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8080

CMD ["./ocr-server"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ocr-go
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ocr-go
  template:
    metadata:
      labels:
        app: ocr-go
    spec:
      containers:
      - name: ocr-go
        image: ocr-go:latest
        ports:
        - containerPort: 8080
        env:
        - name: PORT
          value: "8080"
        - name: TESSERACT_LANG
          value: "spa"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ocr-go-service
spec:
  selector:
    app: ocr-go
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
```

## Monitoring

### Prometheus Metrics

```go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    OcrRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "ocr_requests_total",
            Help: "Total number of OCR requests",
        },
        []string{"endpoint", "status"},
    )

    OcrDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "ocr_duration_seconds",
            Help:    "OCR processing duration",
            Buckets: prometheus.DefBuckets,
        },
        []string{"endpoint"},
    )
)
```

## Commit Message Format

Follow Conventional Commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation only
- `refactor:` Code restructuring
- `test:` Adding/updating tests
- `chore:` Maintenance tasks
- `perf:` Performance improvements

**Examples:**
- `feat(ocr): add concurrent batch processing`
- `fix(handler): resolve memory leak in file upload`
- `perf(tesseract): optimize image preprocessing`

## Resources

- [Go Documentation](https://go.dev/doc/)
- [Standard Go Project Layout](https://github.com/golang-standards/project-layout)
- [Effective Go](https://go.dev/doc/effective_go)
- [Gosseract](https://github.com/otiai10/gosseract)
- [Chi Router](https://github.com/go-chi/chi)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
