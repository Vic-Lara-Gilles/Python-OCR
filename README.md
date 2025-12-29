# Python-OCR

Sistema OCR rapido para reconocimiento de documentos con soporte para tablas.

## Stack Tecnologico

- **Docker** - Contenedorizacion completa
- **Streamlit** - Interfaz web interactiva
- **PaddleOCR-VL** - Modelo vision-lenguaje para OCR
- **Python 3.11** - Runtime

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

## Inicio Rapido

### Con Docker (Recomendado)

```bash
# Construir y ejecutar
docker-compose up --build

# En segundo plano
docker-compose up -d --build
```

Luego abre: http://localhost:8501

### Sin Docker (Desarrollo Local)

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar paquete en modo desarrollo
pip install -e .

# Ejecutar aplicacion
cd src && streamlit run ocr/app.py
```

## Caracteristicas

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

| Formato | Extension |
|---------|-----------|
| JPEG    | .jpg, .jpeg |
| PNG     | .png |
| WebP    | .webp |

## Desarrollo

### Instalacion de Dependencias de Desarrollo

```bash
pip install -r requirements-dev.txt
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src/ocr --cov-report=html

# Tests especificos
pytest tests/test_engine.py -v
```

### Formateo de Codigo

```bash
# Formatear con black
black src/ tests/

# Verificar con ruff
ruff check src/ tests/

# Type checking con mypy
mypy src/
```

### Pre-commit Hooks

```bash
# Instalar hooks
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
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

## Configuracion Docker

### Variables de Entorno

| Variable | Descripcion | Default |
|----------|-------------|---------|
| PYTHONUNBUFFERED | Salida sin buffer | 1 |
| STREAMLIT_SERVER_PORT | Puerto del servidor | 8501 |

### Volumenes

| Host | Container | Descripcion |
|------|-----------|-------------|
| ./outputs | /app/outputs | Resultados OCR |
| ./uploads | /app/uploads | Archivos temporales |

## Solucion de Problemas

### El contenedor no inicia

```bash
# Ver logs
docker-compose logs -f

# Reconstruir imagen
docker-compose build --no-cache
```

### Errores de memoria con imagenes grandes

El modelo PaddleOCR requiere memoria significativa. Para imagenes muy grandes:
- Redimensiona la imagen antes de procesar
- Aumenta la memoria del contenedor Docker

### Modelos no se descargan

Los modelos de PaddleOCR se descargan automaticamente en el primer uso.
Verifica tu conexion a internet.

## Licencia

Este proyecto esta bajo la Licencia MIT. Ver [LICENSE](LICENSE) para mas detalles.

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: add nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Guia de Commits

Este proyecto usa [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` Nueva funcionalidad
- `fix:` Correccion de bugs
- `docs:` Solo documentacion
- `refactor:` Reestructuracion de codigo
- `test:` Agregar o modificar tests
- `chore:` Tareas de mantenimiento
