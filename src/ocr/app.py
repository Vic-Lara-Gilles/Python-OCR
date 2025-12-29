"""Streamlit application for OCR system with PaddleOCR."""

import os
import json
from pathlib import Path
import streamlit as st
import pandas as pd
from ocr.engine import OCREngine


# Page configuration
st.set_page_config(
    page_title="OCR MVP - PaddleOCR",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Create output directory
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Sidebar
with st.sidebar:
    st.title("OCR MVP")
    st.markdown("---")

    task = st.radio(
        "Selecciona una tarea:",
        ["Extraer Texto", "Visualizar Cajas", "Multiples Imagenes"],
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
    st.markdown("### Formatos Soportados")
    st.markdown("**Imagenes:** JPG, JPEG, PNG, WEBP")
    st.markdown("**Documentos:** PDF")

# Main content
tab1, tab2 = st.tabs(["Procesar", "Resultados"])

with tab1:
    st.header("Procesamiento OCR")

    # Task 1: Extract Text
    if task == "Extraer Texto":
        st.subheader("Extraer Texto de Imagen o PDF")

        uploaded_file = st.file_uploader(
            "Sube una imagen o PDF",
            type=["jpg", "jpeg", "png", "webp", "pdf"],
            key="extract_text",
        )

        if uploaded_file:
            col1, col2 = st.columns(2)

            with col1:
                if uploaded_file.name.lower().endswith(".pdf"):
                    st.info(f"Archivo PDF: {uploaded_file.name}")
                    st.markdown("**Tipo:** PDF")
                else:
                    st.image(
                        uploaded_file,
                        caption="Imagen Original",
                        use_container_width=True,
                    )

            with col2:
                if st.button("Extraer Texto", type="primary", use_container_width=True):
                    with st.spinner(
                        "Ejecutando OCR... Esto puede tardar unos segundos"
                    ):
                        # Save uploaded file temporarily
                        temp_path = f"temp_{uploaded_file.name}"
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        try:
                            # Extract text and boxes (handle PDF or image)
                            if uploaded_file.name.lower().endswith(".pdf"):
                                result = OCREngine.extract_text_from_pdf(temp_path)
                            else:
                                result = OCREngine.extract_text_and_boxes(temp_path)

                            # Generate markdown and plain text
                            markdown_text = OCREngine.generate_markdown(result)
                            plain_text = OCREngine.generate_plain_text(result)

                            # Display extracted text
                            st.markdown("### Texto Extraido")
                            st.text_area("Contenido", plain_text, height=300)

                            # Save results to files
                            base_name = os.path.splitext(uploaded_file.name)[0]

                            # Save JSON
                            json_filename = f"ocr_{base_name}.json"
                            json_path = OUTPUT_DIR / json_filename
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump(result, f, ensure_ascii=False, indent=2)

                            # Save Markdown
                            md_filename = f"ocr_{base_name}.md"
                            md_path = OUTPUT_DIR / md_filename
                            with open(md_path, "w", encoding="utf-8") as f:
                                f.write(markdown_text)

                            # Save Plain Text
                            txt_filename = f"ocr_{base_name}.txt"
                            txt_path = OUTPUT_DIR / txt_filename
                            with open(txt_path, "w", encoding="utf-8") as f:
                                f.write(plain_text)

                            # Download buttons
                            col_a, col_b, col_c = st.columns(3)

                            with col_a:
                                st.download_button(
                                    label="Descargar TXT",
                                    data=plain_text,
                                    file_name=txt_filename,
                                    mime="text/plain",
                                    use_container_width=True,
                                )

                            with col_b:
                                st.download_button(
                                    label="Descargar Markdown",
                                    data=markdown_text,
                                    file_name=md_filename,
                                    mime="text/markdown",
                                    use_container_width=True,
                                )

                            with col_c:
                                st.download_button(
                                    label="Descargar JSON",
                                    data=json.dumps(
                                        result, ensure_ascii=False, indent=2
                                    ),
                                    file_name=json_filename,
                                    mime="application/json",
                                    use_container_width=True,
                                )

                            st.success(
                                f"Texto extraido correctamente. {result['total_lines']} lineas detectadas."
                            )

                        except Exception as e:
                            st.error(f"Error al procesar la imagen: {str(e)}")

                        finally:
                            # Clean up temp file
                            if os.path.exists(temp_path):
                                os.remove(temp_path)

    # Task 2: Visualize Boxes
    elif task == "Visualizar Cajas":
        st.subheader("Visualizar Cajas Delimitadoras")

        uploaded_file = st.file_uploader(
            "Sube una imagen o PDF",
            type=["jpg", "jpeg", "png", "webp", "pdf"],
            key="visualize_boxes",
        )

        if uploaded_file:
            if st.button("Procesar Imagen", type="primary"):
                with st.spinner("Procesando imagen..."):
                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    try:
                        # Generate output path
                        output_filename = f"boxes_{uploaded_file.name}"
                        output_path = OUTPUT_DIR / output_filename

                        # Visualize boxes
                        OCREngine.visualize_boxes(temp_path, str(output_path))

                        # Display images side by side
                        col1, col2 = st.columns(2)

                        with col1:
                            st.image(
                                uploaded_file,
                                caption="Original",
                                use_container_width=True,
                            )

                        with col2:
                            st.image(
                                str(output_path),
                                caption="Con Cajas",
                                use_container_width=True,
                            )

                        # Download button
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label="Descargar Imagen Anotada",
                                data=f.read(),
                                file_name=output_filename,
                                mime="image/png",
                            )

                        st.success("Imagen procesada correctamente.")

                    except Exception as e:
                        st.error(f"Error al procesar la imagen: {str(e)}")

                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

    # Task 3: Multiple Images
    elif task == "Multiples Imagenes":
        st.subheader("Procesar Multiples Imagenes o PDFs")

        uploaded_files = st.file_uploader(
            "Sube multiples imagenes o PDFs",
            type=["jpg", "jpeg", "png", "webp", "pdf"],
            accept_multiple_files=True,
            key="multiple_images",
        )

        if uploaded_files:
            if st.button("Procesar Todas", type="primary"):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()

                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(
                        f"Procesado {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}"
                    )

                    # Save uploaded file temporarily
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    try:
                        # Extract text and boxes (handle PDF or image)
                        if uploaded_file.name.lower().endswith(".pdf"):
                            result = OCREngine.extract_text_from_pdf(temp_path)
                        else:
                            result = OCREngine.extract_text_and_boxes(temp_path)

                        results.append(
                            {
                                "Filename": uploaded_file.name,
                                "Lines": result["total_lines"],
                                "Pages": result.get("total_pages", 1),
                                "Text": (
                                    result["full_text"][:100] + "..."
                                    if len(result["full_text"]) > 100
                                    else result["full_text"]
                                ),
                            }
                        )

                        # Save individual result
                        base_name = os.path.splitext(uploaded_file.name)[0]

                        # Save JSON
                        json_filename = f"ocr_{base_name}.json"
                        json_path = OUTPUT_DIR / json_filename
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)

                        # Save Markdown
                        markdown_text = OCREngine.generate_markdown(result)
                        md_filename = f"ocr_{base_name}.md"
                        md_path = OUTPUT_DIR / md_filename
                        with open(md_path, "w", encoding="utf-8") as f:
                            f.write(markdown_text)

                        # Save Plain Text
                        plain_text = OCREngine.generate_plain_text(result)
                        txt_filename = f"ocr_{base_name}.txt"
                        txt_path = OUTPUT_DIR / txt_filename
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write(plain_text)

                    except Exception as e:
                        st.warning(f"Error procesando {uploaded_file.name}: {str(e)}")
                        results.append(
                            {
                                "Filename": uploaded_file.name,
                                "Lines": 0,
                                "Pages": 0,
                                "Text": f"Error: {str(e)}",
                            }
                        )

                    finally:
                        # Clean up temp file
                        if os.path.exists(temp_path):
                            os.remove(temp_path)

                    # Update progress
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                status_text.text("Procesamiento completado.")

                # Display results DataFrame
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)

                # Download CSV button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name="ocr_results.csv",
                    mime="text/csv",
                )

                st.success(f"Procesadas {len(uploaded_files)} imagenes correctamente.")

with tab2:
    st.header("Resultados Guardados")

    if not any(OUTPUT_DIR.iterdir()):
        st.info("No hay resultados guardados aun. Procesa algunas imagenes primero.")
    else:
        # List all files in outputs directory
        files = sorted(
            OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
        )

        for file_path in files:
            with st.expander(f"{file_path.name}"):
                if file_path.suffix == ".json":
                    # Display JSON files
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    st.json(data)
                elif file_path.suffix in [".png", ".jpg", ".jpeg", ".webp"]:
                    # Display image files
                    st.image(str(file_path), use_container_width=True)
