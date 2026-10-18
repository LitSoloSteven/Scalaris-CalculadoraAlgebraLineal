(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  function animar_redimension_matriz_cuadrada(identificadorMatriz, indice, modo) {
    return new Promise(function (resolver) {
      var permitido = window.scalaris.cuadricula && window.scalaris.cuadricula.movimientoActivo ?
        window.scalaris.cuadricula.movimientoActivo() : true;
      if (!permitido) {
        resolver();
        return;
      }
      var selector = 'input[data-matriz-identificador="' + identificadorMatriz + '"][data-matriz-fila="' + indice + '"], ' +
        'input[data-matriz-identificador="' + identificadorMatriz + '"][data-matriz-columna="' + indice + '"]';
      var fotogramas = modo === 'quitar'
        ? [{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(0.95) translateY(-4px)' }]
        : [{ opacity: 0, transform: 'scale(0.95) translateY(4px)' }, { opacity: 1, transform: 'scale(1)' }];
      var entradas = document.querySelectorAll(selector);
      var duracion = modo === 'quitar' ? 140 : 180;
      var paso = Math.min(15, 120 / Math.max(entradas.length, 1));
      var animaciones = [];
      entradas.forEach(function (entrada, i) {
        var control = entrada.closest('.q-field__control');
        if (control) {
          animaciones.push(control.animate(fotogramas, {
            duration: duracion,
            delay: i * paso,
            easing: 'cubic-bezier(0.32, 0.72, 0, 1)',
            fill: 'forwards'
          }).finished);
        }
      });
      Promise.all(animaciones).then(resolver).catch(resolver);
    });
  }

  window.scalaris.cuadricula = window.scalaris.cuadricula || {};
  window.scalaris.cuadricula.animarRedimensionCuadrada = animar_redimension_matriz_cuadrada;
})();
