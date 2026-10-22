(function () {
  'use strict';

  window.scalaris = window.scalaris || {};

  window.scalaris.pasos = {
    revelar: function (identificador, texto) {
      var elemento = document.getElementById(identificador);
      if (!elemento) return;
      var permitido = window.scalaris.movimiento && window.scalaris.movimiento.permitido ?
        window.scalaris.movimiento.permitido() : true;
      if (permitido && window.scalaris.efectoMaquinaEscribir) {
        window.scalaris.efectoMaquinaEscribir(identificador, texto, 12);
        return;
      }
      elemento.textContent = texto;
    },
    destellar: function (identificador) {
      var elemento = document.getElementById(identificador);
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
