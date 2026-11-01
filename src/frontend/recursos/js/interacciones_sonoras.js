/** Añade una única señal a activaciones reales, incluidas las de teclado. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.interaccionesSonoras?.destruir();
    const selector = 'button, a[href], [role="button"], [role="tab"], [role="menuitem"], ' +
        '[role="menuitemradio"], [role="switch"], [role="checkbox"], [role="radio"], [role="option"], .q-select';

    function controlOmitido(control) {
        if (!control || control.closest('[data-sonido-control], [data-sonido-omitir]')) return true;
        return control.matches(':disabled, [aria-disabled="true"], [inert]') || Boolean(control.closest('[inert]'));
    }

    function reproducirActivacion(evento) {
        if (!evento.isTrusted || evento.defaultPrevented || evento.button !== 0) return;
        if (activacionModificada(evento)) return;
        const control = evento.target.closest?.(selector);
        if (controlOmitido(control)) return;
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

    function reproducirSeleccionTeclado(evento) {
        if (!evento?.isTrusted || evento.defaultPrevented || evento.repeat || activacionModificada(evento)) return;
        const desplazamiento = { ArrowLeft: -1, ArrowRight: 1 }[evento.key];
        if (!desplazamiento) return;
        const grupo = evento.target.closest?.('.selector-opciones');
        if (!grupo || grupo.closest('[inert], [data-sonido-omitir]')) return;
        const opciones = Array.from(grupo.querySelectorAll('[role="radio"]'));
        const indice = opciones.indexOf(evento.target.closest('[role="radio"]'));
        if (indice < 0) return;
        const siguiente = opciones[(indice + desplazamiento + opciones.length) % opciones.length];
        const nombre = window.scalaris.asignacionSonora.resolver(siguiente);
        if (nombre) window.scalaris.sonido.reproducir(nombre);
    }

    function reproducirControlTeclado(evento) {
        if (!evento?.isTrusted || evento.defaultPrevented || evento.repeat || activacionModificada(evento)) return;
        if (!['Enter', ' '].includes(evento.key)) return;
        const control = evento.target.closest?.('.q-toggle, .q-checkbox, .q-radio, .q-tab, ' +
            '.q-item[aria-expanded], .q-item[role=menuitemradio], .q-item[role=option], .q-item[role=menuitem]');
        if (controlOmitido(control)) return;
        const tipo = control.matches('[role=tab]') ? 'keydown' : 'keyup';
        if (evento.type !== tipo) return;
        const nombre = window.scalaris.asignacionSonora.resolver(control);
        if (nombre) window.scalaris.sonido.reproducir(nombre);
    }

    function destruir() {
        document.removeEventListener('click', reproducirActivacion, true);
        document.removeEventListener('keydown', reproducirEscape);
        document.removeEventListener('keydown', reproducirSeleccionTeclado, true);
        document.removeEventListener('keydown', reproducirControlTeclado, true);
        document.removeEventListener('keyup', reproducirControlTeclado, true);
    }

    document.addEventListener('click', reproducirActivacion, true);
    document.addEventListener('keydown', reproducirEscape);
    document.addEventListener('keydown', reproducirSeleccionTeclado, true);
    document.addEventListener('keydown', reproducirControlTeclado, true);
    document.addEventListener('keyup', reproducirControlTeclado, true);
    window.scalaris.interaccionesSonoras = { destruir };
}
