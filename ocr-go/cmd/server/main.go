package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/username/ocr-go/internal/handler"
	"github.com/username/ocr-go/internal/middleware"
	"github.com/username/ocr-go/internal/ocr"
)

const shutdownTimeout = 30 * time.Second

func main() {
	if err := run(); err != nil {
		log.Fatalf("fatal: %v", err)
	}
}

// run wires the application together and blocks until shutdown completes.
//
// Errors are returned rather than fatally logged so every deferred cleanup,
// including closing the OCR engine, actually runs.
func run() error {
	cfg := handler.DefaultConfig()
	cfg.OutputDir = getEnv("OUTPUT_DIR", cfg.OutputDir)
	cfg.MaxUploadBytes = int64(getEnvInt("MAX_UPLOAD_SIZE_MB", 10)) << 20
	cfg.MaxBatchBytes = int64(getEnvInt("MAX_BATCH_SIZE_MB", 50)) << 20
	cfg.OCRTimeout = time.Duration(getEnvInt("OCR_TIMEOUT_SECONDS", 30)) * time.Second
	cfg.BatchConcurrency = getEnvInt("OCR_POOL_SIZE", ocr.DefaultPoolSize)

	if err := os.MkdirAll(cfg.OutputDir, 0o755); err != nil {
		return err
	}

	lang := getEnv("TESSERACT_LANG", "spa")

	engine, err := ocr.NewTesseractEngineWithPool(lang, cfg.BatchConcurrency)
	if err != nil {
		return err
	}
	defer engine.Close()

	log.Printf("OCR engine ready: language=%s pool=%d", lang, engine.PoolSize())

	h, err := handler.New(engine, cfg)
	if err != nil {
		return err
	}

	port := getEnv("PORT", "8080")
	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      newRouter(h),
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 90 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	serverErr := make(chan error, 1)
	go func() {
		log.Printf("Server listening on http://localhost:%s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			serverErr <- err
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	select {
	case err := <-serverErr:
		return err
	case <-quit:
		log.Println("Shutting down...")
	}

	ctx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		return err
	}

	log.Println("Server exited")
	return nil
}

// newRouter builds the HTTP router with its middleware stack.
func newRouter(h *handler.Handler) http.Handler {
	r := chi.NewRouter()

	r.Use(chimiddleware.RequestID)
	r.Use(chimiddleware.RealIP)
	r.Use(middleware.Logger)
	r.Use(chimiddleware.Recoverer)
	r.Use(chimiddleware.Timeout(120 * time.Second))

	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   allowedOrigins(),
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Content-Type"},
		AllowCredentials: false,
		MaxAge:           300,
	}))

	r.Handle("/static/*", http.StripPrefix("/static/",
		http.FileServer(http.Dir("web/static"))))

	r.Get("/", h.Index)
	r.Get("/health", h.Health)

	r.Route("/api", func(r chi.Router) {
		r.Post("/extract", h.ExtractText)
		r.Post("/visualize", h.VisualizeBoxes)
		r.Post("/batch", h.BatchProcess)
		r.Get("/results", h.ListResults)
		r.Get("/results/{filename}", h.GetResult)
	})

	return r
}

// allowedOrigins reads the CORS allow list from the environment.
//
// The wildcard default keeps local development frictionless; deployments
// should set ALLOWED_ORIGINS to the sites that actually call the API.
func allowedOrigins() []string {
	raw := getEnv("ALLOWED_ORIGINS", "*")

	origins := make([]string, 0, 4)
	for _, origin := range strings.Split(raw, ",") {
		if trimmed := strings.TrimSpace(origin); trimmed != "" {
			origins = append(origins, trimmed)
		}
	}

	if len(origins) == 0 {
		return []string{"*"}
	}
	return origins
}

// getEnv returns an environment variable, or defaultValue when unset or empty.
func getEnv(key, defaultValue string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return defaultValue
}

// getEnvInt returns an integer environment variable, or defaultValue when
// unset, empty or unparsable.
func getEnvInt(key string, defaultValue int) int {
	value, err := strconv.Atoi(getEnv(key, ""))
	if err != nil || value <= 0 {
		return defaultValue
	}
	return value
}
