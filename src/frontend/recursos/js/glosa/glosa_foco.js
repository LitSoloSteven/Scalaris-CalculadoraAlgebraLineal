/** Foco modal de Glosa y devolución al control que abrió el panel. */
'use strict';
{
    window.scalaris = window.scalaris || {};
    let elementoOrigen = null;

    function abrir(panel, opciones) {
        elementoOrigen = opciones.elemento_origen || document.activeElement;
        if (!panel) return;
        const entrada = panel.querySelector('.glosa-entrada textarea');
        const usarEntrada = window.matchMedia('(pointer: fine)').matches || opciones.origen === 'teclado';
        (usarEntrada && entrada && window.scalaris.focoModal.esEnfocable(entrada) ? entrada : panel).focus();
    }

    function primerEnfocableVisible() {
        if (typeof document.querySelectorAll !== 'function') return null;
        return Array.from(document.querySelectorAll('main a[href], main button, header a[href], header button'))
            .find(window.scalaris.focoModal.esEnfocable) || null;
    }

    function cerrar(panel) {
        const origenValido = elementoOrigen && elementoOrigen.isConnected &&
            (!panel || !panel.contains(elementoOrigen)) && window.scalaris.focoModal.esEnfocable(elementoOrigen);
        const flotante = document.querySelector('.glosa-boton-flotante');
        const flotanteValido = flotante && window.scalaris.focoModal.esEnfocable(flotante) ? flotante : null;
        const destino = origenValido ? elementoOrigen : (flotanteValido || primerEnfocableVisible());
        elementoOrigen = null;
        if (destino) destino.focus();
    }

    function requiereTrampa(evento) {
        const glosa = window.scalaris.glosa;
        return evento.key === 'Tab' && !evento.defaultPrevented && !window.scalaris.focoModal.dialogoActivo() &&
            glosa && glosa.estaAbierto() && glosa.modo() !== 'desplazar';
    }

    function atraparTabulacion(evento) {
        if (!requiereTrampa(evento)) return;
        const panel = document.getElementById('glosa-panel-lateral');
        window.scalaris.focoModal.atraparTabulacion(evento, panel);
    }

    document.addEventListener('keydown', atraparTabulacion);
    window.scalaris.focoGlosa = { abrir, cerrar };
}
