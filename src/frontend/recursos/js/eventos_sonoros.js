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
        if (!control || control.closest('[inert], [data-sonido-omitir]')) return;
        const valor = control.getAttribute('aria-valuenow') ?? control.value;
        if (valores.has(control) && valores.get(control) === valor) return;
        valores.set(control, valor);
        reproducir('deslizador');
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
        document.removeEventListener('keyup', alTecladoDeslizador);
    }

    document.addEventListener('scalaris:glosa', alCambiarGlosa);
    document.addEventListener('input', alMoverDeslizador, { passive: true });
    document.addEventListener('pointerup', alMoverDeslizador, { passive: true });
    document.addEventListener('pointermove', alArrastrarDeslizador, { passive: true });
    document.addEventListener('keyup', alTecladoDeslizador, { passive: true });
    window.scalaris.eventosSonoros = { destruir, rechazo: () => reproducir('rechazo'),
        limpiezaVuelo: () => reproducir('limpiezaVuelo'), limpiezaFinal: () => reproducir('limpiezaFinal') };
}
