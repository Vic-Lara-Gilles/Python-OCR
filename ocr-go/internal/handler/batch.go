package handler

import (
	"context"
	"encoding/json"
	"fmt"
	"image"
	_ "image/gif"
	_ "image/jpeg"
	_ "image/png"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/gofrs/uuid"
	"github.com/username/ocr-go/internal/model"
)

// BatchProcess handles batch processing of multiple files
func (h *Handler) BatchProcess(w http.ResponseWriter, r *http.Request) {
	startTime := time.Now()

	// Parse multipart form (50MB max for batch)
	if err := r.ParseMultipartForm(50 << 20); err != nil {
		h.respondError(w, http.StatusBadRequest, "Failed to parse form")
		return
	}

	files := r.MultipartForm.File["files"]
	if len(files) == 0 {
		h.respondError(w, http.StatusBadRequest, "No files uploaded")
		return
	}

	// Process files concurrently
	results := make([]model.BatchResult, len(files))
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

	response := model.BatchProcessResponse{
		TotalFiles:     len(files),
		SuccessCount:   successCount,
		FailureCount:   failureCount,
		Results:        results,
		ProcessingTime: time.Since(startTime).String(),
	}

	h.respondJSON(w, http.StatusOK, response)
}

// processFile processes a single file for batch processing
func (h *Handler) processFile(ctx context.Context, header *multipart.FileHeader) model.BatchResult {
	result := model.BatchResult{
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

	// Create preview (first 100 characters)
	if len(ocrResult.FullText) > 100 {
		result.Preview = ocrResult.FullText[:100] + "..."
	} else {
		result.Preview = ocrResult.FullText
	}

	// Save result to file
	resultID := uuid.Must(uuid.NewV4()).String()
	outputPath := filepath.Join("outputs", fmt.Sprintf("ocr_%s.json", resultID))

	outputFile, err := os.Create(outputPath)
	if err == nil {
		defer outputFile.Close()
		json.NewEncoder(outputFile).Encode(map[string]interface{}{
			"filename":    header.Filename,
			"full_text":   ocrResult.FullText,
			"boxes":       ocrResult.Boxes,
			"total_lines": ocrResult.TotalLines,
		})
		result.OutputFile = filepath.Base(outputPath)
	}

	return result
}
