package handler

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/username/ocr-go/internal/model"
)

// newResultsRouter wires the result routes against a temporary output dir.
func newResultsRouter(t *testing.T) (*chi.Mux, string) {
	t.Helper()

	outputDir := t.TempDir()
	h := newTestHandler(outputDir)

	r := chi.NewRouter()
	r.Get("/api/results", h.ListResults)
	r.Get("/api/results/{filename}", h.GetResult)

	return r, outputDir
}

func TestGetResultServesStoredFile(t *testing.T) {
	router, outputDir := newResultsRouter(t)

	body := []byte(`{"full_text":"hola"}`)
	if err := os.WriteFile(filepath.Join(outputDir, "ocr_1.json"), body, 0o644); err != nil {
		t.Fatalf("failed to seed file: %v", err)
	}

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/results/ocr_1.json", nil))

	if rec.Code != http.StatusOK {
		t.Fatalf("got status %d, want %d", rec.Code, http.StatusOK)
	}
	if rec.Body.String() != string(body) {
		t.Errorf("got body %q, want %q", rec.Body.String(), body)
	}
}

func TestGetResultRejectsTraversal(t *testing.T) {
	router, _ := newResultsRouter(t)

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(
		http.MethodGet, "/api/results/..%2f..%2fetc%2fpasswd", nil))

	if rec.Code == http.StatusOK {
		t.Errorf("traversal was served with status %d", rec.Code)
	}
}

func TestGetResultReturnsNotFoundForMissingFile(t *testing.T) {
	router, _ := newResultsRouter(t)

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/results/nope.json", nil))

	if rec.Code != http.StatusNotFound {
		t.Errorf("got status %d, want %d", rec.Code, http.StatusNotFound)
	}
}

func TestListResultsReportsStoredFiles(t *testing.T) {
	router, outputDir := newResultsRouter(t)

	for _, name := range []string{"ocr_1.json", "boxes_1.png"} {
		if err := os.WriteFile(filepath.Join(outputDir, name), []byte("x"), 0o644); err != nil {
			t.Fatalf("failed to seed file: %v", err)
		}
	}

	rec := httptest.NewRecorder()
	router.ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/results", nil))

	var response model.ListResultsResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if response.Count != 2 {
		t.Errorf("got count %d, want 2", response.Count)
	}
}

func TestListResultsOnMissingDirectory(t *testing.T) {
	h := newTestHandler(filepath.Join(t.TempDir(), "does-not-exist"))

	rec := httptest.NewRecorder()
	h.ListResults(rec, httptest.NewRequest(http.MethodGet, "/api/results", nil))

	if rec.Code != http.StatusOK {
		t.Fatalf("got status %d, want %d", rec.Code, http.StatusOK)
	}

	var response model.ListResultsResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &response); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}

	if response.Count != 0 {
		t.Errorf("got count %d, want 0", response.Count)
	}
}
