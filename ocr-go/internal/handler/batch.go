package handler

import (
	"context"
	"fmt"
	"log"
	"mime/multipart"
	"net/http"
	"sync"
	"time"

	"github.com/username/ocr-go/internal/model"
)

// previewRunes is how much of the extracted text is echoed back per file.
const previewRunes = 100

// BatchProcess handles OCR over several uploaded files.
func (h *Handler) BatchProcess(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()

	if err := parseUpload(w, r, h.cfg.MaxBatchBytes); err != nil {
		h.respondUploadError(w, err, h.cfg.MaxBatchBytes)
		return
	}

	files := r.MultipartForm.File["files"]
	if len(files) == 0 {
		h.respondError(w, http.StatusBadRequest, "No files uploaded")
		return
	}

	results := h.processFiles(r.Context(), files)

	successCount := 0
	for _, result := range results {
		if result.Success {
			successCount++
		}
	}

	h.respondJSON(w, http.StatusOK, model.BatchProcessResponse{
		TotalFiles:     len(files),
		SuccessCount:   successCount,
		FailureCount:   len(files) - successCount,
		Results:        results,
		ProcessingTime: time.Since(startTime).String(),
	})
}

// processFiles runs OCR over every file, bounded by BatchConcurrency.
//
// Each goroutine writes to its own slot, so no lock is needed around results.
func (h *Handler) processFiles(
	ctx context.Context,
	files []*multipart.FileHeader,
) []model.BatchResult {
	concurrency := h.cfg.BatchConcurrency
	if concurrency < 1 {
		concurrency = 1
	}

	results := make([]model.BatchResult, len(files))
	semaphore := make(chan struct{}, concurrency)
	var wg sync.WaitGroup

	for i, fileHeader := range files {
		wg.Add(1)

		go func(index int, header *multipart.FileHeader) {
			defer wg.Done()

			semaphore <- struct{}{}
			defer func() { <-semaphore }()

			results[index] = h.processFile(ctx, header)
		}(i, fileHeader)
	}

	wg.Wait()
	return results
}

// processFile runs OCR over a single uploaded file.
func (h *Handler) processFile(
	ctx context.Context,
	header *multipart.FileHeader,
) model.BatchResult {
	result := model.BatchResult{Filename: header.Filename}

	img, err := decodeImage(header)
	if err != nil {
		result.Error = err.Error()
		return result
	}

	ctx, cancel := context.WithTimeout(ctx, h.cfg.OCRTimeout)
	defer cancel()

	ocrResult, err := h.engine.ExtractTextWithBoxes(ctx, img)
	if err != nil {
		result.Error = fmt.Sprintf("OCR failed: %v", err)
		return result
	}

	result.Lines = ocrResult.TotalLines
	result.Preview = preview(ocrResult.FullText, previewRunes)
	result.Success = true

	payload := map[string]interface{}{
		"filename":    header.Filename,
		"full_text":   ocrResult.FullText,
		"boxes":       ocrResult.Boxes,
		"total_lines": ocrResult.TotalLines,
	}

	if name, err := h.saveJSONResult(payload); err != nil {
		log.Printf("failed to persist result for %q: %v", header.Filename, err)
	} else {
		result.OutputFile = name
	}

	return result
}

// preview truncates text to at most limit runes.
//
// Slicing by bytes would split multi-byte characters, which is common in
// Spanish text and yields invalid UTF-8 in the JSON response.
func preview(text string, limit int) string {
	runes := []rune(text)
	if len(runes) <= limit {
		return text
	}
	return string(runes[:limit]) + "..."
}
