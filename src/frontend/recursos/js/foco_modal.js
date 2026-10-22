/** Recorrido circular compartido por diálogos y paneles modales. */
'use strict';
{
    window.scalaris = window.scalaris || {};

    function esEnfocable(elemento) {
        return elemento.tabIndex >= 0 && !elemento.matches(':disabled') &&
            !elemento.closest('[inert], [hidden], [aria-hidden="true"]') &&
            elemento.getClientRects().length && getComputedStyle(elemento).visibility !== 'hidden';
    }

    function atraparTabulacion(evento, panel) {
        if (!panel || !esTabulacionDisponible(evento)) return;
        const controles = Array.from(panel.querySelectorAll(
            'a[href], button, input, textarea, select, [tabindex]'
        )).filter(esEnfocable);
        const primero = controles[0] || panel;
        const ultimo = controles[controles.length - 1] || panel;
        const actual = document.activeElement;
        const borde = evento.shiftKey ? primero : ultimo;
        if (!panel.contains(actual) || !controles.includes(actual) || actual === borde) {
            evento.preventDefault();
            (evento.shiftKey ? ultimo : primero).focus();
        }
    }

    function esTabulacionDisponible(evento) {
        return evento.key === 'Tab' && !evento.defaultPrevented;
    }

    function dialogoActivo() {
        return Array.from(document.querySelectorAll('.q-dialog--modal .q-dialog__inner'))
            .filter(panel => panel.getClientRects().length && !panel.closest('[inert], [aria-hidden="true"]')).at(-1);
    }

    document.addEventListener('keydown', evento => atraparTabulacion(evento, dialogoActivo()));
    window.scalaris.focoModal = { esEnfocable, atraparTabulacion, dialogoActivo };
}
