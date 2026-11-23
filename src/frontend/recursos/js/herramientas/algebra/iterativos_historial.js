/** Sincroniza el método de la captura montada con el historial del navegador. */
{
    'use strict';
    window.scalaris = window.scalaris || {};

    function guardar(metodo) {
        const direccion = new URL(window.location.href);
        if (direccion.searchParams.get('method') === metodo) return;
        direccion.searchParams.set('method', metodo);
        window.history.pushState(window.history.state, '', direccion);
    }

    function restaurar() {
        const metodo = new URLSearchParams(window.location.search).get('method');
        emitEvent('iterativos-metodo-historial', metodo);
    }

    function desmontar(evento) {
        if (evento.persisted) return;
        window.removeEventListener('popstate', restaurar);
        window.removeEventListener('pagehide', desmontar);
    }

    window.addEventListener('popstate', restaurar);
    window.addEventListener('pagehide', desmontar);
    window.scalaris.historialIterativos = { guardar };
}
