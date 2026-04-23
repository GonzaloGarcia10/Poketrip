/**
 * Validaciones JS en cliente para formularios de PokeTrip.
 * Se ejecuta al cargar la página y añade validación en tiempo real + al enviar.
 */
(function () {
  'use strict';

  /* ── Utilidades ────────────────────────────────────────── */
  function showError(input, msg) {
    clearError(input);
    input.classList.add('form-input--error', 'auth-input--error');
    const p = document.createElement('p');
    p.className = 'form-field-error auth-field-error js-error';
    p.textContent = msg;
    input.parentNode.appendChild(p);
  }

  function clearError(input) {
    input.classList.remove('form-input--error', 'auth-input--error');
    input.parentNode.querySelectorAll('.js-error').forEach(e => e.remove());
  }

  function validateInput(input) {
    const val = input.value.trim();
    const name = input.name;

    // Campo requerido
    if (input.required && val === '') {
      showError(input, 'Este campo es obligatorio.');
      return false;
    }

    // Email
    if (input.type === 'email' && val) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
        showError(input, 'Introduce un email válido.');
        return false;
      }
    }

    // Contraseña mínimo 6 caracteres (solo en registro)
    if (name === 'password1' && val && val.length < 6) {
      showError(input, 'La contraseña debe tener al menos 6 caracteres.');
      return false;
    }

    // Confirmar contraseña
    if (name === 'password2') {
      const p1 = document.querySelector('[name="password1"]');
      if (p1 && val !== p1.value) {
        showError(input, 'Las contraseñas no coinciden.');
        return false;
      }
    }

    // Importe positivo
    if ((name === 'amount' || input.type === 'number') && val) {
      if (parseFloat(val) <= 0) {
        showError(input, 'El importe debe ser mayor que 0.');
        return false;
      }
    }

    // Fechas: end_date >= start_date
    if (name === 'end_date' && val) {
      const start = document.querySelector('[name="start_date"]');
      if (start && start.value && val < start.value) {
        showError(input, 'La fecha de fin no puede ser anterior a la de inicio.');
        return false;
      }
    }

    // Longitud máxima visible si supera
    if (input.maxLength > 0 && val.length > input.maxLength) {
      showError(input, `Máximo ${input.maxLength} caracteres.`);
      return false;
    }

    clearError(input);
    return true;
  }

  /* ── Inicialización ────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    // Aplica a todos los formularios de la página
    document.querySelectorAll('form').forEach(function (form) {
      // Ignorar formularios de logout/delete (solo tienen csrf + submit)
      if (form.querySelectorAll('input:not([type=hidden]), textarea, select').length === 0) return;
      if (form.dataset.noValidate) return;

      // Validación en blur (al salir del campo)
      form.querySelectorAll('input, textarea').forEach(function (input) {
        if (input.type === 'hidden' || input.type === 'submit') return;
        input.addEventListener('blur', function () { validateInput(input); });
        input.addEventListener('input', function () {
          if (input.classList.contains('form-input--error') || input.classList.contains('auth-input--error')) {
            validateInput(input);
          }
        });
      });

      // Validación al enviar
      form.addEventListener('submit', function (e) {
        let valid = true;
        form.querySelectorAll('input, textarea').forEach(function (input) {
          if (input.type === 'hidden' || input.type === 'submit') return;
          if (!validateInput(input)) valid = false;
        });
        if (!valid) {
          e.preventDefault();
          // Scroll al primer error
          const first = form.querySelector('.form-input--error, .auth-input--error');
          if (first) first.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      });
    });
  });
})();
