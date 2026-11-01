/** Acompaña cambios de estado y deslizadores sin duplicar la activación genérica. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    window.scalaris.eventosSonoros?.destruir();
    const perfiles = window.scalaris.catalogoSonidos.asignaciones.eventos;
    const valores = new WeakMap();

    function reproducir(clave) {
        return window.scalaris.sonido?.reproducir(perfiles[clave]) ?? false;
    }

    function alCambiarGlosa(evento) {
        if (typeof evento.detail?.abierto !== 'boolean') return;
        reproducir(evento.detail.abierto ? 'glosaAbrir' : 'glosaCerrar');
    }

    function alMoverDeslizador(evento) {
        if (!evento.isTrusted || evento.defaultPrevented) return;
        const control = evento.target.closest?.('[role=slider], input[type=range]');
        if (!deslizadorEditable(control)) return;
        const valor = control.getAttribute('aria-valuenow') ?? control.value;
        const anterior = valores.get(control);
        valores.set(control, valor);
        if (anterior === undefined || anterior === valor) return;
        reproducir('deslizador');
    }

    function deslizadorEditable(control) {
        if (!control || control.disabled || control.readOnly) return false;
        if (control.getAttribute('aria-disabled') === 'true' || control.getAttribute('aria-readonly') === 'true') return false;
        return !control.closest('[inert], [data-sonido-omitir]');
    }

    function recordarValor(evento) {
        if (!evento?.isTrusted) return;
        const control = evento.target.closest?.('[role=slider], input[type=range]');
        if (!deslizadorEditable(control)) return;
        valores.set(control, control.getAttribute('aria-valuenow') ?? control.value);
    }

    function alTecladoDeslizador(evento) {
        if (!['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown'].includes(evento.key)) return;
        alMoverDeslizador(evento);
    }

    function alArrastrarDeslizador(evento) {
        if (evento.buttons === 1) alMoverDeslizador(evento);
    }

    function destruir() {
        document.removeEventListener('scalaris:glosa', alCambiarGlosa);
        document.removeEventListener('input', alMoverDeslizador);
        document.removeEventListener('pointerup', alMoverDeslizador);
        document.removeEventListener('pointermove', alArrastrarDeslizador);
        document.removeEventListener('keyup', alTecladoDeslizador, true);
        document.removeEventListener('pointerdown', recordarValor, true);
        document.removeEventListener('focusin', recordarValor);
        document.removeEventListener('keydown', recordarValor, true);
    }

    document.addEventListener('scalaris:glosa', alCambiarGlosa);
    document.addEventListener('input', alMoverDeslizador, { passive: true });
    document.addEventListener('pointerup', alMoverDeslizador, { passive: true });
    document.addEventListener('pointermove', alArrastrarDeslizador, { passive: true });
    document.addEventListener('keyup', alTecladoDeslizador, { passive: true, capture: true });
    document.addEventListener('pointerdown', recordarValor, true);
    document.addEventListener('focusin', recordarValor, { passive: true });
    document.addEventListener('keydown', recordarValor, true);
    window.scalaris.eventosSonoros = { destruir, rechazo: () => reproducir('rechazo'),
        limpiezaVuelo: () => reproducir('limpiezaVuelo'), limpiezaFinal: () => reproducir('limpiezaFinal') };
}
