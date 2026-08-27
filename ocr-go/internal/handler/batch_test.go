package handler

import (
	"strings"
	"testing"
	"unicode/utf8"
)

func TestPreviewKeepsShortText(t *testing.T) {
	if got := preview("hola", 100); got != "hola" {
		t.Errorf("got %q, want %q", got, "hola")
	}
}

func TestPreviewTruncatesLongText(t *testing.T) {
	got := preview(strings.Repeat("a", 500), 100)

	if !strings.HasSuffix(got, "...") {
		t.Errorf("got %q, want a truncated value", got)
	}
	if want := 103; len(got) != want {
		t.Errorf("got length %d, want %d", len(got), want)
	}
}

func TestPreviewDoesNotSplitMultiByteRunes(t *testing.T) {
	// Every rune here is two bytes, so a byte-based cut would leave the
	// response holding invalid UTF-8.
	got := preview(strings.Repeat("ñ", 200), 100)

	if !utf8.ValidString(got) {
		t.Errorf("got invalid UTF-8: %q", got)
	}
	if want := 100; utf8.RuneCountInString(strings.TrimSuffix(got, "...")) != want {
		t.Errorf("got %d runes, want %d",
			utf8.RuneCountInString(strings.TrimSuffix(got, "...")), want)
	}
}
