/** Coordina las transiciones de las regiones persistentes de bisección. */
{
    "use strict";
    const activos = new Map();
    const confirmaciones = new Map();
    const identidad = { opacity: 1, transform: "none" };
    const reducido = window.matchMedia("(prefers-reduced-motion: reduce)");
    let observador;

    function cancelar(nodo) {
        const actual = activos.get(nodo);
        if (!actual) return;
        activos.delete(nodo);
        actual.animacion.cancel();
        nodo.style.removeProperty("will-change");
        actual.alTerminar?.();
        if (!activos.size) observador.disconnect();
    }

    function animar(nodo, destino, opciones) {
        const estilo = activos.has(nodo) && getComputedStyle(nodo);
        const origen = estilo
            ? Object.fromEntries(Object.keys(destino).map(propiedad => [propiedad, estilo[propiedad]]))
            : opciones.origen;
        cancelar(nodo);
        if (!opciones.puntero || reducido.matches || !nodo.animate) {
            opciones.alTerminar?.();
            return;
        }
        const { duracion, curva } = window.scalaris.movimiento;
        const animacion = nodo.animate([origen, destino], {
            duration: duracion(opciones.token), easing: curva(), fill: "both",
        });
        nodo.style.willChange = Object.keys(destino).join(", ");
        activos.set(nodo, { animacion, alTerminar: opciones.alTerminar });
        const liberar = () => {
            if (activos.get(nodo)?.animacion === animacion) cancelar(nodo);
        };
        animacion.finished.then(liberar, liberar);
        observador ??= new MutationObserver(() => {
            for (const elemento of activos.keys()) if (!elemento.isConnected) cancelar(elemento);
        });
        observador.observe(document.body, { childList: true, subtree: true });
    }

    function entrada(nodo, puntero, distancia = 16, token = "--dur-view") {
        if (!nodo?.isConnected || !nodo.getClientRects().length) return;
        animar(nodo, identidad, {
            origen: { opacity: 0, transform: `translateY(${distancia}px)` }, puntero, token,
        });
    }

    function region(boton) {
        return document.getElementById(boton?.getAttribute("aria-controls"));
    }

    function preparar(nodo, fase) {
        nodo.dataset.biseccionTransicion = fase;
        nodo.inert = fase === "salida";
        return () => {
            if (nodo.dataset.biseccionTransicion === fase) {
                delete nodo.dataset.biseccionTransicion;
                nodo.inert = nodo.dataset.biseccionModoLocal === "inactivo";
            }
        };
    }

    function cambiarModo(evento, anterior) {
        const saliente = region(anterior);
        const entrante = region(evento.currentTarget);
        if (!saliente || !entrante || saliente === entrante) return;
        if (!esPuntero(evento) || reducido.matches || !entrante.animate) {
            cancelar(saliente);
            cancelar(entrante);
            return;
        }
        const desplazado = { opacity: 0, transform: "translateY(12px)" };
        animar(saliente, desplazado, {
            origen: identidad, puntero: true, token: "--dur-panel-exit",
            alTerminar: preparar(saliente, "salida"),
        });
        animar(entrante, identidad, {
            origen: desplazado, puntero: true, token: "--dur-panel",
            alTerminar: preparar(entrante, "entrada"),
        });
    }

    function esPuntero(evento) {
        return evento.detail > 0 && document.documentElement.dataset.entrada === "puntero";
    }

    function seleccionarModo(evento) {
        const boton = evento.target.closest('[role="radio"]');
        const grupo = evento.currentTarget;
        if (!boton || !grupo.contains(boton)) return;
        registrarEntrada(evento);
        const anterior = grupo.querySelector('[aria-checked="true"]');
        const saliente = region(anterior);
        const entrante = region(boton);
        if (!saliente || !entrante || saliente === entrante) return;
        confirmarModo(grupo, saliente, entrante);
        cambiarModo({
            currentTarget: boton, detail: evento.detail,
        }, anterior);
    }

    function confirmarModo(grupo, saliente, entrante) {
        confirmaciones.get(grupo)?.();
        saliente.dataset.biseccionModoLocal = "inactivo";
        entrante.dataset.biseccionModoLocal = "activo";
        saliente.inert = true;
        entrante.inert = false;
        const cambios = new MutationObserver(() => {
            if (saliente.classList.contains("hidden") && !entrante.classList.contains("hidden")) limpiar();
        });
        function limpiar() {
            cambios.disconnect();
            clearTimeout(plazo);
            confirmaciones.delete(grupo);
            for (const nodo of [saliente, entrante]) {
                delete nodo.dataset.biseccionModoLocal;
                nodo.inert = nodo.dataset.biseccionTransicion === "salida";
            }
        }
        const plazo = setTimeout(limpiar, 5000);
        confirmaciones.set(grupo, limpiar);
        for (const nodo of [saliente, entrante]) cambios.observe(nodo, { attributeFilter: ["class"] });
    }

    function registrarEntrada(evento) {
        const puntero = evento.type === "pointerdown" || esPuntero(evento);
        evento.currentTarget.toggleAttribute("data-biseccion-puntero", puntero);
    }

    reducido.addEventListener("change", () => {
        if (reducido.matches) for (const nodo of activos.keys()) cancelar(nodo);
    });
    window.addEventListener("pagehide", () => {
        for (const nodo of activos.keys()) cancelar(nodo);
        for (const limpiar of confirmaciones.values()) limpiar();
    });
    window.scalaris.movimientoBiseccion = {
        animar, cancelar, cambiarModo, entrada, esPuntero, seleccionarModo, registrarEntrada,
    };
}
