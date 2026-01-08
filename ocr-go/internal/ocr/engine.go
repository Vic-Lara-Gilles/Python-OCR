package ocr

import (
	"context"
	"image"
)

// Engine defines the OCR engine interface
type Engine interface {
	// ExtractText extracts text from an image
	ExtractText(ctx context.Context, img image.Image) (*Result, error)

	// ExtractTextWithBoxes extracts text with bounding box information
	ExtractTextWithBoxes(ctx context.Context, img image.Image) (*DetailedResult, error)

	// Close releases engine resources
	Close() error
}

// Result represents basic OCR result
type Result struct {
	Text       string  `json:"text"`
	Confidence float64 `json:"confidence"`
}

// BoundingBox represents text location
type BoundingBox struct {
	X      int `json:"x"`
	Y      int `json:"y"`
	Width  int `json:"width"`
	Height int `json:"height"`
}

// TextBox represents detected text with its location
type TextBox struct {
	Text       string      `json:"text"`
	Confidence float64     `json:"confidence"`
	Box        BoundingBox `json:"box"`
}

// DetailedResult represents OCR result with boxes
type DetailedResult struct {
	FullText   string    `json:"full_text"`
	Boxes      []TextBox `json:"boxes"`
	TotalLines int       `json:"total_lines"`
	Language   string    `json:"language"`
}
