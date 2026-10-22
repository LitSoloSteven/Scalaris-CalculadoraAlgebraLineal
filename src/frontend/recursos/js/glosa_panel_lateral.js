'use strict';
{
    window.scalaris = window.scalaris || {};
    window.scalaris.glosa = {
        modo: () => getComputedStyle(document.documentElement).getPropertyValue('--glosa-mode').trim() || 'desplazar',
        estaAbierto: () => document.documentElement.getAttribute('data-glosa') === 'abierto',
        abrir: (opciones = {}) => establecerEstadoGlosa('abierto', opciones),
        cerrar: (opciones = {}) => establecerEstadoGlosa('cerrado', opciones),
        alternar: (opciones = {}) => establecerEstadoGlosa(window.scalaris.glosa.estaAbierto() ? 'cerrado' : 'abierto', opciones)
    };

    function animarDesplazamiento(objetos, antes, instantaneo, modo, anchos) {
        const [anchoAntes, anchoDespues] = anchos;
        if (!instantaneo && anchoAntes === anchoDespues && modo === 'desplazar') {
            const html = document.documentElement;
            const duracion = parseFloat(getComputedStyle(html).getPropertyValue('--dur-med')) || 240;
            const curva = getComputedStyle(html).getPropertyValue('--ease-std') || 'cubic-bezier(0.32, 0.72, 0, 1)';
            objetos.forEach(elemento => {
                const previo = antes.get(elemento);
                const actual = elemento.getBoundingClientRect();
                const desplazamiento = previo.left - actual.left;
                if (desplazamiento !== 0) {
                    elemento.animate([
                        { transform: `translateX(${desplazamiento}px)` },
                        { transform: 'translateX(0)' }
                    ], { duration: duracion, easing: curva });
                }
            });
        } else if (modo === 'desplazar' && anchoAntes !== anchoDespues && window.scalaris && window.scalaris.diseno) {
            window.scalaris.diseno.emitir('panelLateral');
        }
    }

    function actualizarAtributosPanel(nuevoEstado, modo) {
        const panelLateral = document.getElementById('glosa-panel-lateral');
        if (panelLateral) {
            panelLateral.inert = nuevoEstado === 'cerrado';
            panelLateral.removeAttribute('aria-expanded');
            if (modo !== 'desplazar') {
                panelLateral.setAttribute('role', 'dialog');
                panelLateral.setAttribute('aria-modal', 'true');
            } else {
                panelLateral.setAttribute('role', 'complementary');
                panelLateral.removeAttribute('aria-modal');
            }
            if (nuevoEstado === 'cerrado') {
                panelLateral.style.setProperty('--glosa-kb', '0px');
            }
        }
        const botonFlotante = document.querySelector('.glosa-boton-flotante');
        if (botonFlotante) {
            botonFlotante.setAttribute('aria-expanded', nuevoEstado === 'abierto' ? 'true' : 'false');
        }
    }

    function gestionarTrampasFoco(nuevoEstado, modo, opciones) {
        const panelLateral = document.getElementById('glosa-panel-lateral');
        if (modo !== 'desplazar') {
            nuevoEstado === 'abierto' ? desactivarOtros(panelLateral) : restaurarInteraccion();
        } else {
            restaurarInteraccion();
        }

        if (nuevoEstado === 'abierto') {
            if (modo === 'hoja') history.pushState({ glosa: true }, '');
            window.scalaris.focoGlosa.abrir(panelLateral, opciones);
        } else {
            window.scalaris.focoGlosa.cerrar(panelLateral);
        }
    }

    function medirAnchoVista(vista) {
        return vista ? vista.getBoundingClientRect().width : 0;
    }

    function retrocederHojaGlosa() {
        if (window.scalaris.glosa.modo() === 'hoja' && history.state && history.state.glosa) {
            history.back();
        }
    }

    function establecerEstadoGlosa(nuevoEstado, opciones = {}) {
        if (nuevoEstado === (window.scalaris.glosa.estaAbierto() ? 'abierto' : 'cerrado')) return;

        const html = document.documentElement;
        const modo = window.scalaris.glosa.modo();
        const prefiereMovimientoReducido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        const instantaneo = opciones.instantaneo || prefiereMovimientoReducido || html.getAttribute('data-entrada') === 'teclado' || html.hasAttribute('data-glosa-instantaneo');

        const raizVista = document.querySelector('.vista-raiz');
        const anchoAntes = medirAnchoVista(raizVista);
        const objetosDesplazables = document.querySelectorAll('.vista-raiz, .q-header .panel-tarjeta');
        const mapaAntes = new Map();
        objetosDesplazables.forEach(elemento => mapaAntes.set(elemento, elemento.getBoundingClientRect()));

        if (instantaneo) html.setAttribute('data-glosa-instantaneo', '');
        html.setAttribute('data-glosa', nuevoEstado);

        if (modo === 'desplazar') {
            try { localStorage.setItem('scalaris:glosa', nuevoEstado); } catch(evento) {}
        }

        const anchoDespues = medirAnchoVista(raizVista);
        animarDesplazamiento(objetosDesplazables, mapaAntes, instantaneo, modo, [anchoAntes, anchoDespues]);
        actualizarAtributosPanel(nuevoEstado, modo);
        gestionarTrampasFoco(nuevoEstado, modo, opciones);

        if (instantaneo) {
            void document.body.offsetHeight;
            requestAnimationFrame(() => html.removeAttribute('data-glosa-instantaneo'));
        }

        document.dispatchEvent(new CustomEvent('scalaris:glosa', { detail: { abierto: nuevoEstado === 'abierto', modo } }));
    }

    document.addEventListener('click', (evento) => {
        const boton_alternar = evento.target.closest('[data-glosa-alternar]');
        if (boton_alternar) {
            const tipo_origen = evento.detail === 0 ? 'teclado' : 'puntero';
            window.scalaris.glosa.alternar({ origen: tipo_origen, instantaneo: evento.detail === 0, elemento_origen: boton_alternar });
            return;
        }

        const boton_cerrar = evento.target.closest('[data-glosa-cerrar]');
        if (boton_cerrar) {
            const tipo_origen = evento.detail === 0 ? 'teclado' : 'puntero';
            window.scalaris.glosa.cerrar({ origen: tipo_origen, instantaneo: evento.detail === 0, elemento_origen: boton_cerrar });
            retrocederHojaGlosa();
            return;
        }

        if (evento.target.closest('.glosa-fondo-modal')) {
            window.scalaris.glosa.cerrar();
            retrocederHojaGlosa();
        }
    });

    document.addEventListener('keydown', (evento) => {
        if (evento.key === 'Escape' && !evento.defaultPrevented && !window.scalaris.focoModal.dialogoActivo()) {
            const panelLateral = document.getElementById('glosa-panel-lateral');
            const enPanel = panelLateral && panelLateral.contains(evento.target);
            if (enPanel || window.scalaris.glosa.modo() !== 'desplazar') {
                window.scalaris.glosa.cerrar({ instantaneo: true, origen: 'teclado' });
                retrocederHojaGlosa();
            }
        }
    });

    window.addEventListener('popstate', (evento) => {
        if (window.scalaris.glosa.modo() === 'hoja' && window.scalaris.glosa.estaAbierto()) {
            if (!evento.state || !evento.state.glosa) {
                window.scalaris.glosa.cerrar();
            }
        }
    });

    function desactivarOtros(objetivo) {
        if (!objetivo) return;
        let actual = objetivo;
        while (actual && actual !== document.body && actual !== document.documentElement) {
            const padre = actual.parentElement;
            if (!padre) break;
            Array.from(padre.children).forEach(hermano => {
                if (hermano === actual) return;
                if (hermano.hasAttribute('data-glosa-conservar')) return;
                if (hermano.classList.contains('glosa-fondo-modal') || hermano.classList.contains('glosa-panel-lateral')) return;
                const etiqueta = hermano.tagName;
                if (etiqueta === 'SCRIPT' || etiqueta === 'STYLE' || etiqueta === 'LINK') return;
                if (!hermano.inert) {
                    hermano.setAttribute('data-glosa-inactivo', '');
                    hermano.inert = true;
                }
            });
            actual = padre;
        }
    }

    function restaurarInteraccion() {
        document.querySelectorAll('[data-glosa-inactivo]').forEach(elemento => {
            elemento.removeAttribute('data-glosa-inactivo');
            elemento.inert = false;
        });
    }

    if (window.visualViewport) {
        const actualizarTeclado = () => {
            if (window.scalaris.glosa.estaAbierto() && window.scalaris.glosa.modo() === 'hoja') {
                const alturaTeclado = window.innerHeight - window.visualViewport.height;
                const panelLateral = document.getElementById('glosa-panel-lateral');
                if (panelLateral) {
                    panelLateral.style.setProperty('--glosa-kb', Math.max(0, alturaTeclado) + 'px');
                }
            }
        };
        window.visualViewport.addEventListener('resize', actualizarTeclado);
        window.visualViewport.addEventListener('scroll', actualizarTeclado);
    }

    let ultimoModo = window.scalaris.glosa.modo();
    function actualizarModoPanel() {
        const modoActual = window.scalaris.glosa.modo();
        if (modoActual === ultimoModo) return;
        ultimoModo = modoActual;
        if (!window.scalaris.glosa.estaAbierto()) return;
        if (modoActual !== 'desplazar') {
            window.scalaris.glosa.cerrar({ instantaneo: true });
            return;
        }
        restaurarInteraccion();
        const panelLateral = document.getElementById('glosa-panel-lateral');
        if (panelLateral) {
            panelLateral.setAttribute('role', 'complementary');
            panelLateral.removeAttribute('aria-modal');
            panelLateral.style.removeProperty('--glosa-kb');
        }
        document.documentElement.style.removeProperty('--glosa-kb');
    }
    window.addEventListener('resize', actualizarModoPanel);

    function inicializarPanelLateral() {
        const panelLateral = document.getElementById('glosa-panel-lateral');
        const botonFlotante = document.querySelector('.glosa-boton-flotante');
        if (panelLateral) {
            document.documentElement.setAttribute('data-glosa-listo', '');
            panelLateral.inert = !window.scalaris.glosa.estaAbierto();
            panelLateral.removeAttribute('aria-expanded');
            if (botonFlotante) {
                botonFlotante.setAttribute('aria-expanded', window.scalaris.glosa.estaAbierto() ? 'true' : 'false');
            }
            return true;
        }
        return false;
    }

    if (!inicializarPanelLateral()) {
        const observador = new MutationObserver((mutaciones, observadorActivo) => {
            if (inicializarPanelLateral()) {
                observadorActivo.disconnect();
            }
        });
        observador.observe(document.documentElement, { childList: true, subtree: true });
    }
}
