package handler

import (
	"context"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	_ "image/gif"
	_ "image/jpeg"
	"image/png"
	_ "image/png"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gofrs/uuid"
	"golang.org/x/image/font"
	"golang.org/x/image/font/basicfont"
	"golang.org/x/image/math/fixed"
)

// VisualizeBoxes handles bounding box visualization
func (h *Handler) VisualizeBoxes(w http.ResponseWriter, r *http.Request) {
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

	// Create drawable image
	bounds := img.Bounds()
	rgba := image.NewRGBA(bounds)
	draw.Draw(rgba, bounds, img, bounds.Min, draw.Src)

	// Draw bounding boxes
	green := color.RGBA{0, 255, 0, 255}
	red := color.RGBA{255, 0, 0, 255}

	for _, box := range result.Boxes {
		// Draw green rectangle
		drawRect(rgba, box.Box.X, box.Box.Y,
			box.Box.X+box.Box.Width, box.Box.Y+box.Box.Height, green, 2)

		// Draw red text label
		labelY := box.Box.Y - 5
		if labelY < 15 {
			labelY = 15
		}
		drawText(rgba, box.Box.X, labelY,
			fmt.Sprintf("%s (%.0f%%)", box.Text, box.Confidence*100), red)
	}

	// Save annotated image
	resultID := uuid.Must(uuid.NewV4()).String()
	outputPath := filepath.Join("outputs", fmt.Sprintf("boxes_%s.png", resultID))

	outputFile, err := os.Create(outputPath)
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to save image")
		return
	}
	defer outputFile.Close()

	if err := png.Encode(outputFile, rgba); err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to encode image")
		return
	}

	// Send response
	h.respondJSON(w, http.StatusOK, map[string]interface{}{
		"filename":     header.Filename,
		"output_file":  filepath.Base(outputPath),
		"total_boxes":  len(result.Boxes),
		"download_url": fmt.Sprintf("/api/results/%s", filepath.Base(outputPath)),
	})
}

// GetResult serves a result file
func (h *Handler) GetResult(w http.ResponseWriter, r *http.Request) {
	filename := filepath.Base(r.URL.Path)
	filePath := filepath.Join("outputs", filename)

	// Check if file exists
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		h.respondError(w, http.StatusNotFound, "File not found")
		return
	}

	// Determine content type
	ext := filepath.Ext(filename)
	switch ext {
	case ".json":
		w.Header().Set("Content-Type", "application/json")
	case ".png":
		w.Header().Set("Content-Type", "image/png")
	default:
		w.Header().Set("Content-Type", "application/octet-stream")
	}

	// Serve file
	file, err := os.Open(filePath)
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to open file")
		return
	}
	defer file.Close()

	io.Copy(w, file)
}

// ListResults lists all result files
func (h *Handler) ListResults(w http.ResponseWriter, r *http.Request) {
	entries, err := os.ReadDir("outputs")
	if err != nil {
		h.respondError(w, http.StatusInternalServerError, "Failed to read outputs directory")
		return
	}

	files := make([]map[string]interface{}, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		info, err := entry.Info()
		if err != nil {
			continue
		}
		files = append(files, map[string]interface{}{
			"name":     entry.Name(),
			"size":     info.Size(),
			"modified": info.ModTime().Format(time.RFC3339),
		})
	}

	h.respondJSON(w, http.StatusOK, map[string]interface{}{
		"files": files,
		"count": len(files),
	})
}

// Helper function to draw rectangle on image
func drawRect(img *image.RGBA, x1, y1, x2, y2 int, c color.Color, thickness int) {
	for t := 0; t < thickness; t++ {
		// Top edge
		for x := x1; x <= x2; x++ {
			img.Set(x, y1+t, c)
		}
		// Bottom edge
		for x := x1; x <= x2; x++ {
			img.Set(x, y2-t, c)
		}
		// Left edge
		for y := y1; y <= y2; y++ {
			img.Set(x1+t, y, c)
		}
		// Right edge
		for y := y1; y <= y2; y++ {
			img.Set(x2-t, y, c)
		}
	}
}

// Helper function to draw text on image
func drawText(img *image.RGBA, x, y int, text string, c color.Color) {
	point := fixed.Point26_6{
		X: fixed.Int26_6(x * 64),
		Y: fixed.Int26_6(y * 64),
	}

	d := &font.Drawer{
		Dst:  img,
		Src:  image.NewUniform(c),
		Face: basicfont.Face7x13,
		Dot:  point,
	}
	d.DrawString(text)
}
