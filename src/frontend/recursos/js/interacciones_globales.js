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
        rapido: 120, medio: 240, lento: 250,
        permitido: function () {
            if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
            return document.documentElement.getAttribute('data-entrada') !== 'teclado';
        }
    };
    window.scalaris.ultimoClic = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    document.addEventListener('click', function (evento) {
        window.scalaris.ultimoClic = { x: evento.clientX, y: evento.clientY };
    }, { capture: true });
})();

/** Centra el enlace activo sin desplazamiento animado. */
(function registrarNavegacion() {
    window.scalaris.navegacion = {
        centrarActivo: function () {
            var elemento = document.querySelector('.navegacion-elementos .navegacion-activa');
            if (elemento) elemento.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'auto' });
        }
    };
})();

/** Reproduce una animación de resultado y retira su listener al terminar. */
(function registrarAnimacionResultado() {
    window.scalaris.reproducirAnimacionResultado = function (identificadorElemento) {
        var elemento = document.getElementById(identificadorElemento);
        if (!elemento) return;
        elemento.classList.remove('movimiento-entrada');
        void elemento.offsetWidth;
        elemento.classList.add('movimiento-entrada');
        var alFinalizar = function (evento) {
            if (evento.target !== elemento) return;
            elemento.classList.remove('movimiento-entrada');
            elemento.removeEventListener('animationend', alFinalizar);
        };
        elemento.addEventListener('animationend', alFinalizar);
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
