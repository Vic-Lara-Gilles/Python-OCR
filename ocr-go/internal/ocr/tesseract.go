package ocr

import (
	"context"
	"fmt"
	"image"
	"strings"
	"sync"

	"github.com/otiai10/gosseract/v2"
)

// DefaultPoolSize is the number of Tesseract clients created by default.
const DefaultPoolSize = 4

// TesseractEngine implements Engine on top of Tesseract.
//
// gosseract.Client wraps a C API handle that is NOT safe for concurrent use:
// two goroutines sharing one client interleave SetImage and Text calls and read
// each other's results. The engine therefore keeps a pool of clients and hands
// out exactly one per in-flight request.
type TesseractEngine struct {
	available chan *gosseract.Client
	clients   []*gosseract.Client
	lang      string
	closeOnce sync.Once
}

// NewTesseractEngine creates an engine backed by a pool of DefaultPoolSize clients.
func NewTesseractEngine(lang string) (*TesseractEngine, error) {
	return NewTesseractEngineWithPool(lang, DefaultPoolSize)
}

// NewTesseractEngineWithPool creates an engine backed by size clients.
//
// A size below one is raised to one. Every client is configured with lang
// upfront so requests never pay for language switching.
func NewTesseractEngineWithPool(lang string, size int) (*TesseractEngine, error) {
	if size < 1 {
		size = 1
	}

	engine := &TesseractEngine{
		available: make(chan *gosseract.Client, size),
		clients:   make([]*gosseract.Client, 0, size),
		lang:      lang,
	}

	for i := 0; i < size; i++ {
		client := gosseract.NewClient()
		if err := client.SetLanguage(lang); err != nil {
			client.Close()
			engine.closeClients()
			return nil, fmt.Errorf("failed to set language %q: %w", lang, err)
		}
		engine.clients = append(engine.clients, client)
		engine.available <- client
	}

	return engine, nil
}

// PoolSize reports how many requests the engine can process in parallel.
func (e *TesseractEngine) PoolSize() int {
	return cap(e.available)
}

// acquire takes a client from the pool, waiting until one is free or the
// context is done.
func (e *TesseractEngine) acquire(ctx context.Context) (*gosseract.Client, error) {
	select {
	case client, ok := <-e.available:
		if !ok {
			return nil, ErrEngineClosed
		}
		return client, nil
	case <-ctx.Done():
		return nil, ctx.Err()
	}
}

// release returns a client to the pool.
func (e *TesseractEngine) release(client *gosseract.Client) {
	defer func() {
		// Sending on a channel already closed by Close panics; in that case
		// closeClients has taken care of disposing of the client.
		_ = recover()
	}()
	e.available <- client
}

// ExtractText extracts the plain text of an image.
func (e *TesseractEngine) ExtractText(ctx context.Context, img image.Image) (*Result, error) {
	client, err := e.acquire(ctx)
	if err != nil {
		return nil, err
	}
	defer e.release(client)

	if err := client.SetImageFromImage(img); err != nil {
		return nil, fmt.Errorf("failed to set image: %w", err)
	}

	text, err := client.Text()
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}

	confidence, err := client.GetMeanConfidence()
	if err != nil {
		confidence = 0
	}

	return &Result{
		Text:       strings.TrimSpace(text),
		Confidence: float64(confidence) / 100.0,
	}, nil
}

// ExtractTextWithBoxes extracts text along with word level bounding boxes.
func (e *TesseractEngine) ExtractTextWithBoxes(ctx context.Context, img image.Image) (*DetailedResult, error) {
	client, err := e.acquire(ctx)
	if err != nil {
		return nil, err
	}
	defer e.release(client)

	if err := client.SetImageFromImage(img); err != nil {
		return nil, fmt.Errorf("failed to set image: %w", err)
	}

	boxes, err := client.GetBoundingBoxes(gosseract.RIL_WORD)
	if err != nil {
		return nil, fmt.Errorf("failed to get bounding boxes: %w", err)
	}

	textBoxes := make([]TextBox, 0, len(boxes))
	words := make([]string, 0, len(boxes))

	for _, box := range boxes {
		word := strings.TrimSpace(box.Word)
		if word == "" {
			continue
		}

		textBoxes = append(textBoxes, TextBox{
			Text:       word,
			Confidence: box.Confidence / 100.0,
			Box: BoundingBox{
				X:      box.Box.Min.X,
				Y:      box.Box.Min.Y,
				Width:  box.Box.Dx(),
				Height: box.Box.Dy(),
			},
		})

		words = append(words, word)
	}

	return &DetailedResult{
		FullText:   strings.Join(words, " "),
		Boxes:      textBoxes,
		TotalLines: len(textBoxes),
		Language:   e.lang,
	}, nil
}

// Close releases every client in the pool. It is safe to call more than once.
func (e *TesseractEngine) Close() error {
	var err error
	e.closeOnce.Do(func() {
		close(e.available)
		err = e.closeClients()
	})
	return err
}

// closeClients disposes of every created client, returning the first failure.
func (e *TesseractEngine) closeClients() error {
	var firstErr error
	for _, client := range e.clients {
		if err := client.Close(); err != nil && firstErr == nil {
			firstErr = err
		}
	}
	e.clients = nil
	return firstErr
}
