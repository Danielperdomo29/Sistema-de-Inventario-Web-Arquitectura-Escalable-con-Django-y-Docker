// Gestión de productos en formularios de compras

let details = [];

// Evento para actualizar el precio cuando se selecciona un producto
document.addEventListener('DOMContentLoaded', function() {
    const productSelect = document.getElementById('productSelect');
    if (productSelect) {
        productSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const price = selectedOption.dataset.price || 0;
            document.getElementById('priceInput').value = price;
        });
    }

    const addProductBtn = document.getElementById('addProductBtn');
    if (addProductBtn) {
        addProductBtn.addEventListener('click', addProduct);
    }

    const purchaseForm = document.getElementById('purchaseForm');
    if (purchaseForm) {
        purchaseForm.addEventListener('submit', function(e) {
            // Verificar si está en modo "sin productos"
            const noProductsMode = document.getElementById('no_products_mode');
            const isNoProductsMode = noProductsMode && noProductsMode.checked;
            
            // Solo validar productos si NO está en modo "sin productos"
            if (!isNoProductsMode && details.length === 0) {
                e.preventDefault();
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'warning',
                        title: 'Productos requeridos',
                        text: 'Debe agregar al menos un producto a la compra',
                        confirmButtonText: 'Entendido'
                    });
                } else {
                    alert('Debe agregar al menos un producto');
                }
            }
        });
    }
});

function addProduct() {
    // Validar que se haya seleccionado un proveedor primero
    const supplierSelect = document.getElementById('supplierSelect');
    if (supplierSelect && !supplierSelect.value) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'warning',
                title: 'Proveedor requerido',
                text: 'Debe seleccionar un proveedor antes de agregar productos',
                confirmButtonText: 'Entendido'
            });
        } else {
            alert('Debe seleccionar un proveedor antes de agregar productos');
        }
        return;
    }
    
    const productSelect = document.getElementById('productSelect');
    const productId = productSelect.value;
    const productName = productSelect.options[productSelect.selectedIndex].text;
    const quantity = parseInt(document.getElementById('quantityInput').value);
    const price = parseFloat(document.getElementById('priceInput').value);

    if (!productId || quantity <= 0 || price < 0) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                icon: 'error',
                title: 'Datos incompletos',
                text: 'Por favor complete todos los campos correctamente',
                confirmButtonText: 'Entendido'
            });
        } else {
            alert('Por favor complete todos los campos correctamente');
        }
        return;
    }

    const subtotal = quantity * price;

    details.push({
        producto_id: productId,
        producto_nombre: productName,
        cantidad: quantity,
        cantidad_original: quantity, // Guardar para poder restaurar
        precio_unitario: price,
        subtotal: subtotal,
        cancelado: false // Estado de cancelación
    });

    updateTable();

    // Reset
    productSelect.value = '';
    document.getElementById('quantityInput').value = 1;
    document.getElementById('priceInput').value = 0;
}

function updateTable() {
    const tbody = document.getElementById('productsTableBody');
    const emptyRow = document.getElementById('emptyRow');

    if (details.length === 0) {
        // Solo intentar mostrar emptyRow si existe
        if (emptyRow) {
            emptyRow.style.display = '';
        }
        const totalAmount = document.getElementById('totalAmount');
        const totalInput = document.getElementById('totalInput');
        if (totalAmount) totalAmount.textContent = 'S/ 0.00';
        if (totalInput) totalInput.value = 0;
        return;
    }

    // Solo intentar ocultar emptyRow si existe
    if (emptyRow) {
        emptyRow.style.display = 'none';
    }
    
    if (tbody) {
        tbody.innerHTML = '';

        let total = 0;
        details.forEach((detail, index) => {
            // Solo sumar productos NO cancelados
            if (!detail.cancelado) {
                total += detail.subtotal;
            }
            
            // Determinar estilo y botones según estado
            const rowClass = detail.cancelado ? 'product-cancelled' : '';
            const badge = detail.cancelado ? '<span class="cancelled-badge">CANCELADO</span>' : '';
            const actionButton = detail.cancelado 
                ? `<button type="button" class="btn-restore" onclick="restoreProduct(${index})">
                       <i class="fas fa-undo"></i> Restaurar
                   </button>`
                : `<button type="button" class="btn btn-sm btn-danger" onclick="removeProduct(${index})">
                       <i class="fas fa-trash"></i>
                   </button>`;
            
            const row = `
                <tr class="${rowClass}">
                    <td>${detail.producto_nombre}${badge}</td>
                    <td>${detail.cantidad}</td>
                    <td>S/ ${detail.precio_unitario.toFixed(2)}</td>
                    <td>S/ ${detail.subtotal.toFixed(2)}</td>
                    <td>
                        ${actionButton}
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });

        const totalAmount = document.getElementById('totalAmount');
        const totalInput = document.getElementById('totalInput');
        const detailsInput = document.getElementById('detailsInput');
        
        if (totalAmount) totalAmount.textContent = `S/ ${total.toFixed(2)}`;
        if (totalInput) totalInput.value = total.toFixed(2);
        if (detailsInput) detailsInput.value = JSON.stringify(details);
    }
}

function removeProduct(index) {
    // Innovación: Marcar como CANCELADO en lugar de eliminar
    // Esto mantiene trazabilidad del cambio
    
    if (details[index]) {
        // Marcar producto como cancelado
        details[index].cancelado = true;
        details[index].cantidad = 0; // Cantidad a 0 para no afectar total
        details[index].subtotal = 0;
    }
    
    updateTable();
}

// Para el formulario de edición, cargar detalles existentes
function loadExistingDetails(existingDetails) {
    details = existingDetails;
    updateTable();
}

// CSS dinámico para productos cancelados
const style = document.createElement('style');
style.textContent = `
    .product-cancelled {
        background-color: #fee !important;
        text-decoration: line-through;
        opacity: 0.6;
        transition: all 0.3s ease;
    }
    .product-cancelled td {
        color: #999 !important;
    }
    .product-cancelled .cancelled-badge {
        display: inline-block;
        background: #dc3545;
        color: white;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 0.75rem;
        font-weight: bold;
        margin-left: 8px;
    }
    .btn-restore {
        background-color: #28a745;
        color: white;
        padding: 4px 8px;
        border: none;
        border-radius: 3px;
        cursor: pointer;
        font-size: 0.75rem;
    }
    .btn-restore:hover {
        background-color: #218838;
    }
`;
document.head.appendChild(style);

// Función para restaurar un producto cancelado
function restoreProduct(index) {
    if (details[index] && details[index].cancelado) {
        details[index].cancelado = false;
        // Restaurar cantidad original (guardada en otra propiedad)
        details[index].cantidad = details[index].cantidad_original || 1;
        details[index].subtotal = details[index].cantidad * details[index].precio_unitario;
    }
    updateTable();
}
