/**
 * Scalaris - Interacciones compartidas del reproductor de pasos
 */
(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  window.scalaris.pasos = {
    revelar: function (id, texto) {
      var elemento = document.getElementById(id);
      if (!elemento) return;
      var permitido = window.scalaris.movimiento && window.scalaris.movimiento.permitido ?
        window.scalaris.movimiento.permitido() : true;
      if (permitido && window.scalaris.efectoMaquinaEscribir) {
        window.scalaris.efectoMaquinaEscribir(id, texto, 12);
        return;
      }
      elemento.textContent = texto;
    },
    destellar: function (id) {
      var elemento = document.getElementById(id);
      var permitido = window.scalaris.movimiento && window.scalaris.movimiento.permitido ?
        window.scalaris.movimiento.permitido() : true;
      if (!elemento || !permitido) return;
      elemento.animate(
        [{ opacity: 0.55, transform: 'translateY(6px)' }, { opacity: 1, transform: 'translateY(0)' }],
        { duration: 180, easing: 'cubic-bezier(0.32, 0.72, 0, 1)' }
      );
    }
  };
})();
