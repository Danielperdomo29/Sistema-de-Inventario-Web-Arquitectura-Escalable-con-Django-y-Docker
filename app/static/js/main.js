// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger-menu');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (hamburger && sidebar && overlay) {
        // Abrir sidebar
        hamburger.addEventListener('click', function() {
            sidebar.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        // Cerrar sidebar al hacer click en overlay
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        });

        // Cerrar sidebar al hacer click en un enlace
        const sidebarLinks = sidebar.querySelectorAll('a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', function() {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            });
        });
    }

    // Formatear números con estilo colombiano (puntos para miles, coma para decimales)
    formatColombianCurrency();
});

/**
 * Formatea todos los valores de moneda con estilo colombiano
 * Convierte $95200,00 a $95.200,00
 */
function formatColombianCurrency() {
    // Selecciona elementos que típicamente contienen valores monetarios
    const currencySelectors = [
        '.kpi-value',
        '.stat-card-info h2',
        '.cash-flow-summary strong',
        'td:contains("$")',
        '[data-currency]'
    ];

    // Buscar elementos con valores monetarios por contenido
    const allElements = document.querySelectorAll('h2, h3, strong, td, span, div');

    allElements.forEach(el => {
        // Solo procesar elementos de texto que contengan $ seguido de números
        if (el.childNodes.length === 1 && el.childNodes[0].nodeType === 3) {
            const text = el.textContent;
            // Patrón: $NUMBER,DD donde NUMBER puede tener o no miles separados
            const currencyPattern = /^\$(\d+)[,\.](\d{2})$/;
            const match = text.trim().match(currencyPattern);

            if (match) {
                const integerPart = match[1];
                const decimalPart = match[2];

                // Agregar separadores de miles (puntos)
                const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.');

                // Formato final: $95.200,00
                el.textContent = `$${formattedInteger},${decimalPart}`;
            }
        }
    });
}

// Confirmation Dialog using SweetAlert2
function confirmDelete(event, formElement) {
    event.preventDefault(); // Stop default form submission

    const customMessage = formElement.getAttribute('data-confirm-message');
    const text = customMessage || "¡No podrás revertir esto!";
    const confirmButtonText = customMessage ? 'Sí, continuar' : 'Sí, eliminar';

    Swal.fire({
        title: '¿Estás seguro?',
        text: text,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48', // Tailwind red-600 like
        cancelButtonColor: '#4b5563', // Tailwind gray-600 like
        confirmButtonText: confirmButtonText,
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            // Find the form relative to the button if formElement is the button
            const form = formElement.closest('form');
            if (form) {
                form.submit();
            }
        }
    });
    return false;
}
