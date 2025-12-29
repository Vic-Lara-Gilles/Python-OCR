# Python-OCR

Sistema OCR para documentos y PDFs - **100% dockerizado, cero instalaciones locales**.

## Requisitos

- Docker Desktop instalado
- Nada más

## Estructura del Proyecto

```
python-ocr/
├── src/
│   └── ocr/
│       ├── __init__.py
│       ├── engine.py          # Motor OCR con PaddleOCR
│       └── app.py             # Aplicacion Streamlit
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures de pytest
│   └── test_engine.py         # Tests unitarios
├── outputs/                   # Resultados OCR (ignorado por git)
├── uploads/                   # Archivos temporales
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── LICENSE
└── README.md
```

## Inicio Rápido

```bash
# Iniciar aplicación
docker-compose up --build
```

Abre http://localhost:8501

**El contenedor incluye TODO:**
- Python 3.11
- Tesseract-OCR + idioma español
- PyMuPDF para PDFs
- Todas las dependencias
- Streamlit configurado

## Comandos Docker

```bash
# Iniciar (primer plano)
docker-compose up --build

# Iniciar (segundo plano)
docker-compose up -d --build

# Detener
docker-compose down

# Ver logs
docker-compose logs -f

# Reconstruir limpio
docker-compose down && docker-compose build --no-cache && docker-compose up
```

### 1. Extraccion de Texto
- Sube una imagen y extrae todo el texto detectado
- Exporta a JSON, Markdown o TXT
- Muestra estadisticas de lineas detectadas

### 2. Visualizacion de Cajas
- Dibuja cajas delimitadoras sobre el texto detectado
- Muestra confianza de cada deteccion
- Descarga imagen anotada

### 3. Procesamiento por Lotes
- Procesa multiples imagenes simultaneamente
- Genera tabla resumen con resultados
- Exporta resultados a CSV

## Formatos Soportados

| Formato | Extensión | Notas |
|---------|-----------|-------|
| JPEG    | .jpg, .jpeg | Imágenes estándar |
| PNG     | .png | Transparencia soportada |
| WebP    | .webp | Formato moderno |
| PDF     | .pdf | Multi-página con PyMuPDF |

## Stack Tecnológico

### Docker
- Imagen base: `python:3.11-slim`
- Sistema: Tesseract-OCR + español
- Puerto: 8501
- Volúmenes: outputs, uploads, src (hot reload)

### Python
- **Streamlit 1.39.0** - Interfaz web
- **pytesseract** - Wrapper Python para Tesseract
- **PyMuPDF** - Procesamiento PDFs
- **OpenCV-headless** - Procesamiento imágenes
- **Pillow** - Manipulación imágenes

### OCR
- **Motor:** Tesseract 5.x
- **Idioma:** Español (spa)
- **Método:** `pytesseract.image_to_data()`
- **Output:** Texto + coordenadas + confianza

## Desarrollo

### Modificar Código

El directorio `src/` está montado como volumen. Los cambios se reflejan automáticamente:

```bash
# Editar código
nano src/ocr/engine.py

# Streamlit detecta cambios y recarga
```

### Ejecutar Tests

```bash
# Dentro del contenedor
docker-compose exec ocr-app pytest
```

### Ver Logs

```bash
# Logs en tiempo real
docker-compose logs -f

# Últimas 100 líneas
docker-compose logs --tail=100
```

### Reconstruir Imagen

```bash
# Si cambias requirements.txt o Dockerfile
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## API del Motor OCR

### OCREngine

```python
from ocr.engine import OCREngine

# Extraer texto de imagen
result = OCREngine.extract_text_and_boxes("imagen.jpg")
# result = {
#     "file": "imagen.jpg",
#     "full_text": "Texto extraido...",
#     "boxes": [...],
#     "total_lines": 10
# }

# Generar markdown
markdown = OCREngine.generate_markdown(result)

# Generar texto plano
plain_text = OCREngine.generate_plain_text(result)

# Visualizar cajas delimitadoras
OCREngine.visualize_boxes("imagen.jpg", "output.png")
```

## Configuración Docker

### Volúmenes

```yaml
volumes:
  - ./outputs:/app/outputs    # Resultados persistentes
  - ./uploads:/app/uploads    # Archivos temporales
  - ./src:/app/src            # Hot reload código
```

Los resultados OCR se guardan en `./outputs/` y persisten tras detener el contenedor.

### Variables de Entorno

```yaml
environment:
  - PYTHONUNBUFFERED=1      # Logs en tiempo real
  - PYTHONPATH=/app/src     # Import path
```

## Troubleshooting

### Puerto 8501 ocupado

```bash
# Cambiar puerto en docker-compose.yml
ports:
  - "8502:8501"  # Usa 8502 en host
```

### Contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs ocr-app

# Limpiar y reconstruir
docker-compose down
docker system prune -a
docker-compose up --build
```

### Archivos no se guardan

```bash
# Verificar permisos
ls -la outputs/
chmod 777 outputs/ uploads/
```

### Error de dependencias

```bash
# Reconstruir sin caché
docker-compose build --no-cache
```

## Licencia

Este proyecto esta bajo la Licencia MIT. Ver [LICENSE](LICENSE) para mas detalles.

---

**Desarrollo local sin Docker:** Para casos especiales (testing, debugging), ver [docs/MACOS_SETUP.md](docs/MACOS_SETUP.md)
