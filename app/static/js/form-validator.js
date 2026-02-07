/**
 * FormValidator - Sistema Centralizado de Validación con SweetAlert2
 * 
 * Características:
 * - Validaciones declarativas via data-attributes
 * - Rate limiting para prevenir spam (1 submit/segundo)
 * - Integración con SweetAlert2 para alertas visuales
 * - Seguridad contra múltiples envíos
 * 
 * Uso:
 * <form data-validate>
 *   <input name="nombre" data-rules="required|minLength:3" data-label="Nombre">
 *   <input name="email" data-rules="required|email" data-label="Email">
 * </form>
 */

class FormValidator {
    constructor() {
        this.lastSubmitTime = 0;
        this.submitCooldown = 1000; // 1 segundo entre envíos
        this.isSubmitting = false;
        this.init();
    }

    /**
     * Inicializa validación en todos los formularios con data-validate
     */
    init() {
        document.querySelectorAll('form[data-validate]').forEach(form => {
            this.attachValidation(form);
        });
    }

    /**
     * Adjunta validación a un formulario específico
     */
    attachValidation(form) {
        form.addEventListener('submit', (e) => this.handleSubmit(e, form));
        
        // Agregar indicadores visuales en tiempo real
        form.querySelectorAll('[data-rules]').forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }

    /**
     * Maneja el envío del formulario
     */
    handleSubmit(e, form) {
        // Rate limiting
        const now = Date.now();
        if (now - this.lastSubmitTime < this.submitCooldown) {
            e.preventDefault();
            this.showWarning('Por favor espera un momento antes de enviar nuevamente.');
            return false;
        }

        // Prevenir doble envío
        if (this.isSubmitting) {
            e.preventDefault();
            return false;
        }

        // Validar todos los campos
        const errors = this.validateForm(form);
        
        if (errors.length > 0) {
            e.preventDefault();
            this.showValidationErrors(errors);
            return false;
        }

        // Marcar como enviando y actualizar tiempo
        this.lastSubmitTime = now;
        this.isSubmitting = true;

        // Deshabilitar botón de submit
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        }

        // Permitir el envío, pero resetear después de 5 segundos por si falla
        setTimeout(() => {
            this.isSubmitting = false;
            if (submitBtn) {
                submitBtn.disabled = false;
            }
        }, 5000);

        return true;
    }

    /**
     * Valida todos los campos del formulario
     */
    validateForm(form) {
        const errors = [];
        
        form.querySelectorAll('[data-rules]').forEach(input => {
            const fieldErrors = this.validateField(input);
            errors.push(...fieldErrors);
        });

        return errors;
    }

    /**
     * Valida un campo individual
     */
    validateField(input) {
        const rules = input.dataset.rules?.split('|') || [];
        const label = input.dataset.label || input.name || 'Campo';
        const value = input.value?.trim() || '';
        const errors = [];

        for (const rule of rules) {
            const [ruleName, ruleParam] = rule.split(':');
            const error = this.applyRule(ruleName, ruleParam, value, label, input);
            
            if (error) {
                errors.push(error);
                this.markFieldError(input);
                break; // Solo mostrar un error por campo
            }
        }

        if (errors.length === 0) {
            this.clearFieldError(input);
        }

        return errors;
    }

    /**
     * Aplica una regla de validación
     */
    applyRule(ruleName, param, value, label, input) {
        switch (ruleName) {
            case 'required':
                if (!value) return `${label} es requerido`;
                break;

            case 'email':
                if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                    return `${label} debe ser un email válido`;
                }
                break;

            case 'numeric':
                if (value && !/^[0-9]+$/.test(value)) {
                    return `${label} debe contener solo números`;
                }
                break;

            case 'minLength':
                if (value && value.length < parseInt(param)) {
                    return `${label} debe tener al menos ${param} caracteres`;
                }
                break;

            case 'maxLength':
                if (value && value.length > parseInt(param)) {
                    return `${label} no puede exceder ${param} caracteres`;
                }
                break;

            case 'min':
                if (value && parseFloat(value) < parseFloat(param)) {
                    return `${label} debe ser mayor o igual a ${param}`;
                }
                break;

            case 'max':
                if (value && parseFloat(value) > parseFloat(param)) {
                    return `${label} debe ser menor o igual a ${param}`;
                }
                break;

            case 'pattern':
                if (value && !new RegExp(param).test(value)) {
                    return `${label} tiene un formato inválido`;
                }
                break;

            case 'phone':
                if (value && !/^[\d\s\-\+\(\)]+$/.test(value)) {
                    return `${label} debe ser un teléfono válido`;
                }
                break;

            case 'nit':
                if (value && !/^[0-9]{6,15}$/.test(value)) {
                    return `${label} debe ser un NIT válido (6-15 dígitos)`;
                }
                break;

            case 'dv':
                if (value && !/^[0-9]$/.test(value)) {
                    return `Dígito de verificación debe ser un solo número`;
                }
                break;

            case 'matchField':
                const matchInput = document.querySelector(`[name="${param}"]`);
                if (matchInput && value !== matchInput.value) {
                    return `${label} no coincide`;
                }
                break;

            case 'requireWith':
                const relatedInput = document.querySelector(`[name="${param}"]`);
                if (relatedInput && relatedInput.value.trim() && !value) {
                    const relatedLabel = relatedInput.dataset.label || param;
                    return `${label} es requerido cuando ${relatedLabel} está presente`;
                }
                break;
        }

        return null;
    }

    /**
     * Marca un campo con error visual
     */
    markFieldError(input) {
        input.classList.add('input-error');
        input.style.borderColor = '#e11d48';
    }

    /**
     * Limpia el error visual de un campo
     */
    clearFieldError(input) {
        input.classList.remove('input-error');
        input.style.borderColor = '';
    }

    /**
     * Muestra errores de validación con SweetAlert2
     */
    showValidationErrors(errors) {
        const errorList = errors.map(err => `<li>${this.escapeHtml(err)}</li>`).join('');
        
        Swal.fire({
            icon: 'warning',
            title: 'Campos Inválidos',
            html: `<ul style="text-align:left; padding-left: 20px;">${errorList}</ul>`,
            confirmButtonColor: '#3085d6',
            confirmButtonText: 'Corregir'
        });
    }

    /**
     * Muestra error genérico
     */
    showError(message, title = 'Error') {
        Swal.fire({
            icon: 'error',
            title: title,
            text: message,
            confirmButtonColor: '#3085d6'
        });
    }

    /**
     * Muestra advertencia
     */
    showWarning(message, title = 'Advertencia') {
        Swal.fire({
            icon: 'warning',
            title: title,
            text: message,
            confirmButtonColor: '#3085d6',
            timer: 3000,
            timerProgressBar: true
        });
    }

    /**
     * Muestra mensaje de éxito
     */
    showSuccess(message, title = '¡Éxito!') {
        Swal.fire({
            icon: 'success',
            title: title,
            text: message,
            confirmButtonColor: '#28a745',
            timer: 2000,
            timerProgressBar: true
        });
    }

    /**
     * Confirmación de eliminación
     */
    static confirmDelete(options = {}) {
        return Swal.fire({
            icon: 'warning',
            title: options.title || '¿Estás seguro?',
            html: options.message || 'Esta acción no se puede revertir.',
            showCancelButton: true,
            confirmButtonColor: '#e11d48',
            cancelButtonColor: '#4b5563',
            confirmButtonText: options.confirmText || '<i class="fas fa-trash"></i> Sí, eliminar',
            cancelButtonText: options.cancelText || '<i class="fas fa-times"></i> Cancelar',
            reverseButtons: true
        });
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Utilidad global para confirmaciones de eliminación
function confirmDeleteAction(formAction, csrfToken, itemName) {
    FormValidator.confirmDelete({
        title: '¿Estás seguro?',
        message: `¿Deseas eliminar <strong>${itemName}</strong>?<br><small>Esta acción no se puede revertir.</small>`
    }).then((result) => {
        if (result.isConfirmed) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = formAction;
            
            const csrfInput = document.createElement('input');
            csrfInput.type = 'hidden';
            csrfInput.name = 'csrfmiddlewaretoken';
            csrfInput.value = csrfToken;
            
            form.appendChild(csrfInput);
            document.body.appendChild(form);
            form.submit();
        }
    });
}

// Mostrar error del servidor al cargar la página
function showServerError(message) {
    document.addEventListener('DOMContentLoaded', function() {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message,
            confirmButtonColor: '#3085d6'
        });
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.formValidator = new FormValidator();
});

// CSS para campos con error (solo si no existe)
if (!document.getElementById('form-validator-styles')) {
    const style = document.createElement('style');
    style.id = 'form-validator-styles';
    style.textContent = `
        .input-error {
            border-color: #e11d48 !important;
            box-shadow: 0 0 0 2px rgba(225, 29, 72, 0.2) !important;
        }
        .input-error:focus {
            border-color: #e11d48 !important;
            box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.3) !important;
        }
    `;
    document.head.appendChild(style);
}
