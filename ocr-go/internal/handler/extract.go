package handler

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/username/ocr-go/internal/model"
)

// ExtractText handles text extraction from an uploaded image.
func (h *Handler) ExtractText(w http.ResponseWriter, r *http.Request) {
	img, header, ok := h.decodeImageUpload(w, r, "file")
	if !ok {
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), h.cfg.OCRTimeout)
	defer cancel()

	result, err := h.engine.ExtractTextWithBoxes(ctx, img)
	if err != nil {
		h.respondError(w, http.StatusInternalServerError,
			fmt.Sprintf("OCR failed: %v", err))
		return
	}

	response := model.ExtractTextResponse{
		Filename:    header.Filename,
		FullText:    result.FullText,
		Boxes:       result.Boxes,
		TotalLines:  result.TotalLines,
		ProcessedAt: time.Now().UTC(),
	}

	// A failure to persist the result must not fail the request: the caller
	// already has the payload in the response body.
	if name, err := h.saveJSONResult(response); err != nil {
		log.Printf("failed to persist result for %q: %v", header.Filename, err)
	} else {
		response.OutputFile = name
	}

	h.respondJSON(w, http.StatusOK, response)
}
