package handler

import (
	"encoding/json"
	"html/template"
	"net/http"

	"github.com/username/ocr-go/internal/ocr"
)

// Handler contains dependencies for HTTP handlers
type Handler struct {
	engine    ocr.Engine
	templates *template.Template
}

// New creates a new handler with the OCR engine
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
	w.Header().Set("Content-Type", "application/json")
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
