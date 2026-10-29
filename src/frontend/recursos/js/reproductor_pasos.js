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
        window.scalaris.efectoMaquinaEscribir(identificador, texto);
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
        [{ opacity: 0, transform: 'scale(0.95) translateY(16px)' }, { opacity: 1, transform: 'scale(1) translateY(0)' }],
        { duration: window.scalaris.movimiento.duracion('--dur-view'), easing: window.scalaris.movimiento.curva() }
      );
    }
  };
})();
