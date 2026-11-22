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

    function cerrar(panel) {
        const origenValido = elementoOrigen && elementoOrigen.isConnected &&
            (!panel || !panel.contains(elementoOrigen)) && window.scalaris.focoModal.esEnfocable(elementoOrigen);
        const destino = origenValido ? elementoOrigen : document.querySelector('.glosa-boton-flotante');
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
