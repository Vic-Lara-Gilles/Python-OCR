"""Streamlit application for the Tesseract-based OCR system."""

from __future__ import annotations

import json
import logging
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List

import pandas as pd
import streamlit as st

from ocr.config import SUPPORTED_SUFFIXES, settings
from ocr.engine import OCREngine, OCRError

logger = logging.getLogger("ocr")

UPLOAD_TYPES = sorted(suffix.lstrip(".") for suffix in SUPPORTED_SUFFIXES)
PREVIEW_LENGTH = 100
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")

TASK_EXTRACT = "Extraer Texto"
TASK_VISUALIZE = "Visualizar Cajas"
TASK_BATCH = "Multiples Imagenes"


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def configure_logging() -> None:
    """Configure the package logger once per process."""
    if logger.handlers:
        return
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def safe_stem(filename: str) -> str:
    """Return a filesystem-safe base name for an uploaded file.

    Upload names are attacker-controlled: stripping the directory part and
    every unusual character prevents writing outside the output directory.

    Args:
        filename: Original name of the uploaded file.

    Returns:
        A sanitized base name, never empty.
    """
    stem = Path(filename).stem
    cleaned = _UNSAFE_CHARS.sub("_", stem).strip("._-")
    return cleaned or "documento"


def safe_suffix(filename: str) -> str:
    """Return the lowercase extension of a file, or an empty string."""
    suffix = Path(filename).suffix.lower()
    return suffix if suffix in SUPPORTED_SUFFIXES else ""


@contextmanager
def staged_upload(uploaded_file: Any) -> Iterator[Path]:
    """Write an upload to a private temporary directory and clean it up.

    Args:
        uploaded_file: Streamlit ``UploadedFile`` instance.

    Yields:
        Path to the staged file.

    Raises:
        OCRError: If the upload exceeds the configured size limit.
    """
    size = getattr(uploaded_file, "size", None)
    if size is not None and size > settings.max_upload_bytes:
        limit_mb = settings.max_upload_bytes / (1024 * 1024)
        raise OCRError(f"El archivo supera el limite de {limit_mb:.0f} MB.")

    with tempfile.TemporaryDirectory() as tmpdir:
        staged = Path(tmpdir) / (
            f"{safe_stem(uploaded_file.name)}{safe_suffix(uploaded_file.name)}"
        )
        staged.write_bytes(uploaded_file.getbuffer())
        yield staged


def persist_results(result: Dict[str, Any], stem: str) -> Dict[str, Dict[str, str]]:
    """Write the JSON, Markdown and plain text renderings of a result.

    Args:
        result: OCR extraction result dictionary.
        stem: Sanitized base name for the generated files.

    Returns:
        Mapping of format name to ``{"filename": ..., "content": ...}``.
    """
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    payloads = {
        "json": {
            "filename": f"ocr_{stem}.json",
            "content": json.dumps(result, ensure_ascii=False, indent=2),
        },
        "markdown": {
            "filename": f"ocr_{stem}.md",
            "content": OCREngine.generate_markdown(result),
        },
        "text": {
            "filename": f"ocr_{stem}.txt",
            "content": OCREngine.generate_plain_text(result),
        },
    }

    for payload in payloads.values():
        (settings.output_dir / payload["filename"]).write_text(
            payload["content"], encoding="utf-8"
        )

    return payloads


def render_download_buttons(payloads: Dict[str, Dict[str, str]], key: str) -> None:
    """Render one download button per generated format."""
    mimes = {
        "text": ("Descargar TXT", "text/plain"),
        "markdown": ("Descargar Markdown", "text/markdown"),
        "json": ("Descargar JSON", "application/json"),
    }

    for column, (fmt, (label, mime)) in zip(st.columns(len(mimes)), mimes.items()):
        with column:
            st.download_button(
                label=label,
                data=payloads[fmt]["content"],
                file_name=payloads[fmt]["filename"],
                mime=mime,
                use_container_width=True,
                key=f"{key}_{fmt}",
            )


def preview_text(text: str) -> str:
    """Truncate text for tabular previews."""
    if len(text) <= PREVIEW_LENGTH:
        return text
    return f"{text[:PREVIEW_LENGTH]}..."


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------


def render_sidebar() -> str:
    """Render the sidebar and return the selected task."""
    with st.sidebar:
        st.title("OCR MVP")
        st.markdown("---")

        task = st.radio(
            "Selecciona una tarea:",
            [TASK_EXTRACT, TASK_VISUALIZE, TASK_BATCH],
            help="Elige el tipo de procesamiento OCR que deseas realizar",
        )

        st.markdown("---")
        st.markdown("### Stack Tecnologico")
        st.markdown(
            """
            - **Docker** - Contenedorizacion
            - **Streamlit** - Interfaz web
            - **Tesseract-OCR** - Motor OCR
            - **Python 3.11** - Runtime
            - **OpenCV** - Procesamiento de imagenes
            """
        )

        st.markdown("---")
        st.markdown("### Configuracion Activa")
        st.markdown(f"**Idioma OCR:** `{settings.lang}`")
        st.markdown(
            f"**Tamano maximo:** {settings.max_upload_bytes / (1024 * 1024):.0f} MB"
        )

        st.markdown("---")
        st.markdown("### Formatos Soportados")
        st.markdown("**Imagenes:** JPG, JPEG, PNG, WEBP, BMP, TIFF")
        st.markdown("**Documentos:** PDF")

    return task


# ----------------------------------------------------------------------
# Tasks
# ----------------------------------------------------------------------


def render_extract_task() -> None:
    """Render the single-document text extraction task."""
    st.subheader("Extraer Texto de Imagen o PDF")

    uploaded_file = st.file_uploader(
        "Sube una imagen o PDF", type=UPLOAD_TYPES, key="extract_text"
    )
    if not uploaded_file:
        return

    is_pdf = OCREngine.is_pdf(uploaded_file.name)
    col_preview, col_action = st.columns(2)

    with col_preview:
        if is_pdf:
            st.info(f"Archivo PDF: {uploaded_file.name}")
        else:
            st.image(uploaded_file, caption="Imagen Original", use_container_width=True)

    with col_action:
        if not st.button("Extraer Texto", type="primary", use_container_width=True):
            return

        with st.spinner("Ejecutando OCR... Esto puede tardar unos segundos"):
            try:
                with staged_upload(uploaded_file) as staged:
                    result = OCREngine.extract_document(str(staged))
            except OCRError as exc:
                st.error(f"Error al procesar el documento: {exc}")
                return
            except Exception as exc:  # noqa: BLE001 - surfaced to the user
                logger.exception("Unexpected failure extracting %s", uploaded_file.name)
                st.error(f"Error inesperado: {exc}")
                return

        stem = safe_stem(uploaded_file.name)
        payloads = persist_results(result, stem)

        st.markdown("### Texto Extraido")
        st.text_area("Contenido", result["full_text"], height=300)

        render_download_buttons(payloads, key="extract")
        st.success(
            f"Texto extraido correctamente. "
            f"{result['total_lines']} detecciones encontradas."
        )


def render_visualize_task() -> None:
    """Render the bounding box visualization task."""
    st.subheader("Visualizar Cajas Delimitadoras")

    uploaded_file = st.file_uploader(
        "Sube una imagen o PDF", type=UPLOAD_TYPES, key="visualize_boxes"
    )
    if not uploaded_file:
        return

    if not st.button("Procesar Imagen", type="primary"):
        return

    with st.spinner("Procesando documento..."):
        stem = safe_stem(uploaded_file.name)
        try:
            with staged_upload(uploaded_file) as staged:
                outputs = OCREngine.visualize_document(
                    str(staged), str(settings.output_dir), stem
                )
        except OCRError as exc:
            st.error(f"Error al procesar el documento: {exc}")
            return
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            logger.exception("Unexpected failure visualizing %s", uploaded_file.name)
            st.error(f"Error inesperado: {exc}")
            return

    if OCREngine.is_pdf(uploaded_file.name):
        for page_number, output_path in enumerate(outputs, start=1):
            st.image(
                output_path, caption=f"Pagina {page_number}", use_container_width=True
            )
    else:
        col_original, col_annotated = st.columns(2)
        with col_original:
            st.image(uploaded_file, caption="Original", use_container_width=True)
        with col_annotated:
            st.image(outputs[0], caption="Con Cajas", use_container_width=True)

    for output_path in outputs:
        name = Path(output_path).name
        st.download_button(
            label=f"Descargar {name}",
            data=Path(output_path).read_bytes(),
            file_name=name,
            mime="image/png",
            key=f"download_{name}",
        )

    st.success(f"Documento procesado correctamente ({len(outputs)} imagen/es).")


def render_batch_task() -> None:
    """Render the batch processing task."""
    st.subheader("Procesar Multiples Imagenes o PDFs")

    uploaded_files = st.file_uploader(
        "Sube multiples imagenes o PDFs",
        type=UPLOAD_TYPES,
        accept_multiple_files=True,
        key="multiple_images",
    )
    if not uploaded_files:
        return

    if not st.button("Procesar Todas", type="primary"):
        return

    rows: List[Dict[str, Any]] = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for index, uploaded_file in enumerate(uploaded_files, start=1):
        status_text.text(
            f"Procesando {index}/{len(uploaded_files)}: {uploaded_file.name}"
        )

        try:
            with staged_upload(uploaded_file) as staged:
                result = OCREngine.extract_document(str(staged))

            persist_results(result, safe_stem(uploaded_file.name))
            rows.append(
                {
                    "Filename": uploaded_file.name,
                    "Lines": result["total_lines"],
                    "Pages": result.get("total_pages", 1),
                    "Text": preview_text(result["full_text"]),
                }
            )
        except Exception as exc:  # noqa: BLE001 - one failure must not stop the batch
            logger.exception("Failed to process %s", uploaded_file.name)
            st.warning(f"Error procesando {uploaded_file.name}: {exc}")
            rows.append(
                {
                    "Filename": uploaded_file.name,
                    "Lines": 0,
                    "Pages": 0,
                    "Text": f"Error: {exc}",
                }
            )

        progress_bar.progress(index / len(uploaded_files))

    status_text.text("Procesamiento completado.")

    dataframe = pd.DataFrame(rows)
    st.dataframe(dataframe, use_container_width=True)

    st.download_button(
        label="Descargar CSV",
        data=dataframe.to_csv(index=False),
        file_name="ocr_results.csv",
        mime="text/csv",
    )

    succeeded = sum(1 for row in rows if not str(row["Text"]).startswith("Error:"))
    st.success(f"Procesados {succeeded}/{len(uploaded_files)} archivos correctamente.")


# ----------------------------------------------------------------------
# Results tab
# ----------------------------------------------------------------------


def render_results_tab() -> None:
    """List and preview the artifacts stored in the output directory."""
    st.header("Resultados Guardados")

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(
        (path for path in settings.output_dir.iterdir() if path.is_file()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not files:
        st.info("No hay resultados guardados aun. Procesa algunas imagenes primero.")
        return

    for file_path in files:
        with st.expander(file_path.name):
            render_result_preview(file_path)


def render_result_preview(file_path: Path) -> None:
    """Render a single stored artifact according to its extension."""
    suffix = file_path.suffix.lower()

    if suffix == ".json":
        st.json(json.loads(file_path.read_text(encoding="utf-8")))
    elif suffix in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        st.image(str(file_path), use_container_width=True)
    elif suffix == ".md":
        st.markdown(file_path.read_text(encoding="utf-8"))
    elif suffix in {".txt", ".csv"}:
        st.text(file_path.read_text(encoding="utf-8"))
    else:
        st.caption("Vista previa no disponible para este formato.")

    st.download_button(
        label="Descargar",
        data=file_path.read_bytes(),
        file_name=file_path.name,
        key=f"saved_{file_path.name}",
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def main() -> None:
    """Run the Streamlit application."""
    st.set_page_config(
        page_title="OCR MVP - Tesseract",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    configure_logging()
    settings.output_dir.mkdir(parents=True, exist_ok=True)

    task = render_sidebar()
    process_tab, results_tab = st.tabs(["Procesar", "Resultados"])

    with process_tab:
        st.header("Procesamiento OCR")
        if task == TASK_EXTRACT:
            render_extract_task()
        elif task == TASK_VISUALIZE:
            render_visualize_task()
        elif task == TASK_BATCH:
            render_batch_task()

    with results_tab:
        render_results_tab()


if __name__ == "__main__":
    main()
