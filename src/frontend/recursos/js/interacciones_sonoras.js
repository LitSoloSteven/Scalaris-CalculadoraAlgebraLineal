/** Añade una única señal a activaciones reales, incluidas las de teclado. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.interaccionesSonoras?.destruir();
    const selector = 'button, a[href], [role="button"], [role="tab"], [role="menuitem"], [role="menuitemradio"]';

    function tipoSonido(control) {
        if (control.matches('.inicio-dialogo-cerrar')) return 'cierre';
        if (control.matches('.inicio-fila')) return 'apertura';
        if (control.matches('a[href], [href]')) return 'navegacion';
        return 'accion';
    }

    function reproducirActivacion(evento) {
        if (!evento.isTrusted || evento.defaultPrevented || evento.button !== 0) return;
        if (activacionModificada(evento)) return;
        const control = evento.target.closest?.(selector);
        if (!control || control.closest('[data-sonido-control], [data-sonido-omitir]')) return;
        if (control.matches(':disabled, [aria-disabled="true"], [inert]') || control.closest('[inert]')) return;
        window.scalaris.sonido.reproducir(tipoSonido(control));
    }

    function activacionModificada(evento) {
        return evento.ctrlKey || evento.metaKey || evento.altKey || evento.shiftKey;
    }

    function reproducirEscape(evento) {
        if (!evento?.isTrusted || evento.key !== 'Escape' || evento.repeat || evento.defaultPrevented) return;
        if (document.querySelector('dialog.inicio-dialogo[open]')) window.scalaris.sonido.reproducir('cierre');
    }

    function destruir() {
        document.removeEventListener('click', reproducirActivacion);
        document.removeEventListener('keydown', reproducirEscape);
    }

    document.addEventListener('click', reproducirActivacion);
    document.addEventListener('keydown', reproducirEscape);
    window.scalaris.interaccionesSonoras = { destruir };
}
