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

    /* ── Toggle mostrar/ocultar contraseña ─────────────────── */
    document.querySelectorAll('input[type="password"]').forEach(function (input) {
      var wrapper = document.createElement('div');
      wrapper.style.cssText = 'position:relative;display:block;';
      input.parentNode.insertBefore(wrapper, input);
      wrapper.appendChild(input);

      var btn = document.createElement('button');
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Mostrar contraseña');
      btn.style.cssText = 'position:absolute;right:12px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;padding:0;color:#737373;display:flex;align-items:center;';
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
      wrapper.appendChild(btn);

      btn.addEventListener('click', function () {
        var show = input.type === 'password';
        input.type = show ? 'text' : 'password';
        btn.innerHTML = show
          ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
          : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
        btn.setAttribute('aria-label', show ? 'Ocultar contraseña' : 'Mostrar contraseña');
      });
    });
  });
})();
