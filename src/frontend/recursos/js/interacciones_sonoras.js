/** Añade una única señal a activaciones reales, incluidas las de teclado. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.interaccionesSonoras?.destruir();
    const selector = 'button, a[href], [role="button"], [role="tab"], [role="menuitem"], ' +
        '[role="menuitemradio"], [role="switch"], [role="checkbox"], .q-select, .q-expansion-item__header';

    function reproducirActivacion(evento) {
        if (!evento.isTrusted || evento.defaultPrevented || evento.button !== 0) return;
        if (activacionModificada(evento)) return;
        const control = evento.target.closest?.(selector);
        if (!control || control.closest('[data-sonido-control], [data-sonido-omitir]')) return;
        if (control.matches(':disabled, [aria-disabled="true"], [inert]') || control.closest('[inert]')) return;
        const nombre = window.scalaris.asignacionSonora.resolver(control);
        if (nombre) window.scalaris.sonido.reproducir(nombre);
    }

    function activacionModificada(evento) {
        return evento.ctrlKey || evento.metaKey || evento.altKey || evento.shiftKey;
    }

    function reproducirEscape(evento) {
        if (!evento?.isTrusted || evento.key !== 'Escape' || evento.repeat || evento.defaultPrevented) return;
        if (document.querySelector('dialog.inicio-dialogo[open]')) window.scalaris.sonido.reproducir('cierre');
    }

    function destruir() {
        document.removeEventListener('click', reproducirActivacion, true);
        document.removeEventListener('keydown', reproducirEscape);
    }

    document.addEventListener('click', reproducirActivacion, true);
    document.addEventListener('keydown', reproducirEscape);
    window.scalaris.interaccionesSonoras = { destruir };
}
