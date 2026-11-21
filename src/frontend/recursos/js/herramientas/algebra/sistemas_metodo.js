/** Transicion interrumpible del panel al cambiar el metodo de resolucion. */
(function registrarCambioMetodo() {
    'use strict';

    window.scalaris.animarCambioMetodo = function () {
        const panel = document.querySelector('.sistemas-panel-captura');
        if (!panel) return;
        panel.classList.remove('sistemas-cambio-metodo');
        if (!window.scalaris.movimiento.permitido()) return;
        void panel.offsetWidth;
        panel.classList.add('sistemas-cambio-metodo');
    };
})();
