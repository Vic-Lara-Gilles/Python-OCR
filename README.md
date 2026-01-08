# Python-OCR

Sistema OCR para documentos y PDFs - **100% dockerizado, cero instalaciones locales**.

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tested with: pytest](https://img.shields.io/badge/tested%20with-pytest-blue.svg)](https://pytest.org/)

## Tabla de Contenidos

- [Vision General](#vision-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Patrones de Diseño](#patrones-de-diseño)
- [Principios SOLID](#principios-solid)
- [Requisitos](#requisitos)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Inicio Rapido](#inicio-rapido)
- [Comandos Docker](#comandos-docker)
- [Desarrollo](#desarrollo)
- [Testing](#testing)
- [API del Motor OCR](#api-del-motor-ocr)
- [ADRs (Architecture Decision Records)](#adrs-architecture-decision-records)
- [Troubleshooting](#troubleshooting)
- [Licencia](#licencia)

## Vision General

Python-OCR es un sistema de reconocimiento optico de caracteres (OCR) moderno y escalable, diseñado con principios de Clean Architecture y Clean Code. El proyecto implementa extraccion de texto de imagenes y documentos PDF utilizando Tesseract-OCR, con una interfaz web interactiva construida con Streamlit.

### Caracteristicas Clave

- **Arquitectura Limpia**: Separacion clara de responsabilidades entre capas
- **Principios SOLID**: Codigo mantenible y extensible
- **Test-Driven Development (TDD)**: Cobertura de pruebas unitarias
- **Dockerizado**: Despliegue consistente sin dependencias locales
- **Type Hints**: Codigo Python completamente tipado
- **Multi-formato**: Soporte para imagenes (JPG, PNG, WEBP) y PDFs

## Arquitectura del Sistema

### Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   PRESENTATION                       │
│                  (Streamlit UI)                      │
│              src/ocr/app.py                          │
├─────────────────────────────────────────────────────┤
│                  BUSINESS LOGIC                      │
│                 (OCR Engine Core)                    │
│              src/ocr/engine.py                       │
│   ┌──────────────┬──────────────┬──────────────┐   │
│   │   Extract    │  Visualize   │   Format     │   │
│   │   Methods    │   Methods    │   Methods    │   │
│   └──────────────┴──────────────┴──────────────┘   │
├─────────────────────────────────────────────────────┤
│              INFRASTRUCTURE LAYER                    │
│   ┌──────────────┬──────────────┬──────────────┐   │
│   │  Tesseract   │   OpenCV     │   PyMuPDF    │   │
│   │    OCR       │  Processing  │   PDF Parse  │   │
│   └──────────────┴──────────────┴──────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Capas Arquitectonicas

#### 1. Presentation Layer (Capa de Presentacion)
- **Responsabilidad**: Interaccion con el usuario
- **Componentes**: Streamlit UI, File uploads, Results display
- **Principio**: Separation of Concerns (SoC)

#### 2. Business Logic Layer (Capa de Logica de Negocio)
- **Responsabilidad**: Logica de procesamiento OCR
- **Componentes**: OCREngine class, Text extraction, Box visualization
- **Principio**: Single Responsibility Principle (SRP)

#### 3. Infrastructure Layer (Capa de Infraestructura)
- **Responsabilidad**: Integracion con herramientas externas
- **Componentes**: Tesseract, OpenCV, PyMuPDF, PIL
- **Principio**: Dependency Inversion Principle (DIP)

## Patrones de Diseño

### 1. Static Factory Pattern
**Ubicacion**: `OCREngine` class
**Proposito**: Proporcionar metodos estaticos para crear y procesar resultados OCR sin necesidad de instanciar la clase.

```python
class OCREngine:
    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        # Factory method for text extraction
        pass
```

**Beneficios**:
- No requiere instancia de clase
- Simplifica el API
- Cacheo eficiente con `@st.cache_data`

### 2. Facade Pattern
**Ubicacion**: `OCREngine` class
**Proposito**: Proporcionar una interfaz simplificada para operaciones complejas de OCR.

```python
# Facade oculta complejidad de pytesseract, OpenCV, PIL
result = OCREngine.extract_text_and_boxes("image.jpg")
```

**Beneficios**:
- API simple para operaciones complejas
- Encapsula multiples librerias (pytesseract, cv2, PIL)
- Facilita el testing y mantenimiento

### 3. Strategy Pattern
**Ubicacion**: Multiple extraction methods
**Proposito**: Diferentes estrategias para procesar imagenes vs PDFs.

```python
# Strategy 1: Image extraction
extract_text_and_boxes(image_path)

# Strategy 2: PDF extraction
extract_text_from_pdf(pdf_path)
```

**Beneficios**:
- Flexibilidad para agregar nuevos formatos
- Codigo desacoplado por tipo de archivo

### 4. Template Method Pattern
**Ubicacion**: PDF processing
**Proposito**: Definir estructura algoritmica para procesamiento de PDFs multi-pagina.

```python
def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    # 1. Convert PDF to images
    image_paths = OCREngine.pdf_to_images(pdf_path)

    # 2. Process each page
    for img_path in image_paths:
        result = OCREngine.extract_text_and_boxes(img_path)

    # 3. Aggregate results
    return aggregated_result
```

### 5. Caching Pattern
**Ubicacion**: Streamlit decorators
**Proposito**: Optimizar rendimiento cacheando configuracion de Tesseract.

```python
@st.cache_data
def configure_tesseract() -> None:
    # Configuration cached across reruns
    pass
```

## Principios SOLID

### S - Single Responsibility Principle (SRP)
**Implementacion**:
- `OCREngine`: Solo maneja logica OCR
- `app.py`: Solo maneja UI y presentacion
- `test_engine.py`: Solo maneja testing

**Ejemplo**:
```python
# OCREngine tiene una sola razon para cambiar: logica OCR
class OCREngine:
    @staticmethod
    def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
        # Solo extraccion de texto
        pass
```

### O - Open/Closed Principle (OCP)
**Implementacion**: El sistema esta abierto a extension (nuevos formatos) pero cerrado a modificacion.

**Ejemplo**:
```python
# Facil agregar nuevo formato sin modificar codigo existente
@staticmethod
def extract_text_from_tiff(tiff_path: str) -> Dict[str, Any]:
    # Nueva funcionalidad sin modificar metodos existentes
    pass
```

### L - Liskov Substitution Principle (LSP)
**Implementacion**: Metodos estaticos devuelven estructuras de datos consistentes.

**Ejemplo**:
```python
# Todos los metodos de extraccion devuelven el mismo contrato
result = extract_text_and_boxes(path)  # Dict[str, Any]
result = extract_text_from_pdf(path)   # Dict[str, Any]
# Ambos retornan: {"file", "full_text", "boxes", "total_lines"}
```

### I - Interface Segregation Principle (ISP)
**Implementacion**: Metodos pequeños y especificos en lugar de una interfaz monolitica.

**Ejemplo**:
```python
# Metodos especificos en lugar de un metodo gigante
extract_text_and_boxes()  # Solo extraccion
visualize_boxes()         # Solo visualizacion
generate_markdown()       # Solo formato markdown
generate_plain_text()     # Solo formato texto plano
```

### D - Dependency Inversion Principle (DIP)
**Implementacion**: Dependencia de abstracciones (pytesseract API) en lugar de implementaciones concretas.

**Ejemplo**:
```python
# OCREngine depende de la abstraccion pytesseract, no de Tesseract directamente
data = pytesseract.image_to_data(image, lang="spa")
# Podria cambiarse a otro engine OCR modificando solo esta linea
```

## Requisitos

- Docker Desktop instalado
- Nada mas

## Estructura del Proyecto

```
python-ocr/
├── src/
│   └── ocr/
│       ├── __init__.py
│       ├── engine.py          # Motor OCR con Tesseract
│       └── app.py             # Aplicacion Streamlit
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures de pytest
│   └── test_engine.py         # Tests unitarios
├── docs/
│   ├── ARCHITECTURE.md        # Documentacion arquitectura
│   ├── CLEAN_CODE_GUIDE.md    # Guia Clean Code
│   └── MACOS_SETUP.md         # Setup local macOS
├── outputs/                   # Resultados OCR (ignorado por git)
├── uploads/                   # Archivos temporales
├── Dockerfile
├── docker-compose.yml
├── Makefile                   # Comandos de desarrollo
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

## Testing

### Estrategia de Testing (TDD)

El proyecto implementa **Test-Driven Development (TDD)** con pytest.

#### Test Structure
```
tests/
├── __init__.py
├── conftest.py           # Fixtures compartidos
└── test_engine.py        # Tests unitarios del motor OCR
```

#### Cobertura de Tests

##### 1. Text Extraction Tests
```python
class TestOCREngineExtraction:
    def test_extract_text_returns_dict()
    def test_extract_text_file_field()
    def test_extract_text_boxes_is_list()
    def test_extract_empty_image()
```

##### 2. Formatting Tests
```python
class TestOCREngineFormatters:
    def test_generate_markdown_contains_header()
    def test_generate_markdown_contains_stats()
    def test_generate_plain_text()
```

##### 3. Visualization Tests
```python
class TestOCREngineVisualization:
    def test_visualize_boxes_creates_file()
    def test_visualize_boxes_returns_path()
    def test_visualize_boxes_invalid_image_raises()
```

##### 4. Data Structure Tests
```python
class TestOCREngineBoxStructure:
    def test_box_contains_required_fields()
    def test_box_confidence_is_float()
    def test_box_bbox_is_list()
```

#### Ejecutar Tests

```bash
# Todos los tests
make test

# Con detalles verbose
docker-compose exec ocr-app pytest tests/ -v

# Con cobertura
docker-compose exec ocr-app pytest tests/ --cov=src/ocr --cov-report=term

# Test especifico
docker-compose exec ocr-app pytest tests/test_engine.py::TestOCREngineExtraction -v
```

#### Fixtures (Test Data)

```python
@pytest.fixture
def sample_image() -> Generator[str, None, None]:
    """Create temporary sample image with text for OCR testing."""
    # Creates image with "Hello World", "OCR Test Image", "Python 2025"

@pytest.fixture
def empty_image() -> Generator[str, None, None]:
    """Create temporary blank image for testing edge cases."""
```

### Clean Code Practices

#### 1. Naming Conventions
- **Variables**: `snake_case` (e.g., `image_path`, `full_text`)
- **Classes**: `PascalCase` (e.g., `OCREngine`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `OUTPUT_DIR`)
- **Functions**: Descriptive verbs (e.g., `extract_text_and_boxes`, `visualize_boxes`)

#### 2. Type Hints
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Fully typed function signatures."""
    pass
```

#### 3. Documentation
- Docstrings en formato Google Style
- Comentarios explicativos en ingles
- README completo con ejemplos

#### 4. Code Organization
- **Modularidad**: Funciones pequenas y especificas
- **DRY (Don't Repeat Yourself)**: Codigo reutilizable
- **YAGNI (You Aren't Gonna Need It)**: Sin codigo innecesario
- **KISS (Keep It Simple, Stupid)**: Soluciones simples

#### 5. Error Handling
```python
try:
    result = OCREngine.extract_text_and_boxes(temp_path)
except Exception as e:
    st.error(f"Error al procesar la imagen: {str(e)}")
finally:
    if os.path.exists(temp_path):
        os.remove(temp_path)
```

## Desarrollo

### Workflow Scrum (Agile Development)

#### Sprint Planning
1. **Backlog**: Features organizados por prioridad
2. **Sprint**: Iteraciones de 2 semanas
3. **Daily Standup**: Progreso diario
4. **Sprint Review**: Demo de features completados
5. **Retrospective**: Mejora continua

#### Definition of Done (DoD)
- [ ] Codigo implementado
- [ ] Tests unitarios pasando
- [ ] Documentacion actualizada
- [ ] Code review aprobado
- [ ] Sin linter errors
- [ ] Dockerfile actualizado si es necesario

### Code Review Guidelines

#### Checklist para Reviewers
- [ ] **Funcionalidad**: Codigo cumple requisitos
- [ ] **Tests**: Cobertura adecuada de pruebas
- [ ] **SOLID**: Principios respetados
- [ ] **Clean Code**: Nombres descriptivos, funciones pequenas
- [ ] **Type Hints**: Tipos declarados correctamente
- [ ] **Documentacion**: Docstrings actualizados
- [ ] **Error Handling**: Excepciones manejadas apropiadamente
- [ ] **Performance**: Sin operaciones innecesarias
- [ ] **Security**: Sin datos sensibles expuestos

#### Pull Request Template
```markdown
## Descripcion
[Descripcion clara del cambio]

## Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva feature
- [ ] Breaking change
- [ ] Documentacion

## Tests
- [ ] Tests unitarios agregados/actualizados
- [ ] Tests locales pasando

## Checklist
- [ ] Codigo sigue guias de estilo
- [ ] Docstrings actualizados
- [ ] No rompe funcionalidad existente
```

### Modificar Codigo

El directorio `src/` esta montado como volumen. Los cambios se reflejan automaticamente:

```bash
# Editar codigo
nano src/ocr/engine.py

# Streamlit detecta cambios y recarga
```

### Makefile Commands

```bash
make help      # Mostrar todos los comandos disponibles
make start     # Iniciar aplicacion en segundo plano
make stop      # Detener aplicacion
make build     # Construir imagen Docker
make rebuild   # Reconstruir y reiniciar
make logs      # Ver logs en tiempo real
make clean     # Limpiar outputs y contenedores
make dev       # Modo desarrollo (attached)
make test      # Ejecutar tests
make lint      # Ejecutar linter (ruff)
make format    # Formatear codigo (black/ruff)
make shell     # Abrir shell en contenedor
make status    # Ver estado de contenedores
```

### Linting y Formateo

```bash
# Linter (ruff)
make lint

# Formatear codigo
make format

# Pre-commit hooks (opcional)
pip install pre-commit
pre-commit install
```

### Ver Logs

```bash
# Logs en tiempo real
docker-compose logs -f

# Ultimas 100 lineas
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

### Metodos Disponibles

#### 1. `extract_text_and_boxes(image_path: str) -> Dict[str, Any]`
Extrae texto y coordenadas de cajas delimitadoras de una imagen.

**Parametros**:
- `image_path`: Ruta a la imagen de entrada

**Retorna**:
```python
{
    "file": str,              # Nombre del archivo
    "full_text": str,         # Texto completo extraido
    "boxes": [                # Lista de cajas detectadas
        {
            "text": str,      # Texto de la caja
            "confidence": float,  # Confianza (0.0-1.0)
            "bbox": [[x,y], [x,y], [x,y], [x,y]]  # Coordenadas
        }
    ],
    "total_lines": int        # Total de lineas detectadas
}
```

#### 2. `extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]`
Extrae texto de todas las paginas de un PDF.

**Parametros**:
- `pdf_path`: Ruta al archivo PDF de entrada

**Retorna**:
```python
{
    "file": str,
    "full_text": str,         # Texto combinado de todas las paginas
    "boxes": [...],           # Boxes con campo "page" adicional
    "total_lines": int,
    "total_pages": int        # Total de paginas procesadas
}
```

#### 3. `visualize_boxes(image_path: str, output_path: str) -> str`
Dibuja cajas delimitadoras sobre la imagen.

**Parametros**:
- `image_path`: Ruta a la imagen de entrada
- `output_path`: Ruta donde guardar la imagen anotada

**Retorna**: Ruta al archivo guardado

**Visualizacion**:
- Cajas delimitadoras: Verde `(0, 255, 0)`
- Etiquetas de texto: Rojo `(255, 0, 0)`
- Fondo de etiquetas: Blanco con transparencia

#### 4. `generate_markdown(result: Dict[str, Any]) -> str`
Genera texto formateado en Markdown.

**Parametros**:
- `result`: Diccionario de resultados OCR

**Retorna**: String en formato Markdown

#### 5. `generate_plain_text(result: Dict[str, Any]) -> str`
Genera texto plano sin formato.

**Parametros**:
- `result`: Diccionario de resultados OCR

**Retorna**: String de texto plano

#### 6. `pdf_to_images(pdf_path: str) -> List[str]`
Convierte paginas de PDF a imagenes temporales.

**Parametros**:
- `pdf_path`: Ruta al archivo PDF

**Retorna**: Lista de rutas a imagenes temporales

## ADRs (Architecture Decision Records)

### ADR-001: Eleccion de Tesseract-OCR sobre PaddleOCR

**Fecha**: 2025-01-08
**Estado**: Aceptado

**Contexto**:
Necesitabamos un motor OCR para el sistema. Las opciones consideradas fueron:
1. Tesseract-OCR (Google)
2. PaddleOCR (Baidu)
3. EasyOCR

**Decision**:
Elegimos Tesseract-OCR como motor principal.

**Razones**:
- **Madurez**: Tesseract tiene 15+ años de desarrollo y es industry standard
- **Instalacion**: Facil instalacion via apt-get en Docker
- **Tamano**: Imagen Docker mas ligera (~200MB vs ~1.5GB con PaddleOCR)
- **Mantenimiento**: Soporte activo de Google
- **Idioma español**: Excelente soporte con `tesseract-ocr-spa`
- **Documentacion**: Extensa documentacion y comunidad

**Consecuencias**:
- ✅ Startup rapido del contenedor
- ✅ Menor consumo de recursos
- ✅ Mejor compatibilidad con CI/CD
- ⚠️ Precision ligeramente menor que PaddleOCR para tablas complejas
- 📝 Posible migracion futura a PaddleOCR para casos avanzados

**Alternativas Consideradas**:
- PaddleOCR: Mejor para tablas, pero imagen Docker muy pesada
- EasyOCR: Buen balance, pero menos maduro

---

### ADR-002: Streamlit como Framework UI

**Fecha**: 2025-01-08
**Estado**: Aceptado

**Contexto**:
Necesitabamos una interfaz web para el sistema OCR. Opciones:
1. Streamlit
2. FastAPI + React
3. Flask + Vanilla JS
4. Gradio

**Decision**:
Elegimos Streamlit para la interfaz web.

**Razones**:
- **Velocidad de desarrollo**: UI compleja en <300 lineas de codigo
- **Python puro**: Sin JavaScript, HTML o CSS
- **Hot reload**: Desarrollo iterativo rapido
- **Widgets built-in**: File upload, downloads, progress bars
- **Caching**: `@st.cache_data` optimiza performance
- **Deployment**: Facil deploy con Docker

**Consecuencias**:
- ✅ Prototipado rapido (MVP en 2 horas)
- ✅ Mantenimiento simple (un solo lenguaje)
- ✅ UX moderna sin esfuerzo frontend
- ⚠️ Limitado para aplicaciones muy complejas
- ⚠️ Menos control sobre CSS/HTML

**Alternativas Consideradas**:
- FastAPI + React: Mayor flexibilidad, pero 3x mas codigo
- Gradio: Similar a Streamlit, pero menos features

---

### ADR-003: Docker-First Architecture

**Fecha**: 2025-01-08
**Estado**: Aceptado

**Contexto**:
Decidir estrategia de deployment y desarrollo local.

**Decision**:
Arquitectura 100% dockerizada sin instalacion local requerida.

**Razones**:
- **Reproducibilidad**: Mismo entorno en dev/staging/prod
- **Dependencias**: Tesseract requiere instalacion nativa compleja
- **Onboarding**: Desarrolladores nuevos productivos en 5 minutos
- **CI/CD**: Pipeline de deployment simplificado
- **Multi-plataforma**: Funciona igual en macOS/Linux/Windows

**Consecuencias**:
- ✅ Zero setup para nuevos desarrolladores
- ✅ No hay "works on my machine"
- ✅ Rollback instantaneo con `docker-compose down`
- ⚠️ Debugging ligeramente mas complejo
- ⚠️ Requiere Docker Desktop instalado

**Implementacion**:
```yaml
volumes:
  - ./src:/app/src          # Hot reload codigo
  - ./outputs:/app/outputs  # Persistencia resultados
  - ./uploads:/app/uploads  # Archivos temporales
```

---

### ADR-004: Static Methods en OCREngine

**Fecha**: 2025-01-08
**Estado**: Aceptado

**Contexto**:
Diseñar API del motor OCR: metodos estaticos vs instancia de clase.

**Decision**:
Usar metodos estaticos (`@staticmethod`) en clase `OCREngine`.

**Razones**:
- **Stateless**: OCR no requiere estado interno
- **Simplicidad**: No necesita `__init__` ni manejo de instancias
- **Caching**: `@st.cache_data` funciona mejor con funciones stateless
- **Testing**: Tests mas simples sin setup de instancias
- **API limpia**: `OCREngine.extract_text()` mas claro que `engine.extract_text()`

**Consecuencias**:
- ✅ API simple y directa
- ✅ No hay overhead de instanciacion
- ✅ Thread-safe por diseño
- ⚠️ Dificil agregar estado si se requiere en futuro
- ⚠️ No se puede usar herencia facilmente

**Ejemplo**:
```python
# Simple y directo
result = OCREngine.extract_text_and_boxes("image.jpg")

# vs alternativa con instancia
engine = OCREngine(config)
result = engine.extract_text_and_boxes("image.jpg")
```

---

### ADR-005: Type Hints Obligatorios

**Fecha**: 2025-01-08
**Estado**: Aceptado

**Contexto**:
Definir estandares de calidad de codigo Python.

**Decision**:
Todos los metodos publicos deben tener type hints completos.

**Razones**:
- **Documentacion**: Type hints son documentacion ejecutable
- **IDE Support**: Autocompletado y deteccion de errores
- **Refactoring**: Mayor seguridad al refactorizar codigo
- **Mypy**: Verificacion estatica de tipos
- **Clean Code**: Contratos explicitos entre funciones

**Consecuencias**:
- ✅ Menos bugs por errores de tipo
- ✅ Mejor developer experience en IDE
- ✅ Codigo auto-documentado
- ⚠️ Leve overhead al escribir codigo inicial
- 📝 Requiere mypy en pre-commit hooks

**Ejemplo**:
```python
def extract_text_and_boxes(image_path: str) -> Dict[str, Any]:
    """Type hints obligatorios."""
    pass
```

---

### ADR-006: Pytest como Framework de Testing

**Fecha**: 2025-01-08
**Estado**: Aceptado

**Contexto**:
Elegir framework de testing para TDD.

**Decision**:
Usar pytest con fixtures y clases de test organizadas.

**Razones**:
- **Fixtures**: Sistema de fixtures potente y reutilizable
- **Assertions**: Syntax simple con `assert`
- **Parametrization**: `@pytest.mark.parametrize` para test cases multiples
- **Plugins**: Ecosistema extenso (pytest-cov, pytest-xdist)
- **Discovery**: Encuentra tests automaticamente

**Consecuencias**:
- ✅ Tests legibles y mantenibles
- ✅ Fixtures compartidos en `conftest.py`
- ✅ Coverage reports automaticos
- ✅ Parallelization con pytest-xdist

**Estructura**:
```python
class TestOCREngineExtraction:
    """Organizar tests por funcionalidad."""

    def test_extract_text_returns_dict(self, sample_image):
        """Test individual con fixture."""
        pass
```

---

### Resumen de Decisiones Tecnicas

| ADR | Decision | Impacto | Estado |
|-----|----------|---------|--------|
| ADR-001 | Tesseract-OCR | Performance, Size | ✅ Aceptado |
| ADR-002 | Streamlit UI | Developer Velocity | ✅ Aceptado |
| ADR-003 | Docker-First | Deployment, Consistency | ✅ Aceptado |
| ADR-004 | Static Methods | API Simplicity | ✅ Aceptado |
| ADR-005 | Type Hints | Code Quality | ✅ Aceptado |
| ADR-006 | Pytest | Testing Strategy | ✅ Aceptado |

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

### Healthcheck

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1
```

**Beneficios**:
- Docker detecta automaticamente si el contenedor esta saludable
- Reinicio automatico si el servicio falla
- Integracion con orchestrators (Docker Swarm, Kubernetes)

## Diseño de Sistemas

### Escalabilidad

#### Horizontal Scaling
```yaml
# docker-compose.yml para multiples instancias
services:
  ocr-app:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

#### Load Balancing (Future)
```
┌─────────┐
│  Nginx  │  Load Balancer
└────┬────┘
     │
     ├─────────┬─────────┬─────────┐
     │         │         │         │
┌────▼───┐ ┌──▼────┐ ┌──▼────┐ ┌──▼────┐
│ OCR-1  │ │ OCR-2 │ │ OCR-3 │ │ OCR-4 │
└────────┘ └───────┘ └───────┘ └───────┘
```

### Performance Optimizations

#### 1. Caching Strategy
```python
@st.cache_data
def configure_tesseract() -> None:
    """Configuration cached across reruns."""
    pass
```

#### 2. Batch Processing
- Procesamiento paralelo de multiples imagenes
- Progress bar para feedback del usuario
- Error handling individual por archivo

#### 3. Resource Management
```python
try:
    result = OCREngine.extract_text_and_boxes(temp_path)
finally:
    # Cleanup temporal files
    if os.path.exists(temp_path):
        os.remove(temp_path)
```

### Security Considerations

#### 1. File Upload Validation
```python
# Solo formatos permitidos
type=["jpg", "jpeg", "png", "webp", "pdf"]
```

#### 2. Temporary Files
- Archivos temporales con nombres unicos
- Cleanup automatico despues de procesamiento
- Directorio `uploads/` ignorado por git

#### 3. No Sensitive Data
- `.env` en `.gitignore`
- No hardcoded secrets
- Environment variables para configuracion sensible

#### 4. Docker Isolation
- Contenedor aislado del sistema host
- Solo puertos necesarios expuestos (8501)
- Usuario non-root (future improvement)

### Monitoring y Observability

#### Logs
```bash
# Logs en tiempo real
docker-compose logs -f ocr-app

# Filtrar por nivel
docker-compose logs ocr-app | grep ERROR
```

#### Metrics (Future)
- Tiempo promedio de procesamiento
- Tasa de errores
- Uso de memoria y CPU
- Numero de imagenes procesadas

#### Health Checks
```bash
# Verificar salud del contenedor
docker inspect ocr-mvp-streamlit | grep -A 5 Health

# Verificar endpoint de salud
curl http://localhost:8501/_stcore/health
```

## Documentacion Tecnica

### Documentos Disponibles

| Documento | Descripcion | Enlace |
|-----------|-------------|---------|
| **Architecture** | Arquitectura del sistema, diagramas, capas | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Clean Code Guide** | Principios Clean Code aplicados | [docs/CLEAN_CODE_GUIDE.md](docs/CLEAN_CODE_GUIDE.md) |
| **macOS Setup** | Instalacion local sin Docker | [docs/MACOS_SETUP.md](docs/MACOS_SETUP.md) |
| **ADRs** | Architecture Decision Records | Ver seccion [ADRs](#adrs-architecture-decision-records) |

### Para Desarrolladores

**Lectura recomendada**:
1. **Nuevos desarrolladores**: Empezar con [ARCHITECTURE.md](docs/ARCHITECTURE.md) para entender el sistema
2. **Antes de commit**: Revisar [CLEAN_CODE_GUIDE.md](docs/CLEAN_CODE_GUIDE.md)
3. **Decisiones de diseño**: Consultar [ADRs](#adrs-architecture-decision-records)
4. **Setup local**: Si necesitas debugging sin Docker, ver [MACOS_SETUP.md](docs/MACOS_SETUP.md)

### Contenido de ARCHITECTURE.md

- System Overview y diagramas
- Capas arquitectonicas (Presentation, Business Logic, Infrastructure)
- Data Flow y Component Diagram
- Sequence Diagrams
- Design Patterns aplicados
- SOLID Principles detallados
- Testing Strategy
- Security Architecture
- Performance Considerations
- Deployment Architecture
- Extensibility Points

### Contenido de CLEAN_CODE_GUIDE.md

- Naming Conventions completas
- Function Best Practices
- Class Design Guidelines
- Comments y Documentation
- Error Handling Patterns
- Type Hints completos
- Code Organization
- DRY, YAGNI, KISS principles
- Linting y Formatting tools
- Pre-commit hooks setup

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

### Tesseract no encuentra idioma español

```bash
# Verificar instalacion en contenedor
docker-compose exec ocr-app tesseract --list-langs

# Deberia incluir 'spa'
```

### Memoria insuficiente

```bash
# Aumentar limites en docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
```

## Roadmap y Futuras Mejoras

### Short Term (1-2 meses)
- [ ] Agregar soporte para TIFF y BMP
- [ ] Implementar API REST con FastAPI
- [ ] Dashboard de metricas y estadisticas
- [ ] Soporte multi-idioma en UI (i18n)

### Medium Term (3-6 meses)
- [ ] Procesamiento asíncrono con Celery
- [ ] Base de datos para historial (PostgreSQL)
- [ ] Autenticacion y autorizacion de usuarios
- [ ] CI/CD pipeline con GitHub Actions
- [ ] Pre-commit hooks con black, ruff, mypy

### Long Term (6-12 meses)
- [ ] Modelo OCR custom entrenado con datos propios
- [ ] Kubernetes deployment
- [ ] Microservicios architecture
- [ ] Machine learning para post-procesamiento
- [ ] Mobile app (React Native)

## Referencias y Recursos

### Documentacion Oficial
- [Tesseract-OCR Documentation](https://tesseract-ocr.github.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Docker Documentation](https://docs.docker.com/)
- [Pytest Documentation](https://docs.pytest.org/)

### Design Patterns
- [Refactoring Guru - Design Patterns](https://refactoring.guru/design-patterns)
- [Martin Fowler - Patterns](https://martinfowler.com/)

### SOLID Principles
- [Uncle Bob - Clean Code](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [SOLID Principles Explained](https://stackify.com/solid-design-principles/)

### Architecture Decision Records
- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)

### Testing
- [Test-Driven Development by Example](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

## Contribuir

### Process
1. Fork el repositorio
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Escribir tests para nueva funcionalidad
4. Implementar feature siguiendo SOLID y Clean Code
5. Ejecutar tests (`make test`)
6. Commit con mensaje descriptivo (Conventional Commits)
7. Push a branch (`git push origin feature/AmazingFeature`)
8. Abrir Pull Request

### Conventional Commits
```
feat(scope): add new feature
fix(scope): fix bug
docs: update documentation
test: add tests
refactor: refactor code
```

### Code Style
- Black para formateo
- Ruff para linting
- Type hints obligatorios
- Docstrings en formato Google

## Licencia

Este proyecto esta bajo la Licencia MIT. Ver [LICENSE](LICENSE) para mas detalles.

---

**Desarrollo local sin Docker:** Para casos especiales (testing, debugging), ver [docs/MACOS_SETUP.md](docs/MACOS_SETUP.md)

## Contacto y Soporte

Para preguntas, bugs o sugerencias:
- Abrir un [Issue en GitHub](https://github.com/tu-usuario/python-ocr/issues)
- Revisar documentacion en `docs/`
- Consultar ADRs para entender decisiones de diseño

---

**Made with ❤️ using Clean Architecture, SOLID Principles, and Test-Driven Development**
