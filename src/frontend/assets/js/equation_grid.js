/**
 * Scalaris - Interacción y navegación en cuadrícula de ecuaciones
 */
(function () {
  'use strict';

  if (window.__matrix_listeners_active) return;
  window.__matrix_listeners_active = true;

  document.addEventListener('keydown', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    var r = parseInt(active.dataset.row, 10);
    var c = parseInt(active.dataset.col, 10);

    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      if (e.key === 'ArrowLeft' && active.selectionStart !== 0) return;
      if (e.key === 'ArrowRight' && active.selectionEnd !== active.value.length) return;
      if (e.key === 'ArrowRight') c++;
      if (e.key === 'ArrowLeft') c--;
      if (e.key === 'ArrowDown') r++;
      if (e.key === 'ArrowUp') r--;
    } else if (e.key === 'Enter') {
      r++;
    } else {
      return;
    }

    var next = document.querySelector('input[data-row="' + r + '"][data-col="' + c + '"]');
    if (next) {
      next.focus();
      setTimeout(function () { next.select(); }, 10);
      e.preventDefault();
    }
  });

  document.addEventListener('paste', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    e.preventDefault();
    var pasteData = (e.clipboardData || window.clipboardData).getData('text');
    var rows = pasteData.replace(/\s+$/, '').split('\n');
    var startR = parseInt(active.dataset.row, 10);
    var startC = parseInt(active.dataset.col, 10);

    rows.forEach(function (rowStr, rIdx) {
      var cols = rowStr.split('\t');
      cols.forEach(function (val, cIdx) {
        var input = document.querySelector('input[data-row="' + (startR + rIdx) + '"][data-col="' + (startC + cIdx) + '"]');
        if (input) {
          input.value = val.trim();
          input.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
    });
  });

  document.addEventListener('focusin', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    var r = active.dataset.row;
    var c = active.dataset.col;

    var container = active.closest('.panel-card');
    if (!container) return;

    container.querySelectorAll('input[data-row]').forEach(function (inp) {
      var isSame = (inp.dataset.row === r || inp.dataset.col === c);
      var control = inp.closest('.q-field__control');
      if (control) {
        if (isSame) control.classList.add('cross-hl');
        else control.classList.remove('cross-hl');
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.row === undefined) return;
    var container = active.closest('.panel-card');
    if (!container) return;
    container.querySelectorAll('.cross-hl').forEach(function (el) {
      el.classList.remove('cross-hl');
    });
  });
})();
