package handler

import (
	"errors"
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/username/ocr-go/internal/model"
)

// GetResult serves a single stored result file.
func (h *Handler) GetResult(w http.ResponseWriter, r *http.Request) {
	path, err := h.resolveOutputPath(chi.URLParam(r, "filename"))
	if err != nil {
		h.respondError(w, http.StatusBadRequest, "Invalid filename")
		return
	}

	info, err := os.Stat(path)
	if err != nil || info.IsDir() {
		h.respondError(w, http.StatusNotFound, "File not found")
		return
	}

	if contentType := mime.TypeByExtension(filepath.Ext(path)); contentType != "" {
		w.Header().Set("Content-Type", contentType)
	} else {
		w.Header().Set("Content-Type", "application/octet-stream")
	}

	// ServeContent handles range requests, caching headers and errors that
	// surface after the first byte has been written.
	file, err := os.Open(path)
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to open file")
		return
	}
	defer file.Close()

	http.ServeContent(w, r, info.Name(), info.ModTime(), file)
}

// ListResults lists every stored result file.
func (h *Handler) ListResults(w http.ResponseWriter, r *http.Request) {
	entries, err := os.ReadDir(h.cfg.OutputDir)
	if errors.Is(err, os.ErrNotExist) {
		h.respondJSON(w, http.StatusOK, model.ListResultsResponse{
			Files: []model.ResultFile{},
		})
		return
	}
	if err != nil {
		log.Printf("failed to read output directory: %v", err)
		h.respondError(w, http.StatusInternalServerError,
			"Failed to read outputs directory")
		return
	}

	files := make([]model.ResultFile, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}

		info, err := entry.Info()
		if err != nil {
			continue
		}

		files = append(files, model.ResultFile{
			Name:     entry.Name(),
			Size:     info.Size(),
			Modified: info.ModTime().UTC().Format(time.RFC3339),
		})
	}

	h.respondJSON(w, http.StatusOK, model.ListResultsResponse{
		Files: files,
		Count: len(files),
	})
}
