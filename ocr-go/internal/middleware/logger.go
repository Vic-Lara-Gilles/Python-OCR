package middleware

import (
	"log"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5/middleware"
)

// Logger is a middleware that logs HTTP requests
func Logger(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		ww := middleware.NewWrapResponseWriter(w, r.ProtoMajor)
		next.ServeHTTP(ww, r)

		log.Printf(
			"%s %s %d %s %s",
			r.Method,
			r.RequestURI,
			ww.Status(),
			time.Since(start),
			r.RemoteAddr,
		)
	})
}
