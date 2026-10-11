/**
 * Scalaris - Animaciones de redimensionado y utilidades para matrices cuadradas
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  function animateSquareResize(matrixId, idx, mode) {
    return new Promise(function (resolve) {
      var permitido = window.scalaris.cuadricula && window.scalaris.cuadricula.movimientoActivo ?
        window.scalaris.cuadricula.movimientoActivo() : true;
      if (!permitido) {
        resolve();
        return;
      }
      var sel = 'input[data-matrix-id="' + matrixId + '"][data-matrix-row="' + idx + '"], ' +
        'input[data-matrix-id="' + matrixId + '"][data-matrix-col="' + idx + '"]';
      var frames = mode === 'remove'
        ? [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(0.95) translateY(-4px)' }]
        : [{ opacity: 0, transform: 'scale(0.95) translateY(4px)' }, { opacity: 1, transform: 'scale(1)' }];
      var inputs = document.querySelectorAll(sel);
      var dur = mode === 'remove' ? 140 : 180;
      var step = Math.min(15, 120 / Math.max(inputs.length, 1));
      var anims = [];
      inputs.forEach(function (input, i) {
        var ctrl = input.closest('.q-field__control');
        if (ctrl) {
          anims.push(ctrl.animate(frames, {
            duration: dur,
            delay: i * step,
            easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
            fill: 'forwards'
          }).finished);
        }
      });
      Promise.all(anims).then(resolve).catch(resolve);
    });
  }

  window.scalaris.cuadricula = window.scalaris.cuadricula || {};
  window.scalaris.cuadricula.animarRedimensionCuadrada = animateSquareResize;
})();
