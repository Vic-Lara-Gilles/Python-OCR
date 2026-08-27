package handler

import (
	"path/filepath"
	"testing"
)

func newTestHandler(outputDir string) *Handler {
	cfg := DefaultConfig()
	cfg.OutputDir = outputDir
	return &Handler{cfg: cfg}
}

func TestResolveOutputPathAcceptsPlainNames(t *testing.T) {
	h := newTestHandler("outputs")

	path, err := h.resolveOutputPath("ocr_abc.json")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	if want := filepath.Join("outputs", "ocr_abc.json"); path != want {
		t.Errorf("got %q, want %q", path, want)
	}
}

func TestResolveOutputPathRejectsTraversal(t *testing.T) {
	h := newTestHandler("outputs")

	names := []string{
		"",
		"..",
		"../secrets.json",
		"../../etc/passwd",
		"sub/dir.json",
		"/etc/passwd",
		"outputs/../../etc/passwd",
	}

	for _, name := range names {
		if _, err := h.resolveOutputPath(name); err == nil {
			t.Errorf("expected %q to be rejected", name)
		}
	}
}
