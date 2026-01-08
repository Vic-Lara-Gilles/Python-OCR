package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"image"
	_ "image/gif"
	_ "image/jpeg"
	_ "image/png"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gofrs/uuid"
	"github.com/username/ocr-go/internal/model"
)

// ExtractText handles text extraction from uploaded image
func (h *Handler) ExtractText(w http.ResponseWriter, r *http.Request) {
	// Parse multipart form (10MB max)
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

	// Build response
	response := model.ExtractTextResponse{
		Filename:    header.Filename,
		FullText:    result.FullText,
		Boxes:       boxes,
		TotalLines:  result.TotalLines,
		ProcessedAt: time.Now(),
	}

	// Save result to file
	resultID := uuid.Must(uuid.NewV4()).String()
	outputPath := filepath.Join("outputs", fmt.Sprintf("ocr_%s.json", resultID))

	outputFile, err := os.Create(outputPath)
	if err == nil {
		defer outputFile.Close()
		json.NewEncoder(outputFile).Encode(response)
	}

	// Send response
	h.respondJSON(w, http.StatusOK, response)
}
