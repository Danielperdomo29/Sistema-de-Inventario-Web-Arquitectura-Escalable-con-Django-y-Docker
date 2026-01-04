// Gestión de productos en formularios de ventas y compras

class ProductManager {
    constructor(products, existingProducts = []) {
        this.products = products;
        this.selectedProducts = existingProducts;
        this.defaultIvaTasa = 19.00; // Default IVA 19%
    }

    calculateIVA(precioUnitario, cantidad, ivaTasa = null) {
        const tasa = ivaTasa !== null ? ivaTasa : this.defaultIvaTasa;
        const subtotalSinIva = precioUnitario * cantidad;
        const ivaValor = subtotalSinIva * (tasa / 100);
        const subtotalConIva = subtotalSinIva + ivaValor;
        
        return {
            subtotal_sin_iva: subtotalSinIva,
            iva_valor: ivaValor,
            subtotal: subtotalConIva,
            iva_tasa: tasa
        };
    }

    addProduct(productId, quantity) {
        if (!productId || quantity <= 0) {
            Swal.fire({
                icon: 'warning',
                title: 'Datos Inválidos',
                text: 'Seleccione un producto y cantidad válida',
                confirmButtonColor: '#3085d6'
            });
            return;
        }

        const product = this.products.find(p => p.id === productId);
        if (!product) return;

        const existing = this.selectedProducts.find(p => p.producto_id === productId);
        if (existing) {
            existing.cantidad += quantity;
            // Recalcular IVA
            const calculo = this.calculateIVA(existing.precio_unitario, existing.cantidad, existing.iva_tasa);
            Object.assign(existing, calculo);
        } else {
            const calculo = this.calculateIVA(product.precio, quantity);
            this.selectedProducts.push({
                producto_id: productId,
                nombre: product.nombre,
                precio_unitario: product.precio,
                cantidad: quantity,
                ...calculo
            });
        }

        this.render();
    }

    removeProduct(index) {
        this.selectedProducts.splice(index, 1);
        this.render();
    }

    render() {
        const tbody = document.getElementById('productsBody');
        const table = document.getElementById('productsTable');

        if (this.selectedProducts.length === 0 && table) {
            table.style.display = 'none';
            return;
        }

        if (table) {
            table.style.display = 'table';
        }

        tbody.innerHTML = this.selectedProducts.map((p, i) => `
            <tr>
                <td>${p.nombre}</td>
                <td>$${p.precio_unitario.toFixed(2)}</td>
                <td>${p.cantidad}</td>
                <td>$${(p.subtotal_sin_iva || 0).toFixed(2)}</td>
                <td>${(p.iva_tasa || this.defaultIvaTasa).toFixed(0)}%</td>
                <td>$${(p.iva_valor || 0).toFixed(2)}</td>
                <td><b>$${p.subtotal.toFixed(2)}</b></td>
                <td><button type="button" class="btn btn-danger" onclick="manager.removeProduct(${i})">X</button></td>
            </tr>
        `).join('');

        // Calcular totales globales
        const totales = this.selectedProducts.reduce((acc, p) => {
            acc.subtotal += (p.subtotal_sin_iva || 0);
            acc.iva += (p.iva_valor || 0);
            acc.total += p.subtotal;
            return acc;
        }, { subtotal: 0, iva: 0, total: 0 });

        // Actualizar display de totales
        // Actualizar display de totales
        if (document.getElementById('footer-subtotal')) {
            document.getElementById('footer-subtotal').textContent = `$${totales.subtotal.toFixed(2)}`;
        }
        if (document.getElementById('footer-iva')) {
            document.getElementById('footer-iva').textContent = `$${totales.iva.toFixed(2)}`;
        }
        if (document.getElementById('footer-total')) {
            document.getElementById('footer-total').textContent = `$${totales.total.toFixed(2)}`;
        }
    }

    getProducts() {
        return this.selectedProducts;
    }
}

// Instancia global del manager (se inicializará desde la vista)
let manager = null;

// Función para agregar producto (llamada desde el botón)
function addProduct() {
    const select = document.getElementById('productSelect');
    const quantity = parseInt(document.getElementById('quantityInput').value);
    const productId = parseInt(select.value);

    manager.addProduct(productId, quantity);

    select.value = '';
    document.getElementById('quantityInput').value = 1;
}

// Inicialización del formulario
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('saleForm') || document.getElementById('purchaseForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            if (manager.selectedProducts.length === 0) {
                e.preventDefault();
                e.stopImmediatePropagation(); // Prevenir que form-validator también intercepte
                
                // Resetear botón de submit si quedó en estado de procesando
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    const originalIcon = submitBtn.querySelector('i')?.className || 'fas fa-save';
                    const originalText = submitBtn.dataset.originalText || 'Guardar Venta';
                    submitBtn.innerHTML = `<i class="${originalIcon}"></i> ${originalText}`;
                }
                
                Swal.fire({
                    icon: 'warning',
                    title: 'Sin Productos',
                    text: 'Debe agregar al menos un producto',
                    confirmButtonColor: '#3085d6'
                });
                return false;
            }
            document.getElementById('details').value = JSON.stringify(manager.selectedProducts);
        }, true); // Usar fase de captura para ejecutar primero

        // Si hay productos existentes, renderizarlos
        if (manager && manager.selectedProducts.length > 0) {
            manager.render();
        }
    }
});
