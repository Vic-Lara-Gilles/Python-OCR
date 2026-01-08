// Extract Text Form Handler
document.getElementById('extractForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const button = e.target.querySelector('button');
  const originalText = button.textContent;
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Procesando...';

  const formData = new FormData(e.target);
  const resultDiv = document.getElementById('result');

  try {
    const response = await fetch('/api/extract', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.error) {
      resultDiv.innerHTML = `<p class="error">${data.error}</p>`;
    } else {
      resultDiv.innerHTML = `
                <h3>Resultado:</h3>
                <p><strong>Archivo:</strong> ${data.filename}</p>
                <p><strong>Lineas detectadas:</strong> ${data.total_lines}</p>
                <p><strong>Procesado:</strong> ${new Date(data.processed_at).toLocaleString('es-ES')}</p>
                <h4>Texto extraido:</h4>
                <pre>${escapeHtml(data.full_text)}</pre>
            `;
    }
  } catch (error) {
    resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
});

// Visualize Boxes Form Handler
document.getElementById('visualizeForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const button = e.target.querySelector('button');
  const originalText = button.textContent;
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Procesando...';

  const formData = new FormData(e.target);
  const resultDiv = document.getElementById('visualResult');

  try {
    const response = await fetch('/api/visualize', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.error) {
      resultDiv.innerHTML = `<p class="error">${data.error}</p>`;
    } else {
      resultDiv.innerHTML = `
                <h3>Imagen Procesada:</h3>
                <p><strong>Archivo original:</strong> ${data.filename}</p>
                <p><strong>Cajas detectadas:</strong> ${data.total_boxes}</p>
                <p>
                    <a href="${data.download_url}" download class="btn-download">Descargar Imagen Anotada</a>
                </p>
            `;
    }
  } catch (error) {
    resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
});

// Batch Process Form Handler
document.getElementById('batchForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const button = e.target.querySelector('button');
  const originalText = button.textContent;
  button.disabled = true;
  button.innerHTML = '<span class="spinner"></span>Procesando...';

  const formData = new FormData(e.target);
  const resultDiv = document.getElementById('batchResult');

  try {
    const response = await fetch('/api/batch', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (data.error) {
      resultDiv.innerHTML = `<p class="error">${data.error}</p>`;
    } else {
      let resultsHTML = `
                <h3>Resultados del Lote:</h3>
                <div class="batch-summary">
                    <p><strong>Total archivos:</strong> ${data.total_files}</p>
                    <p><strong>Exitosos:</strong> ${data.success_count}</p>
                    <p><strong>Fallidos:</strong> ${data.failure_count}</p>
                    <p><strong>Tiempo de procesamiento:</strong> ${data.processing_time}</p>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Archivo</th>
                            <th>Lineas</th>
                            <th>Estado</th>
                            <th>Vista Previa</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

      data.results.forEach(result => {
        const statusClass = result.success ? 'success' : 'error';
        const statusText = result.success ? 'OK' : 'Error';
        const preview = result.success ? escapeHtml(result.preview) : escapeHtml(result.error);

        resultsHTML += `
                    <tr class="${statusClass}">
                        <td>${escapeHtml(result.filename)}</td>
                        <td>${result.lines || '-'}</td>
                        <td>${statusText}</td>
                        <td>${preview}</td>
                    </tr>
                `;
      });

      resultsHTML += `
                    </tbody>
                </table>
            `;

      resultDiv.innerHTML = resultsHTML;
    }
  } catch (error) {
    resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
});

// Utility function to escape HTML
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
