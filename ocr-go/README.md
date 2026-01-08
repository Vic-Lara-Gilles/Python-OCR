# OCR System - Go + Tesseract

High-performance OCR system for document recognition with concurrent processing capabilities.

## Tech Stack

- **Go 1.21+** - High-performance runtime
- **Chi Router** - Lightweight HTTP router
- **Tesseract-OCR** - OCR engine via gosseract
- **Docker** - Containerized deployment

## Features

- Text extraction from images
- Bounding box visualization
- Batch processing with concurrency
- Spanish language support (configurable)
- RESTful API
- Web interface

## Quick Start

### With Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Or use Makefile
make docker-build
make docker-run
```

Open http://localhost:8080 in your browser.

### Local Development

Requirements:
- Go 1.21+
- Tesseract-OCR installed locally
- Spanish language data (`tesseract-ocr-data-spa`)

```bash
# Install dependencies
make mod

# Run
make run

# Or directly
go run ./cmd/server/main.go
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web interface |
| GET | `/health` | Health check |
| POST | `/api/extract` | Extract text from image |
| POST | `/api/visualize` | Visualize bounding boxes |
| POST | `/api/batch` | Process multiple images |
| GET | `/api/results` | List saved results |
| GET | `/api/results/{filename}` | Download result file |

## API Usage Examples

### Extract Text

```bash
curl -X POST http://localhost:8080/api/extract \
  -F "file=@document.png"
```

### Visualize Boxes

```bash
curl -X POST http://localhost:8080/api/visualize \
  -F "file=@document.png"
```

### Batch Processing

```bash
curl -X POST http://localhost:8080/api/batch \
  -F "files=@doc1.png" \
  -F "files=@doc2.png" \
  -F "files=@doc3.png"
```

## Project Structure

```
ocr-go/
├── cmd/
│   └── server/
│       └── main.go           # Application entry point
├── internal/
│   ├── handler/              # HTTP handlers
│   ├── ocr/                  # OCR engine
│   ├── model/                # Data models
│   └── middleware/           # HTTP middleware
├── web/
│   ├── static/               # CSS and JS
│   └── templates/            # HTML templates
├── outputs/                  # Generated results
├── uploads/                  # Temporary uploads
├── Dockerfile
├── docker-compose.yml
├── go.mod
└── Makefile
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 8080 | Server port |
| TESSERACT_LANG | spa | OCR language |
| APP_ENV | production | Environment |
| LOG_LEVEL | info | Log level |
| MAX_UPLOAD_SIZE | 10485760 | Max upload size (bytes) |

## Development

```bash
# Format code
make fmt

# Run tests
make test

# Build binary
make build

# Clean artifacts
make clean
```

## License

MIT
