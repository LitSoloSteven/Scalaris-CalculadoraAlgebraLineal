/**
 * Scalaris - Interacción y navegación en panel de captura de vectores
 */
(function () {
  'use strict';

  if (window.__vector_listeners_active) return;
  window.__vector_listeners_active = true;

  document.addEventListener('keydown', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.geometriaIndice === undefined) return;

    var idx = parseInt(active.dataset.geometriaIndice, 10);
    var vId = active.dataset.geometriaVector;
    var orientation = active.dataset.geometriaOrientacion;

    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
      if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;

      if (orientation === 'columna') {
        if (e.key === 'ArrowDown') idx++;
        if (e.key === 'ArrowUp') idx--;
      } else {
        if (e.key === 'ArrowRight') idx++;
        if (e.key === 'ArrowLeft') idx--;
      }
    } else if (e.key === 'Enter') {
      idx++;
    } else {
      return;
    }

    var next = document.querySelector('input[data-geometria-vector="' + vId + '"][data-geometria-indice="' + idx + '"]');
    if (next) {
      next.focus();
      setTimeout(function () { next.select(); }, 10);
      e.preventDefault();
    }
  });

  document.addEventListener('paste', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.geometriaIndice === undefined) return;
    e.preventDefault();
    var pasteData = (e.clipboardData || window.clipboardData).getData('text');

    var vals = pasteData.trim().split(/[\n\t,;]+/);
    var startIdx = parseInt(active.dataset.geometriaIndice, 10);
    var vId = active.dataset.geometriaVector;

    vals.forEach(function (val, i) {
      var input = document.querySelector('input[data-geometria-vector="' + vId + '"][data-geometria-indice="' + (startIdx + i) + '"]');
      if (input) {
        input.value = val.trim();
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });

  document.addEventListener('focusin', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.geometriaIndice === undefined) return;
    var idx = active.dataset.geometriaIndice;
    var vId = active.dataset.geometriaVector;

    document.querySelectorAll('input[data-geometria-vector="' + vId + '"]').forEach(function (inp) {
      var isSame = (inp.dataset.geometriaIndice === idx);
      var control = inp.closest('.q-field__control');
      if (control) {
        if (isSame) control.classList.add('cross-hl');
        else control.classList.remove('cross-hl');
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.geometriaIndice === undefined) return;
    var vId = active.dataset.geometriaVector;

    document.querySelectorAll('input[data-geometria-vector="' + vId + '"]').forEach(function (inp) {
      var control = inp.closest('.q-field__control');
      if (control) control.classList.remove('cross-hl');
    });
  });
})();
