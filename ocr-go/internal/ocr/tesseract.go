package ocr

import (
	"context"
	"fmt"
	"image"
	"strings"

	"github.com/otiai10/gosseract/v2"
)

// TesseractEngine implements Engine using Tesseract OCR
type TesseractEngine struct {
	client *gosseract.Client
	lang   string
}

// NewTesseractEngine creates a new Tesseract OCR engine
func NewTesseractEngine(lang string) (*TesseractEngine, error) {
	client := gosseract.NewClient()
	if err := client.SetLanguage(lang); err != nil {
		return nil, fmt.Errorf("failed to set language: %w", err)
	}

	return &TesseractEngine{
		client: client,
		lang:   lang,
	}, nil
}

// ExtractText extracts text from image
func (e *TesseractEngine) ExtractText(ctx context.Context, img image.Image) (*Result, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	if err := e.client.SetImageFromImage(img); err != nil {
		return nil, fmt.Errorf("failed to set image: %w", err)
	}

	text, err := e.client.Text()
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}

	confidence, err := e.client.GetMeanConfidence()
	if err != nil {
		confidence = 0
	}

	return &Result{
		Text:       strings.TrimSpace(text),
		Confidence: float64(confidence) / 100.0,
	}, nil
}

// ExtractTextWithBoxes extracts text with bounding boxes
func (e *TesseractEngine) ExtractTextWithBoxes(ctx context.Context, img image.Image) (*DetailedResult, error) {
	select {
	case <-ctx.Done():
		return nil, ctx.Err()
	default:
	}

	if err := e.client.SetImageFromImage(img); err != nil {
		return nil, fmt.Errorf("failed to set image: %w", err)
	}

	// Get bounding boxes at word level
	boxes, err := e.client.GetBoundingBoxes(gosseract.RIL_WORD)
	if err != nil {
		return nil, fmt.Errorf("failed to get bounding boxes: %w", err)
	}

	var textBoxes []TextBox
	var fullTextParts []string

	for _, box := range boxes {
		word := strings.TrimSpace(box.Word)
		if word == "" {
			continue
		}

		textBoxes = append(textBoxes, TextBox{
			Text:       word,
			Confidence: float64(box.Confidence) / 100.0,
			Box: BoundingBox{
				X:      box.Box.Min.X,
				Y:      box.Box.Min.Y,
				Width:  box.Box.Max.X - box.Box.Min.X,
				Height: box.Box.Max.Y - box.Box.Min.Y,
			},
		})

		fullTextParts = append(fullTextParts, word)
	}

	return &DetailedResult{
		FullText:   strings.Join(fullTextParts, " "),
		Boxes:      textBoxes,
		TotalLines: len(textBoxes),
		Language:   e.lang,
	}, nil
}

// Close releases resources
func (e *TesseractEngine) Close() error {
	return e.client.Close()
}
