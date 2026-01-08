# Multi-stage build for optimal image size
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev tesseract-ocr-dev leptonica-dev

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary with optimizations
RUN CGO_ENABLED=1 GOOS=linux go build -ldflags="-s -w" -o ocr-server ./cmd/server

# Runtime stage
FROM alpine:3.19

# Install runtime dependencies
RUN apk add --no-cache \
    tesseract-ocr \
    tesseract-ocr-data-spa \
    leptonica \
    ca-certificates

WORKDIR /app

# Copy binary and web assets
COPY --from=builder /build/ocr-server .
COPY --from=builder /build/web ./web

# Create directories
RUN mkdir -p outputs uploads

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run as non-root user
RUN adduser -D -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["./ocr-server"]
