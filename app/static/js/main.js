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
});

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
