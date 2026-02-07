/**
 * Manejo del modo "sin productos" en compras manuales
 */

// Esperar a que purchase-manager.js se cargue
document.addEventListener('DOMContentLoaded', function() {
    const noProductsCheckbox = document.getElementById('no_products_mode');
    const productsSection = document.getElementById('products_section_wrapper');
    const manualTotalDiv = document.getElementById('manual_total_input');
    const manualTotalInput = document.getElementById('manual_total');
    const detailsInput = document.getElementById('detailsInput');
    const totalInput = document.getElementById('totalInput');
    const purchaseForm = document.getElementById('purchaseForm');
    
    if (!noProductsCheckbox) return; // Solo correr si existe el checkbox
    
    // === PREVISUALIZACIÓN DE FACTURA MANUAL ===
    const receiptFileManual = document.getElementById('receipt_file_manual');
    const receiptPreviewManual = document.getElementById('receipt_preview_manual');
    const receiptPreviewContent = document.getElementById('receipt_preview_content_manual');
    
    if (receiptFileManual) {
        receiptFileManual.addEventListener('change', function(e) {
            const file = e.target.files[0];
            
            if (!file) {
                receiptPreviewManual.style.display = 'none';
                return;
            }
            
            // Validar tamaño (5MB)
            const maxSize = 5 * 1024 * 1024;
            if (file.size > maxSize) {
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'error',
                        title: 'Archivo muy grande',
                        text: 'El archivo no puede exceder 5MB'
                    });
                } else {
                    alert('El archivo es demasiado grande. Máximo 5MB.');
                }
                this.value = '';
                receiptPreviewManual.style.display = 'none';
                return;
            }
            
            // Mostrar previsualización
            const fileType = file.type;
            const reader = new FileReader();
            
            reader.onload = function(event) {
                receiptPreviewManual.style.display = 'block';
                
                if (fileType === 'application/pdf') {
                    // Para PDFs: Mostrar ícono y botón para abrir en nueva pestaña
                    // Evita problemas con CSP y X-Frame-Options
                    const blobUrl = URL.createObjectURL(file);
                    receiptPreviewContent.innerHTML = `
                        <div style="padding: 30px; background: #f8f9fa; border-radius: 4px;">
                            <i class="fas fa-file-pdf" style="font-size: 80px; color: #dc3545;"></i>
                            <h5 class="mt-3">${file.name}</h5>
                            <p class="text-muted">${(file.size / 1024).toFixed(1)} KB</p>
                            <button type="button" onclick="window.open('${blobUrl}', '_blank')" 
                                    class="btn btn-primary mt-2">
                                <i class="fas fa-external-link-alt"></i> Abrir PDF en Nueva Pestaña
                            </button>
                            <br>
                            <small class="text-muted mt-2">El PDF se abrirá en una nueva ventana</small>
                        </div>
                    `;
                } else if (fileType.startsWith('image/')) {
                    // Previsualización de imagen (funciona sin problemas)
                    receiptPreviewContent.innerHTML = `
                        <img src="${event.target.result}" 
                             style="max-width: 100%; max-height: 380px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <br>
                        <small class="text-muted">Imagen: ${file.name} (${(file.size / 1024).toFixed(1)} KB)</small>
                    `;
                } else {
                    receiptPreviewContent.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-file"></i> ${file.name} (${(file.size / 1024).toFixed(1)} KB)
                        </div>
                    `;
                }
            };
            
            reader.readAsDataURL(file);
        });
    }
    
    // Manejo del toggle
    noProductsCheckbox.addEventListener('change', function() {
        const isChecked = this.checked;
        
        if (isChecked) {
            // Ocultar sección de productos
            if (productsSection) productsSection.style.display = 'none';
            
            // Mostrar y habilitar input de total manual
            if (manualTotalDiv) manualTotalDiv.style.display = 'block';
            if (manualTotalInput) {
                manualTotalInput.disabled = false;
                manualTotalInput.required = true;
                manualTotalInput.focus();
            }
            
            // Clear product details
            if (detailsInput) detailsInput.value = '[]';
            if (totalInput) totalInput.value = '0';
            
        } else {
            // Mostrar sección de productos
            if (productsSection) productsSection.style.display = 'block';
            
            // Ocultar y deshabilitar input de total manual
            if (manualTotalDiv) manualTotalDiv.style.display = 'none';
            if (manualTotalInput) {
                manualTotalInput.disabled = true;
                manualTotalInput.required = false;
                manualTotalInput.value = '';
            }
            
            // Restaurar cálculo automático del total
            if (totalInput) totalInput.value = '0';
        }
    });
    
    // Sincronizar manual_total con totalInput
    if (manualTotalInput) {
        manualTotalInput.addEventListener('input', function() {
            if (!noProductsCheckbox.checked) return;
            if (totalInput) {
                totalInput.value = this.value || '0';
            }
        });
    }
    
    // Validación del formulario
    if (purchaseForm) {
        purchaseForm.addEventListener('submit', function(e) {
            // Validar proveedor primero
            const proveedorSelect = document.querySelector('select[name="proveedor_id"]');
            if (proveedorSelect && !proveedorSelect.value) {
                e.preventDefault();
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Proveedor requerido',
                        text: 'Debe seleccionar un proveedor para continuar'
                    });
                } else {
                    alert('Debe seleccionar un proveedor');
                }
                return false;
            }
            
            const noProductsMode = noProductsCheckbox.checked;
            
            if (noProductsMode) {
                const manualTotal = parseFloat(manualTotalInput.value);
                
                if (!manualTotal || manualTotal <= 0) {
                    e.preventDefault();
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'Debe ingresar un total válido para la compra'
                        });
                    } else {
                        alert('Debe ingresar un total válido para la compra');
                    }
                    return false;
                }
                
                // Asegurar que el total se establezca correctamente
                totalInput.value = manualTotal;
                
            } else {
                // Modo normal: verificar que haya productos
                const details = JSON.parse(detailsInput.value || '[]');
                if (details.length === 0) {
                    e.preventDefault();
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'error',
                            title: 'Error',
                            text: 'Debe agregar al menos un producto o marcar "Sin detalles de productos"'
                        });
                    } else {
                        alert('Debe agregar al menos un producto');
                    }
                    return false;
                }
            }
        });
    }
});

// Función global para limpiar preview manual
function clearManualReceiptPreview() {
    const fileInput = document.getElementById('receipt_file_manual');
    const preview = document.getElementById('receipt_preview_manual');
    
    if (fileInput) fileInput.value = '';
    if (preview) preview.style.display = 'none';
}
