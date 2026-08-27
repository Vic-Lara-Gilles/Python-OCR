package model

import (
	"time"

	"github.com/username/ocr-go/internal/ocr"
)

// ExtractTextResponse represents the text extraction response.
type ExtractTextResponse struct {
	Filename string        `json:"filename"`
	FullText string        `json:"full_text"`
	Boxes    []ocr.TextBox `json:"boxes"`
	// TotalLines counts the detections, which Tesseract reports at word level.
	TotalLines  int       `json:"total_lines"`
	ProcessedAt time.Time `json:"processed_at"`
	// OutputFile is the stored result name, empty when persisting failed.
	OutputFile string `json:"output_file,omitempty"`
}

// VisualizeResponse represents the visualization response.
type VisualizeResponse struct {
	Filename    string `json:"filename"`
	OutputFile  string `json:"output_file"`
	TotalBoxes  int    `json:"total_boxes"`
	DownloadURL string `json:"download_url"`
}

// BatchResult represents the result for a single file in a batch.
type BatchResult struct {
	Filename   string `json:"filename"`
	Lines      int    `json:"lines"`
	Success    bool   `json:"success"`
	Error      string `json:"error,omitempty"`
	Preview    string `json:"preview"`
	OutputFile string `json:"output_file,omitempty"`
}

// BatchProcessResponse represents a batch processing response.
type BatchProcessResponse struct {
	TotalFiles     int           `json:"total_files"`
	SuccessCount   int           `json:"success_count"`
	FailureCount   int           `json:"failure_count"`
	Results        []BatchResult `json:"results"`
	ProcessingTime string        `json:"processing_time"`
}

// ResultFile describes a stored artifact.
type ResultFile struct {
	Name     string `json:"name"`
	Size     int64  `json:"size"`
	Modified string `json:"modified"`
}

// ListResultsResponse represents the stored results listing.
type ListResultsResponse struct {
	Files []ResultFile `json:"files"`
	Count int          `json:"count"`
}

// ErrorResponse represents an error response.
type ErrorResponse struct {
	Error string `json:"error"`
}

// HealthResponse represents a health check response.
type HealthResponse struct {
	Status string `json:"status"`
}
