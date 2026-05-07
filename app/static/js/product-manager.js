// app/static/js/product-manager.js (BORRAR TODO Y PEGAR ESTO)

/**
 * Utilidad para Redondeo Estricto (Equivalente a ROUND_HALF_UP de Python)
 * En Colombia, la DIAN requiere precisión de 2 decimales para el cálculo de impuestos.
 */
function roundDian(value) {
    return Math.round((value + Number.EPSILON) * 100) / 100;
}

class ProductManager {
    constructor(products, existingDetails = []) {
        this.allProducts = products;
        this.details = existingDetails;
    }

    addProduct() {
        const productId = document.getElementById('productSelect').value;
        const quantity = document.getElementById('quantityInput').value;

        if (!productId || !quantity || quantity <= 0) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', 'Por favor seleccione un producto y cantidad válida.', 'warning');
            } else {
                alert('Por favor seleccione un producto y cantidad válida.');
            }
            return;
        }

        const product = this.allProducts.find(p => p.id == productId);
        if (!product) return;

        const qty = parseInt(quantity, 10);

        // --- MOTOR TRIBUTARIO Y DE DESCUENTOS DIAN ---
        const precio = parseFloat(product.precio);
        const descuento_pct = parseFloat(product.descuento || 0.00);

        // MATEMÁTICA DIAN: El descuento afecta directamente la Base Gravable
        const subtotal_bruto = roundDian(precio * qty);
        const valor_descuento = roundDian(subtotal_bruto * (descuento_pct / 100));
        const base_gravable = roundDian(subtotal_bruto - valor_descuento);

        // Validación estricta del tipo de IVA
        let iva_pct = parseFloat(product.iva_porcentaje || 0);
        if (product.iva_tipo !== 'GRAVADO') {
            iva_pct = 0.00;
        }

        // El IVA se calcula SOBRE la base gravable ya descontada
        const iva_valor = roundDian(base_gravable * (iva_pct / 100));
        const total_linea = roundDian(base_gravable + iva_valor);

        const item = {
            producto_id: product.id,
            nombre: product.nombre,
            precio_unitario_base: precio,
            cantidad: qty,
            descuento_pct: descuento_pct,
            valor_descuento: valor_descuento,
            subtotal_base: base_gravable, // Esta es la Base Gravable por línea
            iva_tasa: iva_pct,
            iva_valor: iva_valor,
            subtotal: total_linea
        };

        this.details.push(item);
        this.render();

        // Limpiar input de cantidad
        document.getElementById('quantityInput').value = 1;
    }

    /**
     * Misión 2: Actualización Dinámica de Descuento
     * Permite al cajero modificar el % de descuento directamente en la tabla.
     */
    updateDiscount(index, newValue) {
        const item = this.details[index];
        if (!item) return;

        const new_pct = parseFloat(newValue) || 0;

        // MATEMÁTICA DIAN (Recalcular fila exacta)
        const subtotal_bruto = roundDian(item.precio_unitario_base * item.cantidad);
        const valor_descuento = roundDian(subtotal_bruto * (new_pct / 100));
        const base_gravable = roundDian(subtotal_bruto - valor_descuento);
        const iva_valor = roundDian(base_gravable * (item.iva_tasa / 100));

        // Actualizar el estado del ítem
        item.descuento_pct = new_pct;
        item.valor_descuento = valor_descuento;
        item.subtotal_base = base_gravable;
        item.iva_valor = iva_valor;
        item.subtotal = roundDian(base_gravable + iva_valor);

        // Refrescar los totales del panel de resumen sin re-renderizar toda la tabla
        // para evitar que el usuario pierda el foco del input mientras escribe.
        this.updateTotals();

        // Actualizar los valores en la fila del DOM manualmente para máximo rendimiento
        const row = document.getElementById(`row-${index}`);
        if (row) {
            row.querySelector('.col-subtotal').innerText = `$${item.subtotal_base.toLocaleString('es-CO', {minimumFractionDigits: 2})}`;
            row.querySelector('.col-total').innerText = `$${item.subtotal.toLocaleString('es-CO', {minimumFractionDigits: 2})}`;
        }
    }

    updateTotals() {
        let totalSubtotalBruto = 0;
        let totalDescuentos = 0;
        let totalBaseGravable = 0;
        let totalIva = 0;
        let totalGeneral = 0;

        this.details.forEach(item => {
            totalSubtotalBruto += (item.precio_unitario_base * item.cantidad);
            totalDescuentos += item.valor_descuento;
            totalBaseGravable += item.subtotal_base;
            totalIva += item.iva_valor;
            totalGeneral += item.subtotal;
        });

        // Formato de moneda colombiana
        const fmt = (val) => `$ ${val.toLocaleString('es-CO', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

        // --- ACTUALIZACIÓN DINÁMICA DEL RESUMEN VERTICAL (FASE 3) ---
        const elements = {
            'resumen-subtotal': fmt(totalSubtotalBruto),
            'resumen-descuentos': fmt(totalDescuentos),
            'resumen-base': fmt(totalBaseGravable), // Base gravable total
            'resumen-iva': fmt(totalIva),
            'resumen-total': fmt(totalGeneral)
        };

        // Inyectar valores en el DOM si los elementos existen
        for (const [id, val] of Object.entries(elements)) {
            const el = document.getElementById(id);
            if (el) el.innerText = val;
        }

        // Actualizar el input oculto para que Django procese el JSON exacto (Seguridad AppSec)
        const detailsInput = document.getElementById('details');
        if (detailsInput) {
            detailsInput.value = JSON.stringify(this.details);
        }
    }

    render() {
        const tbody = document.getElementById('productsBody');
        if (!tbody) return;

        tbody.innerHTML = '';

        this.details.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.id = `row-${index}`;

            // --- AJUSTE ESTRICTO DE ORDEN DE COLUMNAS PARA COINCIDIR CON THEAD (FASE 2.1) ---
            // ORDEN: Producto | Precio Base | Cant | Desc % | Subtotal (Base) | IVA % | Total | Acción
            tr.innerHTML = `
                <td><div class="font-bold">${item.nombre}</div></td>
                <td>$${item.precio_unitario_base.toLocaleString('es-CO', {minimumFractionDigits: 2})}</td>
                <td>${item.cantidad}</td>
                <td>
                    <div class="input-group input-group-sm" style="width: 80px; margin: 0 auto;">
                        <input type="number" min="0" max="100" step="0.1"
                               class="form-control text-center"
                               value="${item.descuento_pct}"
                               onchange="manager.updateDiscount(${index}, this.value)"
                               onkeyup="manager.updateDiscount(${index}, this.value)">
                    </div>
                </td>
                <td class="col-subtotal">$${item.subtotal_base.toLocaleString('es-CO', {minimumFractionDigits: 2})}</td>
                <td class="d-none d-md-table-cell">${item.iva_tasa}%</td>
                <td class="font-bold text-success col-total">$${item.subtotal.toLocaleString('es-CO', {minimumFractionDigits: 2})}</td>
                <td>
                    <button type="button" class="btn btn-danger btn-sm" onclick="manager.removeProduct(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Una vez renderizada la tabla, actualizamos el resumen general
        this.updateTotals();

        // Mostrar u ocultar la tabla dependiendo de si hay productos
        const table = document.getElementById('productsTable');
        if (table) {
            if (this.details.length > 0) {
                table.classList.remove('d-none');
            } else {
                table.classList.add('d-none');
            }
        }
    }

    removeProduct(index) {
        this.details.splice(index, 1);
        this.render();
    }
}

// Hacer global para onclick
let manager;

// Inicialización diferida (asegurar que el DOM y el objeto 'products' existen)
document.addEventListener('DOMContentLoaded', function() {
    if (typeof products !== 'undefined' && document.getElementById('saleForm')) {
        // La variable 'products' debe ser inyectada como JSON en el template por SaleView.create/edit
        manager = new ProductManager(products);

        // Soporte para edición: si existen detalles previos
        if (typeof existingDetails !== 'undefined' && existingDetails.length > 0) {
            manager.details = existingDetails;
            manager.render();
        }
    }
});

// Función puente para el botón "Agregar" en la UI
function addProduct() {
    if (manager) manager.addProduct();
}
