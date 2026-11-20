/** Reproduce la eliminación por filas y conserva su resultado visible. */
{
    'use strict';
    const selectorPanel = '[data-ejemplo-inicio]';
    const preferencia = window.matchMedia('(prefers-reduced-motion: reduce)');
    let reproduccion = null;

    function mostrarResultado(panel) {
        panel.setAttribute('data-ejemplo-completado', '');
        panel.querySelector('[data-ejemplo-estado]').textContent = 'Se eliminó x de la segunda fila.';
    }

    function detener(estado, mostrar = false) {
        if (!estado || reproduccion !== estado) return;
        reproduccion = null;
        estado.animacion.cancel();
        if (mostrar && estado.panel.isConnected) mostrarResultado(estado.panel);
    }

    function iniciar(panel, fila, movimiento) {
        try {
            const animacion = fila.animate([
                { opacity: 0, transform: 'translateY(-14px) scale(0.95)' },
                { opacity: 1, transform: 'translateY(0) scale(1)' },
            ], {
                duration: movimiento.duracion('--dur-didactic'),
                easing: movimiento.curva(),
            });
            const estado = { panel, animacion };
            reproduccion = estado;
            const finalizar = () => detener(estado, true);
            animacion.finished.then(finalizar, finalizar);
        } catch {
            mostrarResultado(panel);
        }
    }

    function reproducir(evento) {
        const boton = evento.target.closest?.('[data-ejemplo-reproducir]');
        const panel = boton?.closest(selectorPanel);
        if (!panel || evento.defaultPrevented) return;
        detener(reproduccion);
        const movimiento = window.scalaris?.movimiento;
        const fila = panel.querySelector('[data-ejemplo-fila]');
        if (evento.detail === 0 || preferencia.matches || !movimiento?.permitido() || !fila?.animate) {
            mostrarResultado(panel);
            return;
        }

        panel.removeAttribute('data-ejemplo-completado');
        panel.querySelector('[data-ejemplo-estado]').textContent = '';
        iniciar(panel, fila, movimiento);
    }

    document.addEventListener('click', reproducir);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) detener(reproduccion, true);
    });
    window.addEventListener('pagehide', () => detener(reproduccion, true));
    preferencia.addEventListener('change', () => {
        if (preferencia.matches) detener(reproduccion, true);
    });
}
