package handler

import (
	"encoding/json"
	"errors"
	"fmt"
	"image"
	_ "image/gif"
	_ "image/jpeg"
	_ "image/png"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"

	"github.com/gofrs/uuid"
)

// parseUpload reads a multipart form, enforcing a hard limit on the request
// body.
//
// ParseMultipartForm only bounds how much is buffered in memory before
// spilling to disk, so MaxBytesReader is what actually caps the upload size.
func parseUpload(w http.ResponseWriter, r *http.Request, maxBytes int64) error {
	r.Body = http.MaxBytesReader(w, r.Body, maxBytes)

	if err := r.ParseMultipartForm(memoryBudget(maxBytes)); err != nil {
		return fmt.Errorf("failed to parse form: %w", err)
	}

	return nil
}

// memoryBudget caps in-memory buffering at 10MB regardless of the size limit.
func memoryBudget(maxBytes int64) int64 {
	const maxMemory = 10 << 20
	if maxBytes < maxMemory {
		return maxBytes
	}
	return maxMemory
}

// respondUploadError maps a parse failure to the right status code.
//
// An oversized body and a malformed one are different client mistakes, so
// they must not both report 413.
func (h *Handler) respondUploadError(w http.ResponseWriter, err error, maxBytes int64) {
	var tooLarge *http.MaxBytesError
	if errors.As(err, &tooLarge) {
		h.respondError(w, http.StatusRequestEntityTooLarge,
			fmt.Sprintf("Upload exceeds the %d MB limit", maxBytes>>20))
		return
	}

	h.respondError(w, http.StatusBadRequest, "Failed to parse form")
}

// decodeImageUpload extracts and decodes the single image found in field.
//
// It writes the error response itself and reports whether decoding succeeded,
// so callers can return early without repeating the same four checks.
func (h *Handler) decodeImageUpload(
	w http.ResponseWriter,
	r *http.Request,
	field string,
) (image.Image, *multipart.FileHeader, bool) {
	if err := parseUpload(w, r, h.cfg.MaxUploadBytes); err != nil {
		h.respondUploadError(w, err, h.cfg.MaxUploadBytes)
		return nil, nil, false
	}

	file, header, err := r.FormFile(field)
	if err != nil {
		h.respondError(w, http.StatusBadRequest, "No file uploaded")
		return nil, nil, false
	}
	defer file.Close()

	img, _, err := image.Decode(file)
	if err != nil {
		h.respondError(w, http.StatusBadRequest, "Invalid image file")
		return nil, nil, false
	}

	return img, header, true
}

// decodeImage decodes an uploaded file from a batch, without touching the
// response.
func decodeImage(header *multipart.FileHeader) (image.Image, error) {
	file, err := header.Open()
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	img, _, err := image.Decode(file)
	if err != nil {
		return nil, fmt.Errorf("invalid image: %w", err)
	}

	return img, nil
}

// saveJSONResult writes payload under a fresh name in the output directory.
//
// Returns the base name of the created file.
func (h *Handler) saveJSONResult(payload interface{}) (string, error) {
	if err := os.MkdirAll(h.cfg.OutputDir, 0o755); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	id, err := uuid.NewV4()
	if err != nil {
		return "", fmt.Errorf("failed to generate result id: %w", err)
	}

	name := fmt.Sprintf("ocr_%s.json", id)
	file, err := os.Create(filepath.Join(h.cfg.OutputDir, name))
	if err != nil {
		return "", fmt.Errorf("failed to create result file: %w", err)
	}
	defer file.Close()

	if err := json.NewEncoder(file).Encode(payload); err != nil {
		return "", fmt.Errorf("failed to write result file: %w", err)
	}

	return name, nil
}
