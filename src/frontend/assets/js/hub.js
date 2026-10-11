/**
 * Scalaris - Interacción, modales y halo del Hub
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  var pendingTimer = null;
  var splashObserver = null;
  var splashWasPresent = false;
  var pendingDeadline = 0;

  if (window.location && window.location.pathname === '/') {
    document.documentElement.setAttribute('data-glosa', 'closed');
    if (document.body) document.body.classList.add('hub-page');
    document.documentElement.setAttribute('data-hub-pending', '');
    pendingDeadline = Date.now() + 3400;
    splashWasPresent = Boolean(document.getElementById('agy-splash-overlay'));
    if (window.MutationObserver) {
      splashObserver = new MutationObserver(function () {
        var splashExists = Boolean(document.getElementById('agy-splash-overlay'));
        if (splashExists) splashWasPresent = true;
        else if (splashWasPresent) finishPending();
      });
      splashObserver.observe(document.documentElement, { childList: true, subtree: true });
    }
    pendingTimer = setTimeout(function () {
      pendingTimer = null;
      if (document.getElementById('agy-splash-overlay')) {
        pendingTimer = setTimeout(finishPending, Math.max(0, pendingDeadline - Date.now()));
      } else {
        finishPending();
      }
    }, 1200);
  }

  function finishPending() {
    if (pendingTimer) {
      clearTimeout(pendingTimer);
      pendingTimer = null;
    }
    if (splashObserver) {
      splashObserver.disconnect();
      splashObserver = null;
    }
    document.documentElement.removeAttribute('data-hub-pending');
  }

  function clearPending() {
    if (!document.getElementById('agy-splash-overlay')) finishPending();
  }

  var activeDialog = null;
  var activeOrigin = null;
  var closeTimer = null;
  var closeTransitionHandler = null;
  var closingDialog = null;
  var spotPositions = new WeakMap();
  var spotFrames = new WeakMap();

  function setInputMode(instant) {
    if (instant) document.documentElement.setAttribute('data-input', 'keyboard');
    else document.documentElement.removeAttribute('data-input');
  }

  function cancelCloseWait() {
    if (closeTimer) {
      clearTimeout(closeTimer);
      closeTimer = null;
    }
    if (closeTransitionHandler && closingDialog) {
      var card = closingDialog.querySelector('.hub-pop-card');
      if (card) card.removeEventListener('transitionend', closeTransitionHandler);
    }
    closeTransitionHandler = null;
    closingDialog = null;
  }

  function finishClose(dialog, restoreFocus) {
    var pillarId = dialog.id.replace(/^hub-pop-/, '');
    var origin = activeOrigin || document.getElementById('hub-row-' + pillarId);
    cancelCloseWait();
    if (dialog.open) dialog.close();
    dialog.removeAttribute('data-open');
    document.documentElement.removeAttribute('data-hub-dialog-open');
    var card = dialog.querySelector('.hub-pop-card');
    if (card) card.style.removeProperty('transform-origin');
    if (activeDialog === dialog) {
      activeDialog = null;
      activeOrigin = null;
    }
    if (restoreFocus !== false && origin && origin.isConnected) {
      origin.focus({ preventScroll: true });
    }
  }

  function calcOffset(offset) {
    return offset < 0 ? '- ' + Math.abs(offset) + 'px' : '+ ' + offset + 'px';
  }

  function setPopoverOrigin(card, row) {
    var rect = row.getBoundingClientRect();
    var centerX = rect.left + rect.width / 2;
    var centerY = rect.top + rect.height / 2;
    var xOffset = centerX - window.innerWidth / 2;
    var originY;
    if (window.matchMedia('(max-width: 639px)').matches) {
      originY = 'calc(100% ' + calcOffset(centerY - window.innerHeight) + ')';
    } else {
      originY = 'calc(50% ' + calcOffset(centerY - window.innerHeight / 2) + ')';
    }
    card.style.transformOrigin = 'calc(50% ' + calcOffset(xOffset) + ') ' + originY;
  }

  function open(pillarId, opciones) {
    var instant = opciones && opciones.instant;
    var originEl = opciones && opciones.originEl;
    clearPending();
    var row = originEl || document.getElementById('hub-row-' + pillarId);
    var dialog = document.getElementById('hub-pop-' + pillarId);
    if (!row || !dialog || typeof dialog.showModal !== 'function') return;

    setInputMode(Boolean(instant));
    if (activeDialog && activeDialog !== dialog) {
      finishClose(activeDialog, false);
    }
    cancelCloseWait();

    var card = dialog.querySelector('.hub-pop-card');
    if (card) {
      if (instant) card.style.removeProperty('transform-origin');
      else setPopoverOrigin(card, row);
    }
    if (!dialog.open) dialog.showModal();

    dialog.setAttribute('data-open', '');
    row.setAttribute('aria-expanded', 'true');
    activeDialog = dialog;
    activeOrigin = row;
    document.documentElement.setAttribute('data-hub-dialog-open', '');

    var initialFocus = dialog.querySelector('.hub-tile.is-featured')
      || dialog.querySelector('.hub-tile')
      || dialog.querySelector('.hub-pop-close');
    if (initialFocus) initialFocus.focus({ preventScroll: true });
  }

  function close(opciones) {
    var instant = opciones && opciones.instant;
    var dialog = activeDialog || document.querySelector('dialog.hub-pop[open]');
    if (!dialog) return;

    if (instant) setInputMode(true);
    var expandedRows = document.querySelectorAll('.hub-row[aria-expanded="true"]');
    for (var i = 0; i < expandedRows.length; i++) {
      expandedRows[i].setAttribute('aria-expanded', 'false');
    }

    dialog.removeAttribute('data-open');
    if (instant || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      finishClose(dialog);
      return;
    }

    if (closeTimer && closingDialog === dialog) return;
    cancelCloseWait();
    closingDialog = dialog;
    var card = dialog.querySelector('.hub-pop-card');
    if (!card) {
      finishClose(dialog);
      return;
    }
    closeTransitionHandler = function (event) {
      if (event.target === card && event.propertyName === 'opacity') finishClose(dialog);
    };
    card.addEventListener('transitionend', closeTransitionHandler);
    closeTimer = setTimeout(function () { finishClose(dialog); }, 220);
  }

  function haloDisabled(event) {
    return event.pointerType === 'touch'
      || document.documentElement.getAttribute('data-input') === 'keyboard'
      || !window.matchMedia('(hover: hover) and (pointer: fine)').matches
      || window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function moveSpot(row, event) {
    var spot = row.querySelector('.hub-spot');
    if (!spot) return;
    var rect = row.getBoundingClientRect();
    spotPositions.set(row, {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    });
    if (spotFrames.has(row)) return;

    var frame = window.requestAnimationFrame(function () {
      spotFrames.delete(row);
      var position = spotPositions.get(row);
      if (!position || !row.isConnected) return;
      spot.style.transform = 'translate3d(' + position.x + 'px, ' + position.y + 'px, 0)';
    });
    spotFrames.set(row, frame);
  }

  function clearSpotForPointerOut(event) {
    var target = event.target;
    if (!target || typeof target.closest !== 'function') return;
    var row = target.closest('.hub-row');
    var related = event.relatedTarget;
    var nextRow = related && typeof related.closest === 'function'
      ? related.closest('.hub-row')
      : null;
    if (row && row !== nextRow) row.removeAttribute('data-spot-active');
  }

  function manejarClickDelegado(event) {
    var target = event.target;
    if (!target || typeof target.closest !== 'function') return;
    var closeButton = target.closest('.hub-pop-close');
    if (closeButton) {
      setInputMode(event.detail === 0);
      close({ instant: event.detail === 0 });
      return;
    }
    var dialog = target.closest('dialog.hub-pop');
    if (dialog && target === dialog) {
      setInputMode(event.detail === 0);
      close({ instant: event.detail === 0 });
      return;
    }
    var row = target.closest('.hub-row');
    if (row && !target.closest('.hub-tile')) {
      setInputMode(event.detail === 0);
      open(row.id.replace(/^hub-row-/, ''), { instant: event.detail === 0, originEl: row });
    }
  }

  function registerDelegatedListeners() {
    if (window.__scalarisHubDelegated) return;
    window.__scalarisHubDelegated = true;
    document.addEventListener('click', manejarClickDelegado);
    document.addEventListener('cancel', function (event) {
      var d = event.target;
      if (d && d.classList && d.classList.contains('hub-pop')) {
        event.preventDefault();
        close({ instant: true });
      }
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && activeDialog) {
        setInputMode(true);
        close({ instant: true });
      }
    });
    document.addEventListener('pointerenter', function (e) {
      if (haloDisabled(e) || !e.target || typeof e.target.closest !== 'function') return;
      var row = e.target.closest('.hub-row');
      if (row) { row.setAttribute('data-spot-active', ''); moveSpot(row, e); }
    }, true);
    document.addEventListener('pointermove', function (e) {
      if (haloDisabled(e) || !e.target || typeof e.target.closest !== 'function') return;
      var row = e.target.closest('.hub-row');
      if (row) { if (!row.hasAttribute('data-spot-active')) row.setAttribute('data-spot-active', ''); moveSpot(row, e); }
    }, { capture: true, passive: true });
    document.addEventListener('pointerout', clearSpotForPointerOut, true);
  }

  registerDelegatedListeners();

  window.scalaris.hub = {
    abrir: open,
    cerrar: close
  };
})();
