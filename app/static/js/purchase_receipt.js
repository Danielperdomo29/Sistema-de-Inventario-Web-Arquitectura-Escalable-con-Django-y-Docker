/**
 * OCR Receipt Extraction - Enhanced v3.0
 * Features: Image preview, drag-and-drop, supplier auto-match,
 *           editable extracted fields, OCR badges, confidence bar.
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===== DOM Elements =====
    const modeRadios = document.querySelectorAll('input[name="entry_mode"]');
    const manualPanel = document.getElementById('panel_manual');
    const autoPanel = document.getElementById('panel_auto');
    const receiptFileInput = document.getElementById('receipt_file');
    const btnExtract = document.getElementById('btn_extract');
    const extractedTotalInput = document.getElementById('extracted_total');
    const extractionResult = document.getElementById('extraction_result');
    const confidenceBar = document.getElementById('confidence_bar');
    const confidenceBadge = document.getElementById('confidence_badge');
    const uploadArea = document.getElementById('ocr_upload_area');
    const uploadPlaceholder = document.getElementById('upload_placeholder');
    const uploadFileInfo = document.getElementById('upload_file_info');
    const receiptImagePreview = document.getElementById('receipt_image_preview');
    const ocrRawText = document.getElementById('ocr_raw_text');

    // ===== Mode switching =====
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

    // ===== Drag and Drop =====
    if (uploadArea) {
        ['dragenter', 'dragover'].forEach(evt => {
            uploadArea.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.add('drag-over');
            });
        });
        ['dragleave', 'drop'].forEach(evt => {
            uploadArea.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.classList.remove('drag-over');
            });
        });
        uploadArea.addEventListener('drop', function(e) {
            const files = e.dataTransfer.files;
            if (files.length > 0 && receiptFileInput) {
                receiptFileInput.files = files;
                receiptFileInput.dispatchEvent(new Event('change'));
            }
        });
    }

    // ===== File Selection & Image Preview =====
    if (receiptFileInput) {
        receiptFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];

            // Reset state
            if (extractionResult) extractionResult.style.display = 'none';
            if (extractedTotalInput) extractedTotalInput.value = '';
            resetOcrBadges();

            if (!file) {
                if (btnExtract) btnExtract.disabled = true;
                if (uploadArea) uploadArea.classList.remove('has-file');
                if (uploadPlaceholder) uploadPlaceholder.style.display = 'block';
                if (uploadFileInfo) uploadFileInfo.style.display = 'none';
                return;
            }

            // Validate size (5MB)
            if (file.size > 5 * 1024 * 1024) {
                showAlert('El archivo es demasiado grande. Maximo 5MB.', 'error');
                this.value = '';
                if (btnExtract) btnExtract.disabled = true;
                return;
            }

            // Validate type
            const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/bmp'];
            if (!allowedTypes.includes(file.type)) {
                showAlert('Tipo de archivo no permitido. Use PDF o imagen.', 'error');
                this.value = '';
                if (btnExtract) btnExtract.disabled = true;
                return;
            }

            // Enable extract button
            if (btnExtract) btnExtract.disabled = false;

            // Update upload area
            if (uploadArea) uploadArea.classList.add('has-file');
            if (uploadPlaceholder) uploadPlaceholder.style.display = 'none';

            const isPdf = file.type === 'application/pdf';
            const icon = isPdf ? 'fa-file-pdf text-danger' : 'fa-image text-primary';
            const sizeKB = (file.size / 1024).toFixed(1);

            if (uploadFileInfo) {
                uploadFileInfo.style.display = 'block';
                uploadFileInfo.innerHTML = `
                    <div style="display:flex; align-items:center; gap:12px;">
                        <i class="fas ${icon}" style="font-size:2em;"></i>
                        <div>
                            <strong>${file.name}</strong><br>
                            <small style="color:#888;">${sizeKB} KB</small>
                        </div>
                        <button type="button" onclick="document.getElementById('receipt_file').value=''; document.getElementById('receipt_file').dispatchEvent(new Event('change'));"
                                style="margin-left:auto; background:none; border:none; color:#dc3545; cursor:pointer; font-size:1.2em;">
                            <i class="fas fa-times-circle"></i>
                        </button>
                    </div>
                `;
            }

            // Show image preview in the receipt thumb area
            if (receiptImagePreview && !isPdf) {
                const reader = new FileReader();
                reader.onload = function(ev) {
                    receiptImagePreview.innerHTML = `<img src="${ev.target.result}" alt="Factura">`;
                };
                reader.readAsDataURL(file);
            } else if (receiptImagePreview && isPdf) {
                receiptImagePreview.innerHTML = `
                    <i class="fas fa-file-pdf" style="font-size:3em; color:#dc3545;"></i>
                    <strong style="margin-top:8px;">${file.name}</strong>
                    <small style="color:#888;">Documento PDF</small>
                `;
            }
        });
    }

    // ===== OCR Extraction =====
    if (btnExtract) {
        btnExtract.addEventListener('click', async function() {
            const file = receiptFileInput ? receiptFileInput.files[0] : null;

            if (!file) {
                showAlert('Por favor, selecciona un archivo primero.', 'warning');
                return;
            }

            // Loading state
            const originalText = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando OCR...';

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
                    // Show extraction result panel
                    if (extractionResult) {
                        extractionResult.style.display = 'block';
                        extractionResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }

                    // --- Fill Total ---
                    if (extractedTotalInput && result.total) {
                        extractedTotalInput.value = result.total;
                        markOcrFilled('extracted_total', 'badge_total');
                    }

                    // --- Fill Invoice Number ---
                    if (result.invoice_number) {
                        const invoiceInput = document.getElementById('ocr_numero_factura');
                        if (invoiceInput) {
                            invoiceInput.value = result.invoice_number;
                            markOcrFilled('ocr_numero_factura', 'badge_invoice');
                        }
                    }

                    // --- Fill Date ---
                    if (result.date) {
                        const dateInput = document.getElementById('ocr_fecha');
                        if (dateInput) {
                            // Try to convert to YYYY-MM-DD for date input
                            const parsedDate = parseOcrDate(result.date);
                            if (parsedDate) {
                                dateInput.value = parsedDate;
                                markOcrFilled('ocr_fecha', 'badge_date');
                            }
                        }
                    }

                    // --- Supplier Auto-Match ---
                    const supplierSelect = document.getElementById('ocr_proveedor_select');
                    const supplierDisplay = document.getElementById('ocr_supplier_display');
                    const supplierText = document.getElementById('ocr_supplier_text');

                    if (result.supplier_name && supplierDisplay && supplierText) {
                        supplierDisplay.style.display = 'block';
                        supplierText.textContent = result.supplier_name;
                    }

                    if (result.supplier_match_id && supplierSelect) {
                        // Direct match from backend
                        supplierSelect.value = result.supplier_match_id;
                        markOcrFilled('ocr_proveedor_select', 'badge_supplier');
                    } else if (result.supplier_name && supplierSelect) {
                        // Frontend fallback: try to find matching option
                        const matched = matchSupplierInSelect(supplierSelect, result.supplier_name);
                        if (matched) {
                            markOcrFilled('ocr_proveedor_select', 'badge_supplier');
                        } else {
                            // No match found - select default "Proveedor General (OCR)"
                            const defaultOpt = supplierSelect.querySelector('option[data-default="true"]');
                            if (defaultOpt) {
                                supplierSelect.value = defaultOpt.value;
                                markOcrFilled('ocr_proveedor_select', 'badge_supplier');
                            }
                            // Show quick-create link
                            const actionsDiv = document.getElementById('ocr_supplier_actions');
                            const hintSpan = document.getElementById('ocr_supplier_hint');
                            if (actionsDiv) actionsDiv.style.display = 'block';
                            if (hintSpan) hintSpan.textContent = `"${result.supplier_name}" no encontrado en el sistema`;
                        }
                    } else if (supplierSelect) {
                        // No supplier name from OCR, select default
                        const defaultOpt = supplierSelect.querySelector('option[data-default="true"]');
                        if (defaultOpt) {
                            supplierSelect.value = defaultOpt.value;
                        }
                    }

                    // --- Confidence Bar ---
                    const confidence = (result.confidence || 0) * 100;
                    if (confidenceBar) {
                        confidenceBar.style.width = `${confidence}%`;
                        confidenceBar.textContent = `${confidence.toFixed(0)}%`;

                        if (confidence >= 80) {
                            confidenceBar.style.background = 'linear-gradient(90deg, #28a745, #20c997)';
                        } else if (confidence >= 50) {
                            confidenceBar.style.background = 'linear-gradient(90deg, #ffc107, #fd7e14)';
                        } else {
                            confidenceBar.style.background = 'linear-gradient(90deg, #dc3545, #fd7e14)';
                        }
                    }

                    // --- Confidence Badge ---
                    if (confidenceBadge) {
                        let badgeHTML = '';
                        if (confidence >= 80) {
                            badgeHTML = '<span class="badge" style="background:#28a745;color:#fff;padding:3px 8px;border-radius:4px;font-size:0.75em;">Alta confianza</span>';
                        } else if (confidence >= 50) {
                            badgeHTML = '<span class="badge" style="background:#ffc107;color:#333;padding:3px 8px;border-radius:4px;font-size:0.75em;">Confianza media</span>';
                        } else {
                            badgeHTML = '<span class="badge" style="background:#dc3545;color:#fff;padding:3px 8px;border-radius:4px;font-size:0.75em;">Baja - Verificar</span>';
                        }
                        confidenceBadge.innerHTML = badgeHTML;
                    }

                    // --- Raw Text ---
                    if (ocrRawText && result.extracted_text_preview) {
                        ocrRawText.textContent = result.extracted_text_preview;
                    }

                    showAlert(`Datos extraidos correctamente (Confianza: ${confidence.toFixed(0)}%)`, 'success');

                } else {
                    showAlert(`Error: ${result.error}`, 'error');
                    if (extractedTotalInput) extractedTotalInput.value = '';
                }
            } catch (error) {
                console.error('Error en extraccion OCR:', error);
                showAlert('Error al procesar el archivo. Intenta nuevamente.', 'error');
            } finally {
                this.disabled = false;
                this.innerHTML = originalText;
            }
        });
    }

    // ===== Helper Functions =====

    function markOcrFilled(inputId, badgeId) {
        const input = document.getElementById(inputId);
        const badge = document.getElementById(badgeId);
        if (input) input.classList.add('ocr-filled');
        if (badge) badge.style.display = 'inline-block';
    }

    function resetOcrBadges() {
        ['badge_total', 'badge_supplier', 'badge_invoice', 'badge_date'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.style.display = 'none';
        });
        document.querySelectorAll('.ocr-filled').forEach(el => {
            el.classList.remove('ocr-filled');
        });
    }

    function matchSupplierInSelect(selectEl, supplierName) {
        if (!supplierName || !selectEl) return false;
        const nameLower = supplierName.toLowerCase();
        let bestOption = null;
        let bestScore = 0;

        for (let i = 0; i < selectEl.options.length; i++) {
            const opt = selectEl.options[i];
            if (!opt.value) continue;
            const optText = opt.textContent.toLowerCase();

            // Substring match
            if (optText.includes(nameLower) || nameLower.includes(optText)) {
                const score = Math.min(optText.length, nameLower.length) / Math.max(optText.length, nameLower.length);
                if (score > bestScore) {
                    bestScore = score;
                    bestOption = opt;
                }
            }
        }

        if (bestOption && bestScore > 0.3) {
            selectEl.value = bestOption.value;
            return true;
        }
        return false;
    }

    function parseOcrDate(dateStr) {
        if (!dateStr) return null;
        // Already ISO format
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
        // DD/MM/YYYY or DD-MM-YYYY
        let match = dateStr.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})$/);
        if (match) {
            const day = match[1].padStart(2, '0');
            const month = match[2].padStart(2, '0');
            return `${match[3]}-${month}-${day}`;
        }
        // YYYY/MM/DD
        match = dateStr.match(/^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})$/);
        if (match) {
            return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
        }
        return null;
    }

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
        if (typeof Swal !== 'undefined') {
            const icon = type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info';
            Swal.fire({
                icon: icon,
                title: type === 'success' ? 'Exitoso' : type === 'error' ? 'Error' : 'Aviso',
                text: message,
                confirmButtonText: 'OK',
                timer: type === 'success' ? 3000 : undefined
            });
        } else {
            alert(`${type.toUpperCase()}: ${message}`);
        }
    }
});
