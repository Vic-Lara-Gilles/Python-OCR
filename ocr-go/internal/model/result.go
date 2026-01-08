package model

import "time"

// ExtractTextResponse represents the text extraction response
type ExtractTextResponse struct {
	Filename    string                   `json:"filename"`
	FullText    string                   `json:"full_text"`
	Boxes       []map[string]interface{} `json:"boxes"`
	TotalLines  int                      `json:"total_lines"`
	ProcessedAt time.Time                `json:"processed_at"`
}

// VisualizeResponse represents the visualization response
type VisualizeResponse struct {
	Filename    string `json:"filename"`
	OutputFile  string `json:"output_file"`
	TotalBoxes  int    `json:"total_boxes"`
	DownloadURL string `json:"download_url"`
}

// BatchResult represents result for single file in batch processing
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

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error string `json:"error"`
}

// HealthResponse represents health check response
type HealthResponse struct {
	Status string `json:"status"`
}
