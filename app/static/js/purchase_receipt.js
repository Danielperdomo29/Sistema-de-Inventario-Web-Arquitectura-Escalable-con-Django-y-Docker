/**
 * Manejo de facturas con OCR para compras
 * Sistema dual: Manual vs Automático con extracción OCR
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const modeRadios = document.querySelectorAll('input[name="entry_mode"]');
    const manualPanel = document.getElementById('panel_manual');
    const autoPanel = document.getElementById('panel_auto');
    const receiptFileInput = document.getElementById('receipt_file');
    const btnExtract = document.getElementById('btn_extract');
    const extractedTotalInput = document.getElementById('extracted_total');
    const extractionResult = document.getElementById('extraction_result');
    const confidenceBar = document.getElementById('confidence_bar');
    const confidenceBadge = document.getElementById('confidence_badge');
    const filePreview = document.getElementById('file_preview');
    
    // ===== CAMBIO DE MODO =====
    if (modeRadios.length > 0) {
        modeRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'manual') {
                    if (manualPanel) manualPanel.style.display = 'block';
                    if (autoPanel) autoPanel.style.display = 'none';
                } else {
                    if (manualPanel) manualPanel.style.display = 'none';
                    if (autoPanel) autoPanel.style.display = 'block';
                }
            });
        });
    }
    
    // ===== PREVIEW DE ARCHIVO =====
    if (receiptFileInput) {
        receiptFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            // Limpiar preview anterior
            if (filePreview) {
                filePreview.innerHTML = '';
            }
            
            // Limpiar resultado anterior
            if (extractionResult) {
                extractionResult.style.display = 'none';
            }
            if (extractedTotalInput) {
                extractedTotalInput.value = '';
            }
            
            if (!file) {
                if (btnExtract) btnExtract.disabled = true;
                return;
            }
            
            // Validar tamaño (5MB)
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                showAlert('El archivo es demasiado grande. Máximo 5MB.', 'error');
                this.value = '';
                if (btnExtract) btnExtract.disabled = true;
                return;
            }
            
            // Validar tipo
            const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/bmp'];
            if (!allowedTypes.includes(file.type)) {
                showAlert('Tipo de archivo no permitido. Use PDF o imagen.', 'error');
                this.value = '';
                if (btnExtract) btnExtract.disabled = true;
                return;
            }
            
            // Habilitar botón de extracción
            if (btnExtract) btnExtract.disabled = false;
            
            // Mostrar preview
            if (filePreview) {
                const isPdf = file.type === 'application/pdf';
                const icon = isPdf ? 'fa-file-pdf text-danger' : 'fa-image text-primary';
                const sizeKB = (file.size / 1024).toFixed(1);
                
                filePreview.innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas ${icon} fa-2x"></i>
                        <div class="mt-2">
                            <strong>${file.name}</strong><br>
                            <small>${sizeKB} KB</small>
                        </div>
                    </div>
                `;
            }
        });
    }
    
    // ===== EXTRACCIÓN OCR =====
    if (btnExtract) {
        btnExtract.addEventListener('click', async function() {
            const file = receiptFileInput ? receiptFileInput.files[0] : null;
            
            if (!file) {
                showAlert('Por favor, selecciona un archivo primero.', 'warning');
                return;
            }
            
            // Mostrar loading
            const originalText = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando OCR...';
            
            // Preparar FormData
            const formData = new FormData();
            formData.append('receipt', file);
            
            try {
                const response = await fetch('/api/purchases/extract-total/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Mostrar resultado exitoso
                    if (extractedTotalInput) {
                        extractedTotalInput.value = result.total;
                    }
                    
                    // Auto-completar campos adicionales SI se extrajeron
                    if (result.invoice_number) {
                        const invoiceInput = document.querySelector('input[name="numero_factura"]');
                        if (invoiceInput && !invoiceInput.value) {
                            invoiceInput.value = result.invoice_number;
                            invoiceInput.style.background = '#fffacd'; // Highlight amarillo
                        }
                    }
                    
                    if (result.date) {
                        const dateInput = document.querySelector('input[name="fecha"]');
                        if (dateInput && !dateInput.value) {
                            dateInput.value = result.date;
                            dateInput.style.background = '#fffacd';
                        }
                    }
                    
                    // Mostrar confianza
                    const confidence = (result.confidence || 0) * 100;
                    if (confidenceBar) {
                        confidenceBar.style.width = `${confidence}%`;
                        confidenceBar.textContent = `${confidence.toFixed(0)}%`;
                        
                        // Color según confianza
                        confidenceBar.className = 'progress-bar';
                        if (confidence >= 80) {
                            confidenceBar.classList.add('bg-success');
                        } else if (confidence >= 50) {
                            confidenceBar.classList.add('bg-warning');
                        } else {
                            confidenceBar.classList.add('bg-danger');
                        }
                    }
                    
                    if (confidenceBadge) {
                        let badgeHTML = '';
                        if (confidence >= 80) {
                            badgeHTML = '<span class="badge bg-success">Alta confianza</span>';
                        } else if (confidence >= 50) {
                            badgeHTML = '<span class="badge bg-warning">Confianza media</span>';
                        } else {
                            badgeHTML = '<span class="badge bg-danger">Baja confianza - Verificar</span>';
                        }
                        
                        // Agregar info de campos detectados
                        if (result.invoice_number) {
                            badgeHTML += ' <span class="badge bg-info">Factura detectada</span>';
                        }
                        if (result.date) {
                            badgeHTML += ' <span class="badge bg-info">Fecha detectada</span>';
                        }
                        
                        confidenceBadge.innerHTML = badgeHTML;
                    }
                    
                    // Mostrar resultado
                    if (extractionResult) {
                        extractionResult.style.display = 'block';
                    }
                    
                    // Mensaje de éxito con detalles
                    let successMessage = `Total extraído: $${result.total.toLocaleString()} (Confianza: ${confidence.toFixed(1)}%)`;
                    if (result.invoice_number || result.date) {
                        successMessage += '\\n';
                        if (result.invoice_number) successMessage += `\\n• N° Factura: ${result.invoice_number}`;
                        if (result.date) successMessage += `\\n• Fecha: ${result.date}`;
                    }
                    showAlert(successMessage, 'success');
                } else {
                    showAlert(`Error: ${result.error}`, 'error');
                    if (extractedTotalInput) {
                        extractedTotalInput.value = '';
                    }
                }
            } catch (error) {
                console.error('Error en extracción OCR:', error);
                showAlert('Error al procesar el archivo. Intenta nuevamente.', 'error');
            } finally {
                // Restaurar botón
                this.disabled = false;
                this.innerHTML = originalText;
            }
        });
    }
    
    // ===== UTILIDADES =====
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    function showAlert(message, type = 'info') {
        // Usar SweetAlert2 si está disponible
        if (typeof Swal !== 'undefined') {
            const icon = type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info';
            Swal.fire({
                icon: icon,
                title: type.charAt(0).toUpperCase() + type.slice(1),
                text: message,
                confirmButtonText: 'OK'
            });
        } else {
            // Fallback a alert nativo
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }
});
