/** Expansión entre documentos; los enlaces conservan su navegación nativa. */
{
    'use strict';
    const raiz = document.documentElement;
    const clave = 'scalaris:origen-navegacion';
    const preferencia = window.matchMedia('(prefers-reduced-motion: reduce)');
    let intencion = null;
    let activa = null;

    function consumirOrigen() {
        try {
            const registro = sessionStorage.getItem(clave);
            sessionStorage.removeItem(clave);
            return JSON.parse(registro);
        } catch (_) { return null; }
    }

    function clicNormal(evento) {
        return !evento.defaultPrevented && evento.button === 0 &&
            !evento.ctrlKey && !evento.metaKey && !evento.shiftKey && !evento.altKey;
    }

    function abreEnDocumento(enlace) {
        if (enlace.hasAttribute('download')) return false;
        const destino = enlace.target || document.querySelector('base[target]')?.target;
        return !destino || destino.toLowerCase() === '_self';
    }

    function destinoInterno(evento) {
        if (!clicNormal(evento)) return null;
        const enlace = evento.target.closest?.('a[href]');
        if (!enlace || !abreEnDocumento(enlace)) return null;
        const url = new URL(enlace.href, window.location.href);
        if (url.origin !== window.location.origin) return null;
        const actual = new URL(window.location.href);
        if (url.pathname === actual.pathname && url.search === actual.search) return null;
        return { enlace, url };
    }

    function registrarEnlace(evento) {
        intencion = null;
        const destino = destinoInterno(evento);
        if (!destino) return;
        const caja = destino.enlace.getBoundingClientRect();
        intencion = {
            evento, destino: destino.url.href, instante: Date.now(),
            x: evento.detail === 0 ? caja.left + caja.width / 2 : evento.clientX,
            y: evento.detail === 0 ? caja.top + caja.height / 2 : evento.clientY,
        };
    }

    function guardarSalida(evento) {
        consumirOrigen();
        const activacion = evento.activation;
        const elegida = intencion;
        intencion = null;
        if (!evento.viewTransition) return;
        if (preferencia.matches) {
            evento.viewTransition.skipTransition();
            return;
        }
        prepararTransicion(evento.viewTransition);
        if (!elegida || elegida.evento.defaultPrevented || !activacion) return;
        if (!['push', 'replace'].includes(activacion.navigationType)) return;
        if (activacion.entry.url !== elegida.destino || Date.now() - elegida.instante > 8000) return;
        try {
            // La entrada nueva puede tener una clave provisional en pageswap.
            sessionStorage.setItem(clave, JSON.stringify({
                destino: elegida.destino, salida: activacion.from?.key,
                instante: elegida.instante, x: elegida.x, y: elegida.y,
            }));
        } catch (_) { /* Sin almacenamiento se utiliza el centro de la ventana. */ }
    }

    function limpiar(transicion) {
        if (activa !== transicion) return;
        activa = null;
        transicion.cancelarEspera?.();
        transicion.animacion?.cancel();
        raiz.removeAttribute('data-navegacion-circular');
    }

    function prepararTransicion(transicion) {
        if (activa) {
            activa.transicion.skipTransition();
            limpiar(activa);
        }
        const estado = { transicion, animacion: null, cancelarEspera: null };
        activa = estado;
        raiz.setAttribute('data-navegacion-circular', '');
        transicion.finished.then(() => limpiar(estado), () => limpiar(estado));
        transicion.ready.catch(() => limpiar(estado));
        return estado;
    }

    function registroVigente(registro, activacion) {
        if (!registro || !registro.salida) return false;
        const antiguedad = Date.now() - registro.instante;
        if (antiguedad < 0 || antiguedad >= 8000) return false;
        return registro.destino === window.location.href && registro.salida === activacion?.from?.key;
    }

    function obtenerOrigen(registro) {
        const activacion = window.navigation?.activation;
        const navegacion = performance.getEntriesByType('navigation')[0];
        const normal = ['push', 'replace'].includes(activacion?.navigationType);
        const valido = normal && registroVigente(registro, activacion) && navegacion?.type !== 'reload';
        const x = valido && Number.isFinite(registro.x) ? registro.x : window.innerWidth / 2;
        const y = valido && Number.isFinite(registro.y) ? registro.y : window.innerHeight / 2;
        return { x: Math.max(0, Math.min(x, window.innerWidth)), y: Math.max(0, Math.min(y, window.innerHeight)) };
    }

    function animarEntrada(estado, origen) {
        if (activa !== estado) return;
        const radio = Math.hypot(
            Math.max(origen.x, window.innerWidth - origen.x),
            Math.max(origen.y, window.innerHeight - origen.y),
        );
        const centro = `at ${origen.x}px ${origen.y}px`;
        estado.animacion = raiz.animate(
            { clipPath: [`circle(0px ${centro})`, `circle(${radio}px ${centro})`] },
            { duration: 500, fill: 'both', easing: 'cubic-bezier(0.32, 0.72, 0, 1)', pseudoElement: '::view-transition-new(root)' },
        );
        estado.animacion.pause();
        estado.animacion.finished.catch(() => {});
        esperarContenido(estado);
    }

    function esperarContenido(estado) {
        let fotograma;
        const observador = new MutationObserver(comprobar);
        const limite = setTimeout(terminar, 1000);
        estado.cancelarEspera = () => {
            observador.disconnect();
            clearTimeout(limite);
            cancelAnimationFrame(fotograma);
        };
        function terminar() {
            estado.cancelarEspera();
            estado.cancelarEspera = null;
            if (activa === estado) estado.animacion.play();
        }
        function comprobar() {
            if (!document.querySelector('.navegacion-cabecera') || !document.querySelector('main')) return;
            observador.disconnect();
            fotograma = requestAnimationFrame(() => {
                fotograma = requestAnimationFrame(terminar);
            });
        }
        observador.observe(raiz, { childList: true, subtree: true });
        comprobar();
    }

    function revelarPagina(evento) {
        const registro = consumirOrigen();
        intencion = null;
        if (activa) {
            activa.transicion.skipTransition();
            limpiar(activa);
        }
        if (!evento.viewTransition) return;
        if (preferencia.matches || typeof raiz.animate !== 'function') {
            evento.viewTransition.skipTransition();
            return;
        }
        const estado = prepararTransicion(evento.viewTransition);
        raiz.setAttribute('data-vista-revelada', '');
        const origen = obtenerOrigen(registro);
        estado.transicion.ready.then(() => animarEntrada(estado, origen)).catch(() => {
            estado.transicion.skipTransition();
            limpiar(estado);
        });
    }

    document.addEventListener('click', registrarEnlace);
    window.addEventListener('pageswap', guardarSalida);
    window.addEventListener('pagereveal', revelarPagina);
    preferencia.addEventListener('change', () => {
        if (!preferencia.matches || !activa) return;
        activa.transicion.skipTransition();
        limpiar(activa);
    });
}
