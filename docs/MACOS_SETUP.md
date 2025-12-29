# Guía de Instalación para macOS (M1/M2)

## Requisitos Previos

- macOS 11.0+ (Big Sur o superior)
- Python 3.11
- Homebrew instalado

## Instalación Rápida

### 1. Instalar Homebrew (si no lo tienes)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Instalar Python 3.11

```bash
brew install python@3.11
```

### 3. Instalar Tesseract-OCR (Recomendado)

```bash
# Instalar Tesseract
brew install tesseract

# Instalar paquete de idiomas (incluye español)
brew install tesseract-lang
```

Verificar instalación:

```bash
tesseract --version
# Debería mostrar: tesseract 5.x.x

tesseract --list-langs
# Debería incluir: spa (español)
```

## Configuración del Proyecto

### Opción A: Tesseract (Recomendado para M1/M2)

```bash
# 1. Clonar/descargar el proyecto
cd /ruta/al/proyecto/Python-OCR

# 2. Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# 3. Actualizar pip
pip install --upgrade pip

# 4. Instalar proyecto con dependencias core
pip install -e .

# 5. Ejecutar aplicación
cd src
streamlit run ocr/app.py
```

Abre http://localhost:8501

### Opción B: PaddleOCR (Para tablas/layouts complejos)

⚠️ **Advertencia:** PaddleOCR en Mac M1/M2 tiene limitaciones:
- Solo funciona en modo CPU (sin GPU)
- Instalación más pesada (~2GB)
- Puede requerir builds específicos para ARM64

```bash
# 1. Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Actualizar pip
pip install --upgrade pip

# 3. Instalar proyecto con PaddleOCR
pip install -e ".[paddle]"

# 4. Modificar código (ver sección abajo)

# 5. Ejecutar aplicación
cd src
streamlit run ocr/app.py
```

## Problemas Comunes en Mac M1/M2

### Error: "No module named 'paddle'"

**Solución:**
```bash
pip install paddlepaddle>=2.6.0
```

### Error: "tesseract is not installed or it's not in your PATH"

**Solución 1 - Instalar con Homebrew:**
```bash
brew install tesseract tesseract-lang
```

**Solución 2 - Verificar PATH:**
```bash
which tesseract
# Debería mostrar: /opt/homebrew/bin/tesseract

# Si no aparece, agregar a ~/.zshrc o ~/.bash_profile:
export PATH="/opt/homebrew/bin:$PATH"
```

### Error: PaddleOCR con `cls=True` en Mac M1

**Síntoma:**
```
PaddleOCR.predict() got an unexpected keyword argument 'cls'
```

**Solución:** En `src/ocr/engine.py`, usar:
```python
ocr = PaddleOCR(
    use_angle_cls=False,  # ← False en Mac M1
    lang="es",
    use_gpu=False,
)

# Y al llamar:
result = ocr.ocr(image_path)  # Sin cls=True
```

### Error: "Symbol not found: _iconv" (OpenCV)

**Solución:**
```bash
# Desinstalar opencv-python
pip uninstall opencv-python opencv-python-headless

# Reinstalar solo headless
pip install opencv-python-headless>=4.8.0
```

### Error: "zsh: illegal hardware instruction python"

Esto ocurre si instalaste versiones x86_64 en lugar de ARM64.

**Solución:**
```bash
# 1. Verificar que Python es ARM64
file $(which python3.11)
# Debe decir: Mach-O 64-bit executable arm64

# 2. Limpiar y reinstalar
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

## Verificación de la Instalación

### Test rápido de Tesseract

```bash
# Crear imagen de prueba
echo "Hello World" | convert -pointsize 48 label:@- test.png

# Ejecutar OCR
tesseract test.png stdout -l spa

# Debería mostrar: Hello World
```

### Test de dependencias Python

```python
# test_install.py
import streamlit
import pytesseract
import PIL
import cv2
import numpy
import pandas
import fitz

print("✅ Todas las dependencias instaladas correctamente")
print(f"Tesseract version: {pytesseract.get_tesseract_version()}")
```

```bash
python test_install.py
```

## Configuración de Idiomas

### Ver idiomas instalados

```bash
tesseract --list-langs
```

### Instalar idiomas adicionales

```bash
# Instalar todos los idiomas
brew install tesseract-lang

# O descargar manualmente desde:
# https://github.com/tesseract-ocr/tessdata
# Y copiar a: /opt/homebrew/share/tessdata/
```

### Usar idioma específico en código

```python
# En src/ocr/engine.py, línea ~30:
data = pytesseract.image_to_data(
    image,
    lang='spa',  # 'spa' para español
    output_type=pytesseract.Output.DICT
)
```

Idiomas comunes:
- `eng` - Inglés
- `spa` - Español
- `fra` - Francés
- `deu` - Alemán
- `por` - Portugués

## Comparación Tesseract vs PaddleOCR en Mac M1

| Característica | Tesseract | PaddleOCR |
|----------------|-----------|-----------|
| **Instalación** | ✅ Simple (Homebrew) | ⚠️ Compleja (~2GB) |
| **Rendimiento M1** | ✅ Optimizado ARM64 | ⚠️ Solo CPU |
| **Tamaño** | ✅ ~50MB | ❌ ~2GB |
| **Idiomas** | ✅ 100+ disponibles | ✅ Múltiples idiomas |
| **Tablas** | ❌ No especializado | ✅ Mejor para tablas |
| **Precisión texto** | ✅ Buena | ✅ Muy buena |
| **Velocidad** | ✅ Rápido | ⚠️ Más lento en M1 |
| **Estabilidad M1** | ✅ Excelente | ⚠️ Requiere ajustes |

**Recomendación:** Usa Tesseract como default. Solo usa PaddleOCR si necesitas:
- Reconocimiento de tablas complejas
- Layout analysis avanzado
- Documentos con estructuras complejas

## Docker en Mac M1/M2

```bash
# Asegúrate de usar Docker Desktop para Mac (ARM64)
# Verificar plataforma:
docker info | grep Architecture
# Debe decir: Architecture: aarch64

# Construir y ejecutar
docker-compose up --build
```

**Nota:** El Dockerfile incluye `tesseract-ocr` y `tesseract-ocr-spa` pre-instalados.

## Recursos

- [Tesseract Documentation](https://tesseract-ocr.github.io/)
- [PaddleOCR macOS Issues](https://github.com/PaddlePaddle/PaddleOCR/issues?q=macos)
- [Homebrew Tesseract](https://formulae.brew.sh/formula/tesseract)
- [Python 3.11 en macOS](https://www.python.org/downloads/macos/)

## Soporte

Si encuentras problemas:
1. Revisa esta guía completa
2. Verifica versiones: `python --version`, `tesseract --version`
3. Intenta reinstalar en entorno limpio
4. Abre un issue con los detalles del error
