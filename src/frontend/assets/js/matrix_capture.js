/**
 * Scalaris - Interacción y navegación en panel de captura de matrices
 */
(function () {
  'use strict';

  if (window.__matrix_ops_listeners_active) return;
  window.__matrix_ops_listeners_active = true;

  document.addEventListener('keydown', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    var r = parseInt(active.dataset.matrixRow, 10);
    var c = parseInt(active.dataset.matrixCol, 10);
    var mId = active.dataset.matrixId;

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

    var next = document.querySelector('input[data-matrix-id="' + mId + '"][data-matrix-row="' + r + '"][data-matrix-col="' + c + '"]');
    if (next) {
      next.focus();
      setTimeout(function () { next.select(); }, 10);
      e.preventDefault();
    }
  });

  document.addEventListener('paste', function (e) {
    var active = document.activeElement;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    e.preventDefault();
    var pasteData = (e.clipboardData || window.clipboardData).getData('text');
    var rows = pasteData.trim().split('\n');
    var startR = parseInt(active.dataset.matrixRow, 10);
    var startC = parseInt(active.dataset.matrixCol, 10);
    var mId = active.dataset.matrixId;

    rows.forEach(function (rowStr, rIdx) {
      var cols = rowStr.split('\t');
      cols.forEach(function (val, cIdx) {
        var input = document.querySelector('input[data-matrix-id="' + mId + '"][data-matrix-row="' + (startR + rIdx) + '"][data-matrix-col="' + (startC + cIdx) + '"]');
        if (input) {
          input.value = val.trim();
          input.dispatchEvent(new Event('input', { bubbles: true }));
        }
      });
    });
  });

  document.addEventListener('focusin', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    var r = active.dataset.matrixRow;
    var c = active.dataset.matrixCol;
    var mId = active.dataset.matrixId;

    document.querySelectorAll('input[data-matrix-id="' + mId + '"]').forEach(function (inp) {
      var isSame = (inp.dataset.matrixRow === r || inp.dataset.matrixCol === c);
      var control = inp.closest('.q-field__control');
      if (control) {
        if (isSame) control.classList.add('cross-hl');
        else control.classList.remove('cross-hl');
      }
    });
  });

  document.addEventListener('focusout', function (e) {
    var active = e.target;
    if (active.tagName !== 'INPUT' || active.dataset.matrixRow === undefined) return;
    var mId = active.dataset.matrixId;

    document.querySelectorAll('input[data-matrix-id="' + mId + '"]').forEach(function (inp) {
      var control = inp.closest('.q-field__control');
      if (control) control.classList.remove('cross-hl');
    });
  });
})();
