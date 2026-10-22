/** Estado de entrada y acciones compartidas de la aplicación. */
(function registrarEntradaGlobal() {
    'use strict';
    window.scalaris = window.scalaris || {};
    document.addEventListener('keydown', function () {
        document.documentElement.setAttribute('data-entrada', 'teclado');
    }, { capture: true, passive: true });
    document.addEventListener('pointerdown', function () {
        document.documentElement.setAttribute('data-entrada', 'puntero');
    }, { capture: true, passive: true });
    window.scalaris.movimiento = {
        medio: 240,
        permitido: function () {
            if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
            return document.documentElement.getAttribute('data-entrada') !== 'teclado';
        }
    };
})();

/** Expone el contenido de celdas cuyo texto supera su anchura disponible. */
(function registrarAyudaCeldas() {
    function ajustarAyudaCelda(evento) {
        var objetivo = evento.target;
        if (objetivo && objetivo.matches && objetivo.matches('.matriz-entrada input')) {
            if (objetivo.scrollWidth > objetivo.clientWidth) objetivo.title = objetivo.value || '';
            else if (objetivo.hasAttribute('title')) objetivo.removeAttribute('title');
        }
    }
    document.addEventListener('mouseover', ajustarAyudaCelda);
    document.addEventListener('focusin', ajustarAyudaCelda);
})();
/* Los elementos superpuestos comparten la profundidad del token var(--z-modal). */
