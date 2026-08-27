package handler

import (
	"encoding/json"
	"errors"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"path/filepath"
	"strings"
	"time"

	"github.com/username/ocr-go/internal/model"
	"github.com/username/ocr-go/internal/ocr"
)

// ErrUnsafeFilename is returned when a requested result name could escape the
// output directory.
var ErrUnsafeFilename = errors.New("handler: unsafe filename")

// Config holds the handler tunables.
type Config struct {
	// OutputDir is where generated artifacts are written and served from.
	OutputDir string
	// TemplateGlob matches the HTML templates to parse at startup.
	TemplateGlob string
	// MaxUploadBytes caps a single file upload.
	MaxUploadBytes int64
	// MaxBatchBytes caps a whole batch upload.
	MaxBatchBytes int64
	// OCRTimeout bounds the time spent on one document.
	OCRTimeout time.Duration
	// BatchConcurrency caps how many batch files are processed in parallel.
	BatchConcurrency int
}

// DefaultConfig returns the configuration used when none is supplied.
func DefaultConfig() Config {
	return Config{
		OutputDir:        "outputs",
		TemplateGlob:     filepath.Join("web", "templates", "*.html"),
		MaxUploadBytes:   10 << 20,
		MaxBatchBytes:    50 << 20,
		OCRTimeout:       30 * time.Second,
		BatchConcurrency: 4,
	}
}

// Handler contains the dependencies shared by every HTTP handler.
type Handler struct {
	engine    ocr.Engine
	templates *template.Template
	cfg       Config
}

// New creates a handler for the given OCR engine.
//
// Parsing the templates can fail, so the error is returned instead of being
// raised as a panic at startup.
func New(engine ocr.Engine, cfg Config) (*Handler, error) {
	templates, err := template.ParseGlob(cfg.TemplateGlob)
	if err != nil {
		return nil, fmt.Errorf("failed to parse templates %q: %w", cfg.TemplateGlob, err)
	}

	return &Handler{
		engine:    engine,
		templates: templates,
		cfg:       cfg,
	}, nil
}

// Index renders the main page.
func (h *Handler) Index(w http.ResponseWriter, r *http.Request) {
	if err := h.templates.ExecuteTemplate(w, "index.html", nil); err != nil {
		log.Printf("failed to render index: %v", err)
		http.Error(w, "Failed to render page", http.StatusInternalServerError)
	}
}

// Health reports whether the service is up.
func (h *Handler) Health(w http.ResponseWriter, r *http.Request) {
	h.respondJSON(w, http.StatusOK, model.HealthResponse{Status: "healthy"})
}

// resolveOutputPath maps a requested result name to a path inside OutputDir.
//
// Names are attacker controlled, so anything with a directory component or a
// traversal segment is rejected outright rather than cleaned up silently.
func (h *Handler) resolveOutputPath(name string) (string, error) {
	if name == "" || name != filepath.Base(name) || strings.Contains(name, "..") {
		return "", ErrUnsafeFilename
	}

	path := filepath.Join(h.cfg.OutputDir, name)
	if filepath.Dir(path) != filepath.Clean(h.cfg.OutputDir) {
		return "", ErrUnsafeFilename
	}

	return path, nil
}

// respondJSON writes data as a JSON response.
func (h *Handler) respondJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	if err := json.NewEncoder(w).Encode(data); err != nil {
		// The status line is already on the wire, so logging is all that is
		// left to do here.
		log.Printf("failed to encode response: %v", err)
	}
}

// respondError writes an error payload with the given status.
func (h *Handler) respondError(w http.ResponseWriter, status int, message string) {
	h.respondJSON(w, status, model.ErrorResponse{Error: message})
}
