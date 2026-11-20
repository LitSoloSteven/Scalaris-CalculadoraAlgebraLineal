/** Expansión entre documentos; los enlaces conservan su navegación nativa. */
{
    'use strict';
    const raiz = document.documentElement;
    const revelado = window.scalaris.reveladoCircular;
    const clave = 'scalaris:origen-navegacion';
    const claveTeclado = 'scalaris:navegacion-teclado';
    const preferencia = window.matchMedia('(prefers-reduced-motion: reduce)');
    let intencion = null;
    let activa = null;

    function recuperarTeclado() {
        try {
            const registro = JSON.parse(sessionStorage.getItem(claveTeclado));
            sessionStorage.removeItem(claveTeclado);
            if (registro?.destino === window.location.href && Date.now() - registro.instante < 8000) {
                raiz.setAttribute('data-entrada', 'teclado');
            }
        } catch (_) { /* La navegación no depende del almacenamiento. */ }
    }

    function registrarTeclado(evento, destino) {
        try {
            sessionStorage.removeItem(claveTeclado);
            if (evento.detail === 0) {
                sessionStorage.setItem(claveTeclado, JSON.stringify({ destino: destino.href, instante: Date.now() }));
            }
        } catch (_) { /* La navegación no depende del almacenamiento. */ }
    }

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
        registrarTeclado(evento, destino.url);
        const origen = evento.detail === 0 ? revelado.centroDe(destino.enlace) :
            { x: evento.clientX, y: evento.clientY };
        intencion = {
            evento, destino: destino.url.href, instante: Date.now(),
            ...origen,
        };
    }

    function guardarSalida(evento) {
        consumirOrigen();
        const activacion = evento.activation;
        const elegida = intencion;
        intencion = null;
        if (!evento.viewTransition) return;
        if (omitirMovimiento(elegida)) {
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

    function omitirMovimiento(elegida) {
        return preferencia.matches || elegida?.evento.detail === 0 ||
            window.scalaris.presentacion?.activa || !window.scalaris.movimiento.permitido();
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
        return valido ? registro : null;
    }

    function animarEntrada(estado, origen) {
        if (activa !== estado) return;
        estado.animacion = revelado.animarCaptura(raiz, origen, { fill: 'both' });
        estado.animacion.pause();
        estado.animacion.finished.catch(() => {});
        esperarContenido(estado);
    }

    function contenidoMontado() {
        if (window.location.pathname === '/') {
            return document.querySelector('.inicio-cabecera') &&
                document.querySelector('.inicio-directorio[data-directorio-listo] .inicio-enlace[href]');
        }
        return document.querySelector('.navegacion-cabecera') && document.querySelector('main');
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
            if (activa === estado) {
                window.scalaris.sonido?.reproducir('entrada');
                estado.animacion.play();
            }
        }
        function comprobar() {
            if (!contenidoMontado()) return;
            observador.disconnect();
            fotograma = requestAnimationFrame(() => {
                fotograma = requestAnimationFrame(terminar);
            });
        }
        observador.observe(raiz, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-directorio-listo'] });
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
        if (omitirMovimiento() || typeof raiz.animate !== 'function') {
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

    recuperarTeclado();
    document.addEventListener('click', registrarEnlace);
    window.addEventListener('pageswap', guardarSalida);
    window.addEventListener('pagereveal', revelarPagina);
    preferencia.addEventListener('change', () => {
        if (!preferencia.matches || !activa) return;
        activa.transicion.skipTransition();
        limpiar(activa);
    });
}
