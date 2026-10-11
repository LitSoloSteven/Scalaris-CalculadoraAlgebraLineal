/**
 * Scalaris - Interacción y navegación en panel de captura de vectores
 */
(function () {
  'use strict';

  if (window.__vector_listeners_active) return;
  window.__vector_listeners_active = true;

  document.addEventListener('keydown', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;

    var idx = parseInt(active.dataset.vecIdx, 10);
    var vId = active.dataset.vecId;
    var orientation = active.dataset.vecOrientation;

    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
      if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;

      if (orientation === 'column') {
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

    var next = document.querySelector('input[data-vec-id="' + vId + '"][data-vec-idx="' + idx + '"]');
    if (next) {
      next.focus();
      setTimeout(function () { next.select(); }, 10);
      e.preventDefault();
    }
  });

  document.addEventListener('paste', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
    e.preventDefault();
    var pasteData = (e.clipboardData || window.clipboardData).getData('text');

    var vals = pasteData.trim().split(/[\n\t,;]+/);
    var startIdx = parseInt(active.dataset.vecIdx, 10);
    var vId = active.dataset.vecId;

    vals.forEach(function (val, i) {
      var input = document.querySelector('input[data-vec-id="' + vId + '"][data-vec-idx="' + (startIdx + i) + '"]');
      if (input) {
        input.value = val.trim();
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    });
  });

  document.addEventListener('focusin', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
    var idx = active.dataset.vecIdx;
    var vId = active.dataset.vecId;

    document.querySelectorAll('input[data-vec-id="' + vId + '"]').forEach(function (inp) {
      var isSame = (inp.dataset.vecIdx === idx);
      var control = inp.closest('.q-field__control');
      if (control) {
        if (isSame) control.classList.add('cross-hl');
        else control.classList.remove('cross-hl');
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.vecIdx === undefined) return;
    var vId = active.dataset.vecId;

    document.querySelectorAll('input[data-vec-id="' + vId + '"]').forEach(function (inp) {
      var control = inp.closest('.q-field__control');
      if (control) control.classList.remove('cross-hl');
    });
  });
})();
