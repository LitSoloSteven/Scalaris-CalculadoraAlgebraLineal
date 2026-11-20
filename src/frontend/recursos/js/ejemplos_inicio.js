/** Reproduce el ejemplo didáctico activo de la portada y conserva el resultado visible. */
{
    'use strict';
    window.scalaris = window.scalaris || {};
    const selectorPanel = '[data-ejemplo-inicio]';
    const selectorMarcas = '[data-ejemplo-marca], [data-ejemplo-fila]';
    const preferencia = window.matchMedia('(prefers-reduced-motion: reduce)');
    const movimiento = window.scalaris?.movimiento;
    const opciones = movimiento && {
        duration: movimiento.duracion('--dur-didactic'),
        easing: movimiento.curva(),
    };
    const trazos = {
        fila: [{ opacity: 0, transform: 'translateY(-14px) scale(0.95)' }, { opacity: 1, transform: 'translateY(0) scale(1)' }],
        'crecer-x': [{ opacity: 0.4, transform: 'scaleX(0.35)' }, { opacity: 1, transform: 'scaleX(1)' }],
        'deslizar-derecha': [{ opacity: 0, transform: 'translateX(-16px) scale(0.95)' }, { opacity: 1, transform: 'translateX(0) scale(1)' }],
        'deslizar-izquierda': [{ opacity: 0, transform: 'translateX(16px) scale(0.95)' }, { opacity: 1, transform: 'translateX(0) scale(1)' }],
        expandir: [{ opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1)' }],
        cizalla: [{ opacity: 0.4, transform: 'skewX(16deg) scale(0.95)' }, { opacity: 1, transform: 'skewX(0deg) scale(1)' }],
        'punta-cola': [{ opacity: 0, transform: 'translate(-18px, 14px) scale(0.95)' }, { opacity: 1, transform: 'translate(0, 0) scale(1)' }],
        punto: [{ opacity: 0, transform: 'scale(0.95)' }, { opacity: 1, transform: 'scale(1.18)', offset: 0.6 }, { opacity: 1, transform: 'scale(1)' }],
    };
    let reproduccion = null;

    function marcasPanel(panel) {
        if (panel.querySelectorAll) return Array.from(panel.querySelectorAll(selectorMarcas));
        const fila = panel.querySelector?.('[data-ejemplo-fila]');
        return fila ? [fila] : [];
    }

    function cambiarVoluntad(marcas, valor) {
        for (const marca of marcas) {
            if (marca?.style) marca.style.willChange = valor;
        }
    }

    function mostrarResultado(panel) {
        panel.setAttribute('data-ejemplo-completado', '');
        const mensaje = panel.dataset?.ejemploMensaje || 'Se eliminó x de la segunda fila.';
        const estado = panel.querySelector('[data-ejemplo-estado]');
        if (estado) estado.textContent = mensaje;
    }

    function detener(estado, mostrar = false) {
        if (!estado || reproduccion !== estado) return;
        reproduccion = null;
        cambiarVoluntad(estado.marcas, '');
        for (const animacion of estado.animaciones) animacion.cancel();
        if (mostrar && estado.panel.isConnected) mostrarResultado(estado.panel);
    }

    function cancelarActual() {
        detener(reproduccion, false);
    }

    function prepararPanel(panel) {
        cancelarActual();
        const objetivo = panel || document.querySelector?.(selectorPanel);
        if (objetivo) cambiarVoluntad(marcasPanel(objetivo), '');
    }

    function iniciar(panel, marcas) {
        const activas = [];
        try {
            cambiarVoluntad(marcas, 'transform, opacity');
            for (const marca of marcas) {
                const fotogramas = trazos[marca.dataset?.ejemploMarca] || trazos.fila;
                activas.push(marca.animate(fotogramas, opciones));
            }
            const estado = { panel, marcas, animaciones: activas };
            reproduccion = estado;
            const finalizar = () => detener(estado, true);
            Promise.all(activas.map(animacion => animacion.finished)).then(finalizar, finalizar);
        } catch {
            cambiarVoluntad(marcas, '');
            for (const animacion of activas) animacion.cancel();
            mostrarResultado(panel);
        }
    }

    function reproducir(evento) {
        const boton = evento.target.closest?.('[data-ejemplo-reproducir]');
        const panel = boton?.closest(selectorPanel);
        if (!panel || evento.defaultPrevented) return;
        detener(reproduccion);
        const marcas = marcasPanel(panel);
        if (evento.detail === 0 || preferencia.matches || !movimiento?.permitido() || !marcas.some(marca => marca?.animate)) {
            mostrarResultado(panel);
            return;
        }
        panel.removeAttribute('data-ejemplo-completado');
        const estado = panel.querySelector('[data-ejemplo-estado]');
        if (estado) estado.textContent = '';
        iniciar(panel, marcas);
    }

    function alVolverPagina(evento) {
        if (!evento.persisted) return;
        const recientes = window.scalaris?.recientes?.leer?.();
        if (!recientes?.valido) return;
        const primero = recientes.identificadores?.[0] || '';
        const activo = document.querySelector?.('.inicio-destacado')?.dataset?.accesoReciente || '';
        if (primero !== activo) window.location?.reload?.();
    }

    document.addEventListener('click', reproducir);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) detener(reproduccion, true);
    });
    window.addEventListener('pagehide', () => detener(reproduccion, true));
    window.addEventListener('pageshow', alVolverPagina);
    preferencia.addEventListener('change', () => {
        if (preferencia.matches) detener(reproduccion, true);
    });

    window.scalaris.ejemplosInicio = { preparar: prepararPanel, cancelar: cancelarActual };
}
