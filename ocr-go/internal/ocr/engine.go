package ocr

import (
	"context"
	"errors"
	"image"
)

// ErrEngineClosed is returned when a request reaches an engine that has
// already released its resources.
var ErrEngineClosed = errors.New("ocr: engine is closed")

// Engine defines the OCR engine interface.
//
// Implementations must be safe for concurrent use by multiple goroutines.
type Engine interface {
	// ExtractText extracts text from an image.
	ExtractText(ctx context.Context, img image.Image) (*Result, error)

	// ExtractTextWithBoxes extracts text with bounding box information.
	ExtractTextWithBoxes(ctx context.Context, img image.Image) (*DetailedResult, error)

	// Close releases engine resources.
	Close() error
}

// Result represents a basic OCR result.
type Result struct {
	Text string `json:"text"`
	// Confidence is the mean confidence of the detection, in the 0-1 range.
	Confidence float64 `json:"confidence"`
}

// BoundingBox represents the location of detected text, in pixels.
type BoundingBox struct {
	X      int `json:"x"`
	Y      int `json:"y"`
	Width  int `json:"width"`
	Height int `json:"height"`
}

// TextBox represents a detected word together with its location.
type TextBox struct {
	Text string `json:"text"`
	// Confidence is the detection confidence, in the 0-1 range.
	Confidence float64     `json:"confidence"`
	Box        BoundingBox `json:"box"`
}

// DetailedResult represents an OCR result with per-word boxes.
type DetailedResult struct {
	FullText string    `json:"full_text"`
	Boxes    []TextBox `json:"boxes"`
	// TotalLines counts the detections, which Tesseract reports at word level.
	TotalLines int    `json:"total_lines"`
	Language   string `json:"language"`
}
