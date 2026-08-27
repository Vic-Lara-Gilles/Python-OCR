package handler

import (
	"context"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"net/http"
	"os"
	"path/filepath"

	"github.com/gofrs/uuid"
	"github.com/username/ocr-go/internal/model"
	"golang.org/x/image/font"
	"golang.org/x/image/font/basicfont"
	"golang.org/x/image/math/fixed"
)

const (
	boxThickness = 2
	// labelMinY keeps a label from being drawn above the top edge.
	labelMinY = 15
)

var (
	boxColor   = color.RGBA{R: 0, G: 255, B: 0, A: 255}
	labelColor = color.RGBA{R: 255, G: 0, B: 0, A: 255}
)

// VisualizeBoxes annotates an uploaded image with the detected bounding boxes.
func (h *Handler) VisualizeBoxes(w http.ResponseWriter, r *http.Request) {
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

	canvas := image.NewRGBA(img.Bounds())
	draw.Draw(canvas, img.Bounds(), img, img.Bounds().Min, draw.Src)

	for _, box := range result.Boxes {
		drawRect(canvas,
			box.Box.X, box.Box.Y,
			box.Box.X+box.Box.Width, box.Box.Y+box.Box.Height,
			boxColor, boxThickness)

		labelY := box.Box.Y - 5
		if labelY < labelMinY {
			labelY = labelMinY
		}
		drawText(canvas, box.Box.X, labelY,
			fmt.Sprintf("%s (%.0f%%)", box.Text, box.Confidence*100), labelColor)
	}

	name, err := h.saveAnnotatedImage(canvas)
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to save image")
		return
	}

	h.respondJSON(w, http.StatusOK, model.VisualizeResponse{
		Filename:    header.Filename,
		OutputFile:  name,
		TotalBoxes:  len(result.Boxes),
		DownloadURL: "/api/results/" + name,
	})
}

// saveAnnotatedImage stores the annotated canvas and returns its base name.
func (h *Handler) saveAnnotatedImage(canvas image.Image) (string, error) {
	if err := os.MkdirAll(h.cfg.OutputDir, 0o755); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}

	id, err := uuid.NewV4()
	if err != nil {
		return "", fmt.Errorf("failed to generate result id: %w", err)
	}

	name := fmt.Sprintf("boxes_%s.png", id)
	file, err := os.Create(filepath.Join(h.cfg.OutputDir, name))
	if err != nil {
		return "", fmt.Errorf("failed to create image file: %w", err)
	}
	defer file.Close()

	if err := png.Encode(file, canvas); err != nil {
		return "", fmt.Errorf("failed to encode image: %w", err)
	}

	return name, nil
}

// drawRect outlines a rectangle. Coordinates outside the image are ignored by
// Set, so no clipping is needed here.
func drawRect(img *image.RGBA, x1, y1, x2, y2 int, c color.Color, thickness int) {
	for t := 0; t < thickness; t++ {
		for x := x1; x <= x2; x++ {
			img.Set(x, y1+t, c)
			img.Set(x, y2-t, c)
		}
		for y := y1; y <= y2; y++ {
			img.Set(x1+t, y, c)
			img.Set(x2-t, y, c)
		}
	}
}

// drawText renders a label with its baseline at (x, y).
func drawText(img *image.RGBA, x, y int, text string, c color.Color) {
	drawer := &font.Drawer{
		Dst:  img,
		Src:  image.NewUniform(c),
		Face: basicfont.Face7x13,
		Dot: fixed.Point26_6{
			X: fixed.I(x),
			Y: fixed.I(y),
		},
	}
	drawer.DrawString(text)
}
