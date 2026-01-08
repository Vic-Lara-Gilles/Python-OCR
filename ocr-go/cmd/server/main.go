package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/username/ocr-go/internal/handler"
	"github.com/username/ocr-go/internal/middleware"
	"github.com/username/ocr-go/internal/ocr"
)

func main() {
	// Ensure output directories exist
	os.MkdirAll("outputs", 0755)
	os.MkdirAll("uploads", 0755)

	// Get language from environment
	lang := getEnv("TESSERACT_LANG", "spa")

	// Initialize OCR engine
	engine, err := ocr.NewTesseractEngine(lang)
	if err != nil {
		log.Fatalf("Failed to initialize OCR engine: %v", err)
	}
	defer engine.Close()

	log.Printf("OCR engine initialized with language: %s", lang)

	// Initialize handler
	h := handler.New(engine)

	// Setup router
	r := chi.NewRouter()

	// Middleware stack
	r.Use(chimiddleware.RequestID)
	r.Use(chimiddleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(chimiddleware.Recoverer)
	r.Use(chimiddleware.Timeout(60 * time.Second))

	// CORS configuration
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: false,
		MaxAge:           300,
	}))

	// Static files
	r.Handle("/static/*", http.StripPrefix("/static/",
		http.FileServer(http.Dir("web/static"))))

	// Routes
	r.Get("/", h.Index)
	r.Get("/health", h.Health)

	// API routes
	r.Route("/api", func(r chi.Router) {
		r.Post("/extract", h.ExtractText)
		r.Post("/visualize", h.VisualizeBoxes)
		r.Post("/batch", h.BatchProcess)
		r.Get("/results", h.ListResults)
		r.Get("/results/{filename}", h.GetResult)
	})

	// Server configuration
	port := getEnv("PORT", "8080")
	srv := &http.Server{
		Addr:         fmt.Sprintf(":%s", port),
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 60 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown setup
	go func() {
		log.Printf("Server starting on http://localhost:%s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server failed to start: %v", err)
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Server shutting down...")

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("Server exited")
}

// getEnv returns environment variable value or default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
