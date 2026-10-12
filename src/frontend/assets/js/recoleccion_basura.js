/* La limpieza espera que terminen los desplazamientos antes de retirar las celdas. */
'use strict';
{

  window.scalaris = window.scalaris || {};

  function crearClon(input, rect) {
    var clon = document.createElement('div');
    clon.textContent = input.value;
    clon.style.position = 'fixed';
    clon.style.left = rect.left + 'px';
    clon.style.top = rect.top + 'px';
    clon.style.width = rect.width + 'px';
    clon.style.height = rect.height + 'px';
    clon.style.margin = '0';
    clon.style.zIndex = 'var(--z-modal)';
    clon.style.display = 'flex';
    clon.style.alignItems = 'center';
    clon.style.justifyContent = 'center';

    var contenedor = input.closest('.q-field__control');
    if (contenedor) {
      var estiloContenedor = window.getComputedStyle(contenedor);
      clon.style.background = estiloContenedor.background;
      clon.style.borderRadius = estiloContenedor.borderRadius;
      clon.style.boxShadow = estiloContenedor.boxShadow;
    }

    var estiloInput = window.getComputedStyle(input);
    clon.style.fontFamily = estiloInput.fontFamily;
    clon.style.fontSize = estiloInput.fontSize;
    clon.style.color = estiloInput.color;
    clon.style.transition = 'transform 160ms cubic-bezier(0.32, 0.72, 0, 1), opacity 160ms cubic-bezier(0.32, 0.72, 0, 1)';
    clon.style.pointerEvents = 'none';
    return clon;
  }

  function animarTrayectoria(clon, input, rect, btnRect, retraso) {
    input.style.color = 'transparent';
    document.body.appendChild(clon);

    setTimeout(function () {
      input.value = '';
      var destX = btnRect.left + btnRect.width / 2 - rect.width / 2;
      var destY = btnRect.top + btnRect.height / 2 - rect.height / 2;
      clon.style.transform = 'translate(' + (destX - rect.left) + 'px, ' + (destY - rect.top) + 'px) scale(0.1)';
      clon.style.opacity = '0';
    }, retraso);

    setTimeout(function () {
      clon.remove();
    }, retraso + 160);
  }

  function filtrarInputsVisibles() {
    var allInputs = document.querySelectorAll('.matrix-input input');
    return Array.from(allInputs).filter(function (i) {
      var r = i.getBoundingClientRect();
      return i.value && i.value !== '0' && i.value.trim() !== '' &&
        r.bottom > 0 && r.top < window.innerHeight && r.right > 0 && r.left < window.innerWidth;
    }).slice(0, 40);
  }

  function ejecutarRecoleccion(btn, iconElem, targets, resolve) {
    var btnRect = btn.getBoundingClientRect();
    var paso = Math.max(1, Math.floor(90 / targets.length));
    var retrasoAcumulado = 0;

    targets.forEach(function (input) {
      var rect = input.getBoundingClientRect();
      var clon = crearClon(input, rect);
      animarTrayectoria(clon, input, rect, btnRect, retrasoAcumulado);
      retrasoAcumulado += paso;
    });

    var duracionMed = (window.scalaris.movimiento && window.scalaris.movimiento.medio) || 240;
    setTimeout(function () {
      btn.classList.add('squash-bounce');
      setTimeout(function () {
        btn.classList.remove('squash-bounce');
        if (iconElem) {
          iconElem.textContent = 'delete';
          iconElem.classList.remove('text-err');
        }
        document.querySelectorAll('.matrix-input input').forEach(function (i) {
          i.style.color = '';
        });
        resolve();
      }, duracionMed);
    }, retrasoAcumulado + 160);
  }

  function animarRecoleccionBasura() {
    return new Promise(function (resolve) {
      var permitido = window.scalaris.movimiento && window.scalaris.movimiento.permitido ?
        window.scalaris.movimiento.permitido() : true;
      if (!permitido) {
        resolve();
        return;
      }
      var btn = document.getElementById('btn-limpiar-main');
      if (!btn) {
        resolve();
        return;
      }
      var iconElem = btn.querySelector('.q-icon');
      if (iconElem) {
        iconElem.textContent = 'delete_sweep';
        iconElem.classList.add('text-err');
      }
      var targets = filtrarInputsVisibles();
      if (targets.length === 0) {
        if (iconElem) {
          iconElem.textContent = 'delete';
          iconElem.classList.remove('text-err');
        }
        resolve();
        return;
      }
      ejecutarRecoleccion(btn, iconElem, targets, resolve);
    });
  }


  window.scalaris.animarRecoleccionBasura = animarRecoleccionBasura;
}
